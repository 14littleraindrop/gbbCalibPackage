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
parser.add_argument('--var', type=str, nargs=1,
        help='The variable (ROOT leaf) to plot. Supported: fat_pt, D, fat_mass, fat_eta, trkjet_MV2c10.', required=True)
parser.add_argument('--weight', type=str, nargs=1, help='The ROOT leaf name containing the weights to use. Supported: eve_mv_w',
        required=False)
parser.add_argument('-f', type=float, nargs=1, help='mixing fraction, if plotting D', required=False)
parser.add_argument('--xlabel', type=str, nargs=1, help='Histogram x-axis label', required=True)
parser.add_argument('--ylabel', type=str, nargs=1, help='Histogram y-axis label', required=True)
parser.add_argument('--title', type=str, nargs=1, help='Histogram title', required=True)
parser.add_argument('--fname', type=str, nargs=1, help='File name', required=True)

args = parser.parse_args()
directory = args.dir[0]
variable = args.var[0]
weight_name = None
if args.weight:
    weight_name = args.weight[0]

from ROOT import TFile
from ROOT.Math import PtEtaPhiEVector

all_values = []
all_weights = []
for name in os.listdir(directory):
    values = []
    weights = []
    print "Processing: %s " % (name)
    with open(os.path.join(directory, name), 'r') as f:
        for line in f.readlines():
            tfile = TFile(line.strip())
            mychain = tfile.Get('FlavourTagging_Nominal')
            entries = mychain.GetEntriesFast()
            print "Collecting %s values: %d entries..." % (variable, entries)

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
                        value[np.isinf(value)] = np.nan
                    else:
                        raise ValueError('f is required for plotting D')
                elif variable == 'fat_mass':
                    value = [PtEtaPhiEVector(pt, eta, phi, e).mass()
                            for (pt, eta, phi, e) in list(zip(
                                mychain.fat_pt, mychain.fat_eta,
                                mychain.fat_phi, mychain.fat_E))]
                elif variable == 'fat_eta':
                    value = mychain.fat_eta
                elif variable == 'trkjet_MV2c10':
                    value = mychain.trkjet_MV2c10
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

    hist_label = name.split('.')[3]
    print "Plotting %s set %s, with %d points" % (variable, hist_label, len(values))
    plt.hist(values, 300, weights=weights, histtype='step',
            stacked=True, fill=False, label=hist_label)
    all_values.extend(values)
    all_weights.extend(weights)

print "Plotting combined dataset for %s..." % variable
plt.hist(all_values, 300, weights=all_weights, histtype='step',
        stacked=True, fill=False, label='All')

plt.legend()
plt.xlabel(args.xlabel[0])
plt.ylabel(args.ylabel[0])
plt.ticklabel_format(axis="x", style="sci", scilimits=(0,0))
plt.yscale('log')
plt.title(args.title[0])
plt.savefig(args.fname[0]+'.png') 
print "Done!"
