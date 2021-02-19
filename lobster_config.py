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

# Not all of these files are needed for each workflow, but we include them all anyways
extra_inputs = [
    os.path.join(GIT_REPO_DIR,"python/Die.py"),
    os.path.join(GIT_REPO_DIR,"python/the_job.py"),
    os.path.join(GIT_REPO_DIR,"python/merge_results.py")
]

dice_str = "20d100"
rolls_per_job = int(100e3)
njobs = 10

unique_args = []
for x in range(njobs):
    new_args = "{dice} {rolls:d} {seed:d}".format(dice=dice_str,rolls=rolls_per_job,seed=random.randint(1e3,1e9))
    unique_args += [new_args]

wf = []

roll = Workflow(
    label='roll',
    dataset=EmptyDataset(),
    sandbox=cmssw.Sandbox(release=os.environ["CMSSW_BASE"]),
    category=roll_resources,
    command='python the_job.py',
    unique_arguments=unique_args,
    extra_inputs=extra_inputs,
    globaltag=False,
    merge_size=-1,
    outputs=['results.json']
)

merge_rolls = Workflow(
    label='merge',
    dataset=ParentDataset(parent=roll,units_per_task=10),
    sandbox=cmssw.Sandbox(release=os.environ["CMSSW_BASE"]),
    category=merge_resources,
    cleanup_input=False,
    command='python merge_results.py @inputfiles',
    extra_inputs=extra_inputs,
    globaltag=False,
    merge_size=-1,
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