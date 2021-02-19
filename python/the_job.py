import argparse
import random
import json
import math

from Die import Die

parser = argparse.ArgumentParser(description='roll some dice')
parser.add_argument('infiles',type=str, nargs='+',help='The file with the rolling parameters')
args = parser.parse_args()

results = {}
nfiles = len(args.infiles)
padding = math.floor(math.log(nfiles,10)) + 1
for idx,fn in enumerate(args.infiles):
    fn = fn.replace("file:","")
    # Python string formatting is great!
    print "[{idx:0>{pad}.0f}/{total:.0f}] Processing {fn}:".format(pad=padding,idx=idx,total=nfiles,fn=fn)
    with open(fn,'r') as inf:
        dicestr, nrolls, seed = inf.readline().strip().split()

        random.seed(int(seed))
        dice = Die(dicestr)

        last_update = 0.0
        for i in range(int(nrolls)):
            progress = float(i) / args.nrolls
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