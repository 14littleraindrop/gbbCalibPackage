import argparse
import json
import shutil
import os
import cPickle as pickle

from histogram import Histogram

parser = argparse.ArgumentParser(description='Sort output histograms from hist_maker.py according to how you want to make MC tamplate.\
        Options are inclusive-only (incl), mu-filtered only (mufilt) or LL-inclusive (comb) [default: comb].')
parser.add_argument('--dir', type=str, nargs=1, help='Directory which contains two directories named 361 (inclusive )and 427 (mu filtered),\
        where the sub-directories are the output of hist_maker.py', required=True)
parser.add_argument('--config', type=str, nargs=1, help='config file to use (JSON)', required=True) 
parser.add_argument('--output', type=str, nargs=1, help='Name of the output directory', required=True)
parser.add_argument('--mcflag', type=str, nargs=1, default='comb', help='Tell script how to make MC sample. Options are inclusive-only (incl),\
        mu-filtered only (mufilt) or LL-inclusive (comb) [default: comb]')

args = parser.parse_args()
directory = args.dir[0]
mcflag = args.mcflag[0]

with open(args.config[0]) as f:
    config = json.load(f)
variables = config['variables']

if mcflag == 'incl':
    shutil.copytree(os.path.join(directory, '361'), args.output[0])
elif mcflag == 'mufilt':
    shutil.copytree(os.path.join(directory, '427'), args.output[0])
else:
    os.mkdir(args.output[0])
    for var in variables:
        os.mkdir(args.output[0] + '/' + var)
        for name in os.listdir(os.path.join(directory, '361', var)):
            if name.split('_')[5] == 'LL':
                shutil.copy(os.path.join(directory, '361', var, name), os.path.join(args.output[0], var))
        for name in os.listdir(os.path.join(directory, '427', var)):
            if name.split('_')[5] != 'LL':
                shutil.copy(os.path.join(directory, '427', var, name), os.path.join(args.output[0], var))
