import argparse
import random
import json

from Die import Die

parser = argparse.ArgumentParser(description='roll some dice')
parser.add_argument('dicestr',type=str,help='Dice string to define what type of dice to roll')
parser.add_argument('nrolls',type=int,help='How many times to roll')
parser.add_argument('seed',type=int,help='Random number seed')

args = parser.parse_args()

random.seed(args.seed)

dice = Die(args.dicestr)

results = {}
last_update = 0.0
for i in range(args.nrolls):
    progress = float(i) / args.nrolls
    if (progress - last_update) > 0.05:
        print "Rolling... {:.1f}%".format(progress*100)
        last_update = progress
    x = dice.roll()
    if not results.has_key(x):
        results[x] = 0
    results[x] += 1

f = open("results.json","w")
json.dump(results,f,sort_keys=True)
f.close()