import argparse
import os
import numpy as np
import sys
import json
import math
import matplotlib
matplotlib.use('pdf')
matplotlib.rc('figure', figsize=(8, 5))
import matplotlib.pyplot as plt
import cPickle as pickle

from histogram import Histogram

parser = argparse.ArgumentParser(description='Make histogram of a variable given a directory of \
        text files containing ROOT file pathes of all five MC slices.')
parser.add_argument('--dir', type=str, nargs=1,
        help='Directory of text files containing paths of ROOT files to process', required=True)
parser.add_argument('--var', type=str, nargs=1, 
        help='The variable (ROOT leaf) to make histogram. Supported: ????', required=True)
parser.add_argument('--range', type=float, nargs=2, help='Histogram range. 1st arg = min, 2nd arg = max', required=True)
parser.add_argument('--bin', type=int, nargs=1, help='Number of bins', required=True)

args = parser.parse_args()
directory = args.dir[0]
variable = args.var[0]
with open('histMacker.json') as f:
    config = json.load(f)
weight = config['weight']
trigger = config['trigger']

from ROOT import TFile
from ROOT.Math import PtEtaPhiEVector

###################
def trigger():
    # Check fatjet_eta
    all(trigger['fat_eta'][0] <= x <= trigger['fat_eta'][1] for x in mychain.fat_eta) and \
    # Check leading_fatjet_pt
    mychain.fat_pt >= trigger['fat_pt']
###################

with open(directory+'.pickle', 'wb') as output:
    hist_all = {}
    bin_width = (args.range[1] - args. range[0]) / args.bin[0]
    for i in range (0, args.bin[0]):
        hist_all[(i + 1) * bin_width] = 0
    for name in os.listdir(directory):
        print 'Processing: %s... ' % (name)
        hist = {}
        for i in range (0, args.bin[0]):
            hist[(i + 1) * bin_width] = 0.

        # Get weighting info for the slice
        sum_of_w = 0
        xsec = weight[name.split('.')[3]]['xsec']
        filterEff = weight[name.split('.')[3]]['filterEff']

        # Loop over root files in one mc slice
        with open(os.path.join(directory, name), 'r') as f:
            for line in f.readlines():
                tfile = TFile(line.strip())
                mychain = tfile.Get('FlavourTagging_Nominal')
                entries = mychain.GetEntriesFast()
                print 'Collecting %s values: %d entries...' % (variable, entries)

                # Get leaf value
                for i in range(entries):
                    nb = mychain.GetEntry(i)
                    if nb <= 0:
                        continue

                    # Chekc trigger value
                    #################
                    if mychain.trigger['eve_HLT']['variable'] != 1:
                        continue
                    if mychain.trigger['leading_fat_pt']
                    #################

                    if variable == 'fat_pt':
                        value = mychain.fat_pt
                    else:
                        raise ValueError('Unsupported variable name.')
                    mc_eve_w = mychain.eve_mc_w * mychain.eve_pu_w
                    sum_of_w = sum_of_w + mc_eve_w
                    for item in value:
                        if not np.isnan(item) and not np.isinf(item):
                            selected_bin = min([ x - item for x in hist.keys()], key=abs) + item
                            hist[selected_bin] = hist[selected_bin] + (1 * mc_eve_w)

        # Add on slice-wise weight
        hist.update((x, y * xsec * filterEff / sum_of_w) for x, y in hist.items())
        for key in hist.keys():
            hist_all[key] = hist_all[key] + hist[key]
        # TODO: rename hist before dumpping
        pickle.dump(hist, output, protocol = pickle.HIGHEST_PROTOCOL)
        print 'Histogram for %s has been created.' % (name)
    pickle.dump(hist_all, output, protocol = pickle.HIGHEST_PROTOCOL)
    print 'Combined histogram has been created.'
    print 'Done!'
