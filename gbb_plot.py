import argparse
import os
import numpy as np
import sys
import math 
import matplotlib
matplotlib.use('pdf')
matplotlib.rc('figure', figsize=(8, 5))
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Plot a histogram of a variable given a directory of \
        text files containing ROOT file paths to analyze.')
parser.add_argument('--dir', type=str, nargs=1,
        help='Directory of text files containing paths of ROOT files to process', required=True)
parser.add_argument('--var', type=str, nargs=1, help='The variable (ROOT leaf) to plot', required=True)
parser.add_argument('--weight', type=str, nargs=1, help='The ROOT leaf name containing the weights to use',
        required=False)
parser.add_argument('--xlabel', type=str, nargs=1, help='Histogram x-axis label', required=True)
parser.add_argument('--ylabel', type=str, nargs=1, help='Histogram y-axis label', required=True)
parser.add_argument('-f', type=float, nargs=1, help='mixing fraction, if plotting D', required=False)

args = parser.parse_args()
directory = args.dir[0]
variable = args.var[0]
weight_name = None
if args.weight:
    weight_name = args.weight[0]

from ROOT import TFile
for name in os.listdir(directory):
    values = []
    weights = []
    with open(os.path.join(directory, name), 'r') as f:
        for line in f.readlines():
            tfile = TFile(line.strip())
            mychain = tfile.Get('FlavourTagging_Nominal')
            entries = mychain.GetEntriesFast()
            print "The number of entries is: ", entries

            for i in range(entries):
                nb = mychain.GetEntry(i)
                if nb <= 0:
                    continue

                # Get leaf value
                if variable == 'fat_pt':
                    value = mychain.fat_pt
                elif variable == 'D':
                    # TODO: add option to plot new tagger values
                    if args.f:
                        f = args.f[0]
                        pH = np.array(mychain.fat_XbbScoreHiggs)
                        pTop = np.array(mychain.fat_XbbScoreTop)
                        pQCD = np.array(mychain.fat_XbbScoreQCD)
                        value = np.log(pH / ((1-f) * pQCD + f * pTop))
                    else:
                        raise ValueError('f is required for plotting D')
                else:
                    raise ValueError('Unsupported variable name.')

                # Get weight value (if desired)
                weight = 1
                if weight_name is not None:
                    if weight_name == 'eve_mc_w':
                        weight = mychain.eve_mc_w

                for item in value:
                    if not np.isnan(item):
                        values.append(item)
                        weights.append(weight)

    plt.hist(values, 300, weights=weights, histtype='step',
            stacked=True, fill=False, label=name.split('.')[3])
plt.legend()
plt.xlabel(args.xlabel)
plt.ylabel(args.ylabel)
plt.ticklabel_format(axis="x", style="sci", scilimits=(0,0))
plt.yscale('log')
plt.title('Large R jet pt distribution')
plt.savefig("large_R_jet_pt.png") 

