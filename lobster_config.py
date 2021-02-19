import datetime
import os
import sys
import shutil
import subprocess
import random

from lobster import cmssw
from lobster.core import *

GIT_REPO_DIR = subprocess.check_output(['git','rev-parse','--show-toplevel']).strip()

tstamp1 = datetime.datetime.now().strftime('%Y%m%d_%H%M')
tstamp2 = datetime.datetime.now().strftime('%Y_%m_%d')
tstamp3 = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
lobster_step = "diceRolling"

ver = "v1"
tag = "test/testing_{tstamp}".format(tstamp=tstamp1)
master_label = "ROLL_ALL_{tstamp}".format(tstamp=tstamp1)

workdir_path = "{path}/{step}/{tag}/{ver}".format(step=lobster_step,tag=tag,ver=ver,path="/tmpscratch/users/$USER")
plotdir_path = "{path}/{step}/{tag}/{ver}".format(step=lobster_step,tag=tag,ver=ver,path="~/www/lobster")
output_path  = "{path}/{step}/{tag}/{ver}".format(step=lobster_step,tag=tag,ver=ver,path="/store/user/$USER")

input_path = os.path.join(GIT_REPO_DIR)

URI_HDFS   = "{scheme}://{host}:{port}".format(scheme="hdfs",host="eddie.crc.nd.edu",port="19000")
URI_ROOT   = "{scheme}://{host}/".format(scheme="root",host="deepthought.crc.nd.edu") # Note the extra slash after the hostname!
URI_GSIFTP = "{scheme}://{host}".format(scheme="gsiftp",host="T3_US_NotreDame")
URI_SRM    = "{scheme}://{host}".format(scheme="srm",host="T3_US_NotreDame")
URI_FILE   = "{scheme}://{host}".format(scheme="file",host="")


storage = StorageConfiguration(
    input=[
        "{uri}{path}".format(uri=URI_FILE,path=input_path),
    ],
    output=[
        "{uri}{path}".format(uri=URI_HDFS,path=output_path),
    ],
    disable_input_streaming = True
)

roll_resources = Category(
    name='processing',
    cores=1,
    memory=2500,
    disk=2900,
)

merge_resources = Category(
    name='processing',
    cores=1,
    memory=2500,
    disk=2900,
)

dice_str = "20d100"
rolls_per_job = int(100e3)
njobs = 50

# This is just to generate some input files that we can run over
# IMPORTANT NOTE:
#   This generates dummy input files and stores them in a directory located under the parent GIT repo,
#   which means that all of your lobster workers will be trying to access that same location! This
#   might have some nasty consequences for your home area (or wherever you cloned the git repo). However,
#   you will normally be running over files stored somewhere else, e.g. on hadoop, but you should be
#   aware of this difference when working off of this toy example!
input_dir = "test_inputs_{}".format(tstamp1)
os.mkdir(os.path.join(GIT_REPO_DIR,"inputs",input_dir))
for i in range(njobs):
    input_fn = os.path.join(GIT_REPO_DIR,"inputs",input_dir,"params_{:d}.txt".format(i))
    with open(input_fn,'w') as f:
        job_params = "{dice} {rolls:d} {seed:d}\n".format(dice=dice_str,rolls=rolls_per_job,seed=random.randint(1e3,1e9))
        f.write(job_params)

dataset=Dataset(
    files=['inputs/{}'.format(input_dir)],   # This needs to be relative to the input path specified in your StorageConfiguration
    files_per_task=1,
    patterns=['*.txt']
)

# When doing a non-CMSSW based lobster job, you will generally need to specify all the non-CMSSW
#   code required to run your job. Also, not all of these files are needed for each workflow, but
#   we include them all anyways to make passing to the Workflow() objects simpler
extra_inputs = [
    os.path.join(GIT_REPO_DIR,"python/Die.py"),
    os.path.join(GIT_REPO_DIR,"python/the_job.py"),
    os.path.join(GIT_REPO_DIR,"python/merge_results.py")
]

wf = []

roll = Workflow(
    label='roll',
    dataset=dataset,
    sandbox=cmssw.Sandbox(release=os.environ["CMSSW_BASE"]),
    category=roll_resources,
    command='python the_job.py @inputfiles',
    extra_inputs=extra_inputs,
    globaltag=False,
    merge_size=-1,
    outputs=['results.json']
)

# This is kind of extreme overkill, since we could've specified this merging in the previous workflow
#   (and which we do in this workflow anyways), but is meant to illustrate how you can still chain
#   together multiple workflows just like in a CMSSW based lobster workflow
merge_rolls = Workflow(
    label='merge',
    dataset=ParentDataset(parent=roll,units_per_task=10),
    sandbox=cmssw.Sandbox(release=os.environ["CMSSW_BASE"]),
    category=merge_resources,
    cleanup_input=False,
    command='python merge_results.py',
    extra_inputs=extra_inputs,
    globaltag=False,
    # This is really kind of redundant, but is just to showcase how to use a custom merge command.
    #   The exact size here doesn't matter very much, since the outputs all pretty much have the same
    #   static size, if you want the final output to all get merged down into a single file just make
    #   the merge_size significantly larger than w/e the size of your output files is.
    merge_size='1G',
    merge_command='python merge_results.py',
    outputs=['results.json']
)

wf.extend([roll,merge_rolls])

config = Config(
    label=master_label,
    workdir=workdir_path,
    plotdir=plotdir_path,
    storage=storage,
    workflows=wf,
    advanced=AdvancedOptions(
        bad_exit_codes=[127, 160],
        log_level=1,
        dashboard=False
    )
)