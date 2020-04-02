import argparse
import os
import numpy as np
import sys
import math
import matplotlib
matplotlib.use('pdf')
matplotlib.rc('figure', figsize=(8, 5))
import matplotlib.pyplot as plt
import cPickle as pickle

from histogram import Histogram
from plot_utils import add_plot_options

parser = argparse.ArgumentParser(description='Plot histogram for all pickle file in \
        directory generated by hist_maker.py')
parser.add_argument('--dir', type=str, nargs=1,
        help='Directory of pickle files, generated by hist_maker.py', required=True)
add_plot_options(parser)

args = parser.parse_args()
directory = args.dir[0]

for name in os.listdir(directory):
    print 'Processing: %s...' % (name)
    with open(os.path.join(directory, name), 'rb') as f:
        hist = pickle.load(f)
    plt.plot(hist.bins(), hist.frequencies(), '+', label=name.split('.')[0])

plt.legend()
plt.xlabel(args.xlabel[0])
plt.ylabel(args.ylabel[0])
plt.ticklabel_format(axis='x', style='sci', scilimits=(0,0))
plt.yscale('log')
plt.title(args.title[0])
plt.savefig(args.fname[0]+'.png') 
print "Done!!!"

