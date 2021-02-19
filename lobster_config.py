import datetime
import os
import sys
import shutil
import subprocess
import random

from lobster import cmssw
from lobster.core import *

GIT_REPO_DIR = subprocess.check_output(['git','rev-parse','--show-toplevel']).strip()

tstamp1 = dt.now().strftime('%Y%m%d_%H%M')
tstamp2 = dt.now().strftime('%Y_%m_%d')
tstamp3 = dt.now().strftime('%Y-%m-%d_%H%M')
lobster_step = "diceRolling"

ver = "v1"
tag = "test/testing_{tstamp}".format(tstamp=tstamp3)

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

processing = Category(
    name='processing',
    cores=1,
    memory=2500,
    disk=2900,
)

extra_inputs = [
    os.path.join(GIT_REPO_DIR,"python/Die.py"),
    os.path.join(GIT_REPO_DIR,"python/the_job.py")
]

dice_str = "20d100"
rolls_per_job = int(100e3)
njobs = 10

unique_args = []
for x in range(njobs):
    new_args = "{dice} {rolls:d} {seed:d}".format(dice=dice_str,rolls=rolls_per_job,seed=random.randint(1e3,1e9))
    unique_args += [new_args]

wf = []

output = Workflow(
    label='roll',
    dataset=EmptyDataset(),
    category=processing,
    command='python the_job.py',
    unique_arguments=unique_args,
    extra_inputs=extra_inputs,
    merge_size=-1,
    outputs=['results.json']
)

wf.extend([output])

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