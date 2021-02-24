import argparse
import random
import json
import math

from Dice import Die

parser = argparse.ArgumentParser(description='roll some dice')
parser.add_argument('infiles',type=str, nargs='+',help='The file with the rolling parameters')
args = parser.parse_args()

results = {}
nfiles = len(args.infiles)
padding = int(math.floor(math.log(nfiles,10)) + 1)
for idx,fn in enumerate(args.infiles):
    fn = fn.replace("file:","")
    # Python string formatting is great!
    print "[{idx:0>{pad}}/{total:d}] Processing {fn}".format(pad=padding,idx=idx+1,total=nfiles,fn=fn)
    with open(fn,'r') as inf:
        dicestr, nrolls, seed = inf.readline().strip().split()

        dice = Die(dicestr)
        nrolls = int(nrolls)
        seed   = int(seed)

        random.seed(seed)

        last_update = 0.0
        for i in range(nrolls):
            progress = float(i) / nrolls
            if (progress - last_update) > 0.05:
                print "\tRolling... {:.1f}%".format(progress*100)
                last_update = progress
            x = dice.roll()
            if not results.has_key(x):
                results[x] = 0
            results[x] += 1

f = open("results.json","w")
json.dump(results,f,sort_keys=True)
f.close()