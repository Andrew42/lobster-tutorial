import argparse
import json

parser = argparse.ArgumentParser(description='merge output json files')
parser.add_argument('infiles',type=str, nargs='+',help='The json files to merge')
args = parser.parse_args()

results = {}
for fn in args.infiles:
    with open(fn,'r') as inf:
        obj = json.load(inf)
        for k,v in obj.iteritems():
            k = int(k)
            if not results.has_key(k):
                results[k] = 0
            results[k] += v

outf = open("results.json","w")
json.dump(results,outf,sort_keys=True)
outf.close()