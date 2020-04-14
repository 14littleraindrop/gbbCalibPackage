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
mjpt = config['pt_bins']['mjet']
nmjpt = config['pt_bins']['nmjet']
flavors = config['flavors']
os.mkdir(args.output[0])

from ROOT import TFile
from ROOT.Math import PtEtaPhiEVector

# Define histograms (only support 3x3 pt range)
hists = {
        'l' + str(mjpt[0]) : {
            'l' + str(nmjpt[0]) : {flavor : {} for flavor in flavors},
            'g' + str(nmjpt[0]) + 'l' + str(nmjpt[1]) : {flavor : {} for flavor in flavors},
            'g' + str(nmjpt[1]) : {flavor : {} for flavor in flavors}
            },
        'g' + str(mjpt[0]) + 'l' + str(mjpt[1]) : {
            'l' + str(nmjpt[0]) : {flavor : {} for flavor in flavors},
            'g' + str(nmjpt[0]) + 'l' + str(nmjpt[1]) : {flavor : {} for flavor in flavors},
            'g' + str(nmjpt[1]) : {flavor : {} for flavor in flavors}
            },
        'g' + str(mjpt[1]) : {
            'l' + str(nmjpt[0]) : {flavor : {} for flavor in flavors},
            'g' + str(nmjpt[0]) + 'l' + str(nmjpt[1]) : {flavor : {} for flavor in flavors},
            'g' + str(nmjpt[1]) : {flavor : {} for flavor in flavors}
            }
        }

# Muon selection: Return a list with 1st entry = muon trkjet index, 2nd entry = non-muon trkjet index

def fjFiltter():
    fat_jets = []
    for fj in mychain.fat_assocTrkjet_ind:
        mjinds = []
        fjinds = []
        if len(fj) < 2:
            continue
        for ind in fj:
            if mychain.trkjet_assocMuon_n[ind] >= 1:
                mjinds.append(ind)
        if len(mjinds) == 0:
            continue
        fjinds.append(min(mjinds))
        # Find trkjet with largest pt to be the nmj
        if fj[0] == fjinds[0]:
            fjinds.append(fj[1])
        else:
            fjinds.append(fj[0])
        fat_jets.append(fjinds)
    return fat_jets
                
# Define functions which return jet labels

def GetPt(fjs):
    pt_labels = []
    for fj in fjs:
        pt_label = []
        # Get muon jet pt label
        muon_pt = mychain.trkjet_pt[fj[0]]/1000
        if muon_pt <= mjpt[0]:
            pt_label.append('l' + str(mjpt[0]))
        elif muon_pt <= mjpt[1]:
            pt_label.append('g' + str(mjpt[0]) + 'l' + str(mjpt[1]))
        else:
            pt_label.append('g' + str(mjpt[1]))
        # Get non-muon jet pt label
        nmuon_pt = mychain.trkjet_pt[fj[1]]/1000
        if nmuon_pt <= nmjpt[0]:
            pt_label.append('l' + str(nmjpt[0]))
        elif nmuon_pt <= nmjpt[1]:
            pt_label.append('g' + str(nmjpt[0]) + 'l' + str(nmjpt[1]))
        else:
            pt_label.append('g' + str(nmjpt[1]))
        pt_labels.append(pt_label)
    return pt_labels


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
                print 'fat_assocTrkjet_ind ='
                print mychain.fat_assocTrkjet_ind
                print 'trkjet_assocMuon_n ='
                print mychain.trkjet_assocMuon_n
                print fjFiltter()
                print GetPt(fjFiltter())
                print mychain.fat_assocTrkjet_ind.size()
                print 'trkjet_pt ='
                print mychain.trkjet_pt
                if nb <= 0:
                    continue

                # TODO: Check trigger value
                '''
                if mychain.trigger['eve_HLT']['variable'] != 1:
                    continue
                if mychain.trigger['leading_fat_pt']:
                    pass
                '''
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
                '''

    # Add on slice-wise weight
    for var in variables.keys():
        hist[var].rescale(xsec * filterEff / sum_of_w)
        hist[var].pickle(args.output[0] + '/' + var)
        combined_hist[var].combine(hist[var])
    print 'Histogram for %s has been created.' % (name)
[combined_hist[var].pickle(args.output[0] + '/' + var) for var in variables.keys()]
print 'Combined histogram has been created.'
print 'Done!'
