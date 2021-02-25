# Introduction

This repo provides the code for a basic tutorial showcasing the use of [lobster](https://github.com/NDCMS/lobster) with a non-CMSSW based program. It is assumed that you already have a working lobster installation and understand the basics of how to setup and configure a lobster job.

# Setup and Usage

First we need to checkout the repo from github:

    cd ~/Public
    git clone https://github.com/Andrew42/lobster-tutorial.git

Next we need to activate our CMS environment in order to use lobster:

    cd ~/path/to/some/release/CMSSW_X_Y_Z
    cmsenv

Finally, we activate our VOMS proxy and the lobster virtual environment:

    voms-proxy-init -voms cms -valid 192:00
    source ~/.lobster/bin/activate.csh # or activate.sh if in a bash environment

Now we should be good to run the example:

    cd ~/Public/lobster-tutorial
    lobster process lobster_config.py

# Description

Running lobster with a non-CMSSW executable is not very different from using lobster normally. The setup of the `StorageConfiguration` object should be largely unchanged:
```python
tstamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
storage = StorageConfiguration(
    input=[
        "file://~$USER/Public/lobster-tutorial",
    ],
    output=[
        "hdfs://eddie.crc.nd.edu:19000/store/user/$USER/diceRolling/test/testing_{tstamp}".format(tstamp=tstamp),
    ],
    disable_input_streaming = True
)
```
The main caveat to keep in mind is that when lobster passes the filenames to your job they might be prefixed with a file transfer protocol identifier, e.g. `file:`, which should be accounted for in your code in order to properly read the file.

For non-CMSSW jobs you will almost always be using the plain [`Dataset`](https://github.com/NDCMS/lobster/blob/master/lobster/core/dataset.py#L82-L125) object, where you will be specifying all the files and/or directories you want lobster to process. The list object passed to `files` can contain paths to individual files, or it can be paths to directories containing all the files you wish to run over. The `patterns` argument can then be used to help make sure that lobster only processes the types of files you want from a given directory. Finally, the `files_per_task` option will tell lobster how many files should be grouped together in a single task.
```python
dataset=Dataset(
    files=['inputs/test_inputs_{tstamp}'.format(tstamp=tstamp)],   # This needs to be relative to the input path specified in your StorageConfiguration
    patterns=['*.txt'],
    files_per_task=1
)
```
Keep in mind that this means that the smallest unit of work that lobster can process at a time this way is a single file. So if your inputs aren't split up over a sufficient number of files, you may not be able to to take full advantage of the benefits that batch computing provides.

*Note:* Currently there is a bug in the way dependent workflow tasks update their expected number of remaining units to process. As a result of this the `files_per_task` argument of all parent datasets must be set to 1, otherwise the dependent workflow will get stuck in an endless loop of failing to create tasks due to insufficient units from the parent dataset. If none of your workflows involve a `ParentDataset` then you can safely set `files_per_task` to any value you wish.

The most significant difference from how a normal lobster configuration might be setup is that for non-CMSSW jobs you will generally need to specify all the non-CMSSW code required to run your job. This is done through the `extra_inputs` argument of the [`Workflow`](https://github.com/NDCMS/lobster/blob/master/lobster/core/workflow.py#L125-L540) class:
```python
GIT_REPO_DIR = subprocess.check_output(['git','rev-parse','--show-toplevel']).strip()
extra_inputs = [
    os.path.join(GIT_REPO_DIR,"python/Dice.py"),
    os.path.join(GIT_REPO_DIR,"python/the_job.py"),
    os.path.join(GIT_REPO_DIR,"python/merge_results.py")
]
```
A key thing to keep in mind here is that when lobster copies the extra inputs to the worker to run your job, it won't preserve the directory structure of whatever original location you got the extra inputs from. So in the above example, the three extra input files: `Dice.py`, `the_job.py`, and `merge_results.py` _won't_ be located in a subdirectory called `python` when the remote worker tries to run your job. Instead they will all be located in the top level directory of the task working area. This means that if your code import statements assume some sort of directory structure, that being all in the same top-level directory won't break the imports.

The `Workflow` object itself isn't much different from normal running. The main differences are that the `command` argument should correspond to whatever command line argument you would use to run your code interactively and the other important option is to specify `globaltag=False`, which will bypass the `autosense.sh` code from getting run, which has problems if you're running from a directory not located inside of a CMSSW release:
```python
roll = Workflow(
    label='roll',
    dataset=dataset,
    sandbox=cmssw.Sandbox(release=os.environ["CMSSW_BASE"]),
    category=Category(name='processing',cores=1,memory=2500,disk=2900),
    command='python the_job.py @inputfiles',
    globaltag=False,
    merge_size='1G',
    merge_command='python merge_results.py',
    outputs=['results.json']
)
```
That should cover most of the major differences that one should expect to encounter when trying to run lobster with a non-CMSSW based workflow.