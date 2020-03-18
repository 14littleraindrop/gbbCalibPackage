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
        help='The variable (ROOT leaf) to make histogram. Supported: fat_pt, fat_mass, fat_eta, \
                trkjet_MV2c10, D', required=True)
parser.add_argument('-f', type=float, nargs=1, help='mixing fraction, if plotting D')
parser.add_argument('--range', type=float, nargs=2, help='Histogram range. 1st arg = min, 2nd arg = max', required=True)
parser.add_argument('--bin', type=int, nargs=1, help='Number of bins', required=True)
parser.add_argument('--config', type=str, nargs=1, help='Config file to use (JSON)', default='hist_maker.json')
parser.add_argument('--output', type=str, nargs=1, help='Name of output directory', required=True)

args = parser.parse_args()
directory = args.dir[0]
variable = args.var[0]
with open(args.config[0]) as f:
    config = json.load(f)
weight = config['weight']
trigger = config['trigger']
os.mkdir(args.output[0])

from ROOT import TFile
from ROOT.Math import PtEtaPhiEVector

###################
def trigger():
    # Check fatjet_eta, leading_fatjet_pt
    all(trigger['fat_eta'][0] <= x <= trigger['fat_eta'][1] for x in mychain.fat_eta) and \
    mychain.fat_pt >= trigger['fat_pt']
###################

hist_all = Histogram('combined')
hist_all.setup_bins(args.range[0], args.range[1], args.bin[0])

for name in os.listdir(directory):
    print 'Processing: %s... ' % (name)
    hist = Histogram(name.split('.')[3])
    hist.setup_bins(args.range[0], args.range[1], args.bin[0])

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

                # TODO: Check trigger value
                '''
                if mychain.trigger['eve_HLT']['variable'] != 1:
                    continue
                if mychain.trigger['leading_fat_pt']:
                    pass
                '''

                if variable == 'fat_pt':
                    value = mychain.fat_pt
                elif variable == 'fat_mass':
                    value = [PtEtaPhiEVector(pt, eta, phi, e).mass()
                            for (pt, eta, phi, e) in list(zip(
                                mychain.fat_pt, mychain.fat_eta,
                                mychain.fat_phi, mychain.fat_E))]
                elif variable == 'fat_eta':
                    value = mychain.fat_eta
                elif variable == 'trkjet_MV2c10':
                    value = mychain.trkjet_MV2c10
                elif variable == 'D':
                    if args.f:
                        f = args.f[0]
                        pH = np.array(mychain.fat_XbbScoreHiggs)
                        pTop = np.array(mychain.fat_XbbScoreTop)
                        pQCD = np.array(mychain.fat_XbbScoerQCD)
                        value = np.log(pH / ((1-f) * pQCD + f * pTop))
                    else:
                        raise ValueError('f is required for plotting D')
                else:
                    raise ValueError('Unsupported variable name.')
                mc_eve_w = mychain.eve_mc_w * mychain.eve_pu_w
                sum_of_w = sum_of_w + mc_eve_w
                for item in value:
                    if not np.isnan(item) and not np.isinf(item):
                        hist.add_point(item, mc_eve_w)

    # Add on slice-wise weight
    hist.rescale(xsec * filterEff / sum_of_w)
    hist.pickle(args.output[0])
    hist_all.combine(hist)
    print 'Histogram for %s has been created.' % (name)
hist_all.pickle(args.output[0])
print 'Combined histogram has been created.'
print 'Done!'
