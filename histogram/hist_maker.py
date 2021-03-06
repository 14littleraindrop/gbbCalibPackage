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
                trkjet_MV2c10, D', required=False)
parser.add_argument('-f', type=float, nargs=1, help='mixing fraction, if plotting D')
parser.add_argument('--config', type=str, nargs=1, help='Config file to use (JSON)', default='hist_maker.json')
parser.add_argument('--output', type=str, nargs=1, help='Name of output directory', required=True)

args = parser.parse_args()
directory = args.dir[0]
with open(args.config[0]) as f:
    config = json.load(f)
weight = config['weight']
trigger = config['trigger']
variables = config['variables']
os.mkdir(args.output[0])

from ROOT import TFile
from ROOT.Math import PtEtaPhiEVector

###################
def trigger():
    # Check fatjet_eta, leading_fatjet_pt
    all(trigger['fat_eta'][0] <= x <= trigger['fat_eta'][1] for x in mychain.fat_eta) and \
    mychain.fat_pt >= trigger['fat_pt']
###################


# Declare combined histograms for all provided variables
combined_hist = { var : Histogram('combined_' + var) for var in variables.keys()}
for var in variables.keys():
    combined_hist[var].setup_bins(variables[var]['min'], variables[var]['max'], variables[var]['bin'])

# Create directories to hold pickled histograms for each variables
for var in variables.keys():
    os.mkdir(args.output[0] + '/' + var)

for name in os.listdir(directory):
    print 'Processing: %s... ' % (name)
    hist = {var : Histogram(name.split('.')[3] + '_' + var) for var in variables.keys()}
    for var in variables.keys():
        hist[var].setup_bins(variables[var]['min'], variables[var]['max'], variables[var]['bin'])

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
            print 'Collecting entries: %d entries...' % (entries)

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
                values = {var : 0 for var in variables.keys()}
                for var in variables.keys():
                    if var == 'fat_pt':
                        values[var] = mychain.fat_pt
                    elif var == 'fat_mass':
                        values[var] = [PtEtaPhiEVector(pt, eta, phi, e).mass()
                                for (pt, eta, phi, e) in list(zip(
                                    mychain.fat_pt, mychain.fat_eta,
                                    mychain.fat_phi, mychain.fat_E))]
                    elif var == 'fat_eta':
                        values[var] = mychain.fat_eta
                    elif var == 'trkjet_MV2c10':
                        values[var] = mychain.trkjet_MV2c10
                    elif var == 'D':
                        if args.f:
                            f = args.f[0]
                            pH = np.array(mychain.fat_XbbScoreHiggs)
                            pTop = np.array(mychain.fat_XbbScoreTop)
                            pQCD = np.array(mychain.fat_XbbScoerQCD)
                            values[var] = np.log(pH / ((1-f) * pQCD + f * pTop))
                        else:
                            raise ValueError('f is required for plotting D')
                    else:
                        raise ValueError('Unsupported variable name.')
                mc_eve_w = mychain.eve_mc_w * mychain.eve_pu_w
                sum_of_w = sum_of_w + mc_eve_w
                for var in variables.keys():
                    for item in values[var]:
                        if not np.isnan(item) and not np.isinf(item):
                            hist[var].add_point(item, mc_eve_w)

    # Add on slice-wise weight
    for var in variables.keys():
        hist[var].rescale(xsec * filterEff / sum_of_w)
        hist[var].pickle(args.output[0] + '/' + var)
        combined_hist[var].combine(hist[var])
    print 'Histogram for %s has been created.' % (name)
[combined_hist[var].pickle(args.output[0] + '/' + var) for var in variables.keys()]
print 'Combined histogram has been created.'
print 'Done!'
