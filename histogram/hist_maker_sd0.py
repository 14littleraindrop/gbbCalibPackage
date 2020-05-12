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
mjpt_bins = config['pt_bins']['mjet']
nmjpt_bins = config['pt_bins']['nmjet']
flavors = config['flavors']
xbbtagger = config['XbbTagger']
os.mkdir(args.output[0])
for var in variables.keys():
    os.mkdir(args.output[0] + '/' + var)

from ROOT import TFile
from ROOT.Math import PtEtaPhiEVector

# Define histograms (only support 3x3 pt range)
def hist_init():
    hists = {
            'l' + str(mjpt_bins[0]) : {
                'l' + str(nmjpt_bins[0]) : {
                    '2TAG' : {flavor : 0 for flavor in flavors},
                    'NOT2TAG' : {flavor : 0 for flavor in flavors}
                    },
                'g' + str(nmjpt_bins[0]) + 'l' + str(nmjpt_bins[1]) : {
                    '2TAG' : {flavor : 0 for flavor in flavors},
                    'NOT2TAG' : {flavor : 0 for flavor in flavors}
                    },
                'g' + str(nmjpt_bins[1]) : {
                    '2TAG' : {flavor : 0 for flavor in flavors},
                    'NOT2TAG' : {flavor : 0 for flavor in flavors}
                    }
                },
            'g' + str(mjpt_bins[0]) + 'l' + str(mjpt_bins[1]) : {
                'l' + str(nmjpt_bins[0]) : {
                    '2TAG' : {flavor : 0 for flavor in flavors},
                    'NOT2TAG' : {flavor : 0 for flavor in flavors}
                    },
                'g' + str(nmjpt_bins[0]) + 'l' + str(nmjpt_bins[1]) : {
                    '2TAG' : {flavor : 0 for flavor in flavors},
                    'NOT2TAG' : {flavor : 0 for flavor in flavors}
                    },
                'g' + str(nmjpt_bins[1]) : {
                    '2TAG' : {flavor : 0 for flavor in flavors},
                    'NOT2TAG' : {flavor : 0 for flavor in flavors}
                    }
                },
            'g' + str(mjpt_bins[1]) : {
                'l' + str(nmjpt_bins[0]) : {
                    '2TAG' : {flavor : 0 for flavor in flavors},
                    'NOT2TAG' : {flavor : 0 for flavor in flavors}
                    },
                'g' + str(nmjpt_bins[0]) + 'l' + str(nmjpt_bins[1]) : {
                    '2TAG' : {flavor : 0 for flavor in flavors},
                    'NOT2TAG' : {flavor : 0 for flavor in flavors}
                    },
                'g' + str(nmjpt_bins[1]) : {
                    '2TAG' : {flavor : 0 for flavor in flavors},
                    'NOT2TAG' : {flavor : 0 for flavor in flavors}
                    }
                }
            }
    return hists

# Muon selection: Return a list with 1st entry = muon trkjet index, 2nd entry = non-muon trkjet index
def fjFilter():
    fat_jets = []
    fj_index = []
    fj_ind = 0
    for fj in mychain.fat_assocTrkjet_ind:
        # Find associate trkjet index
        trkjet_ind = []
        for ind in fj:
            trkjet_ind.append(list(mychain.trkjet_ind).index(ind))

        mjinds = []
        fjinds = []
        if len(trkjet_ind) < 2:
            continue
        for ind in trkjet_ind:
            if mychain.trkjet_assocMuon_n[ind] >= 1:
                mjinds.append(ind)
        if len(mjinds) == 0:
            continue
        fjinds.append(min(mjinds))
        # Find trkjet with largest pt to be the nmj
        if trkjet_ind[0] == fjinds[0]:
            fjinds.append(trkjet_ind[1])
        else:
            fjinds.append(trkjet_ind[0])
        fat_jets.append(fjinds)
        fj_index.append(fj_ind)
        fj_ind += 1
    return zip(fat_jets, fj_index)

# Define triggers
def eve_HLT():
    eve_HLT = trigger['eve_HLT']
    if eve_HLT == 'None':
        return True
    elif eve_HLT == 'eve_HLT_j460_a10_lcw_subjes_L1J100':
       return  mychain.eve_HLT_j460_a10_lcw_subjes_L1J100 == 1
    elif eve_HLT == 'eve_HLT_j420_a10t_lcw_jes_40smcINF_L1J100':
        return mychain.eve_HLT_j420_a10t_lcw_jes_40smcINF_L1J100 ==1
    elif eve_HLT == 'eve_HLT_2j330_a10t_lcw_jes_40smcINF_L1J100':
        return mychain.eve_HLT_2j330_a10t_lcw_jes_40smcINF_L1J100 == 1
    else:
        raise ValueError('eve_HLT not matched or not found')

def leading_fat_pt():
    pt_cut = trigger['leading_fat_pt']
    if pt_cut == 'None':
        return True
    elif mychain.fat_pt[0]/100 >= pt_cut:
        return True
    else:
        return False

def eveTrigger():
    if eve_HLT() and leading_fat_pt():
        return True
    else:
        return False

# Define functions which return fat jet labels
def GetPt(fj):
    pt_label = []
    # Get muon jet pt label
    muon_pt = mychain.trkjet_pt[fj[0]]/1000
    if muon_pt <= mjpt_bins[0]:
        pt_label.append('l' + str(mjpt_bins[0]))
    elif muon_pt <= mjpt_bins[1]:
        pt_label.append('g' + str(mjpt_bins[0]) + 'l' + str(mjpt_bins[1]))
    else:
        pt_label.append('g' + str(mjpt_bins[1]))
    # Get non-muon jet pt label
    nmuon_pt = mychain.trkjet_pt[fj[1]]/1000
    if nmuon_pt <= nmjpt_bins[0]:
        pt_label.append('l' + str(nmjpt_bins[0]))
    elif nmuon_pt <= nmjpt_bins[1]:
        pt_label.append('g' + str(nmjpt_bins[0]) + 'l' + str(nmjpt_bins[1]))
    else:
        pt_label.append('g' + str(nmjpt_bins[1]))
    return pt_label

def GetFlavor(fj):
    flavors = []
    # Get jet flavors
    for i in fj:
        if mychain.trkjet_BHad_n[i] >= 1:
            flavors.append('B')
        elif mychain.trkjet_CHad_n[i] >= 1:
            flavors.append('C')
        else:
            flavors.append('L')
    fj_flavor = ''.join(flavors)
    if fj_flavor == 'BL' or 'BC':
        return 'BL'
    elif fj_flavor == 'CL' or 'CB':
        return 'CL'
    elif fj_flavor == 'LL' or 'LB' or 'LC':
        return 'LL'
    else:
        return fj_flavor

# Define function for Xbb tagging
def XbbScoreTagger(fj_index):
    pH = np.array(mychain.fat_XbbScoreHiggs)
    pTop = np.array(mychain.fat_XbbScoreTop)
    pQCD = np.array(mychain.fat_XbbScoreQCD)
    xbb_discriminant = np.log(pH / ((1-xbbtagger['topFrac']) * pQCD + xbbtagger['topFrac'] * pTop))
    if xbb_discriminant[fj_index] > xbbtagger['cut']:
        return '2TAG'
    else:
        return 'NOT2TAG'

# Define function to calculate Sd0
def Get_meanSd0(trkjet_ind):
    d0s = np.array(mychain.trkjet_assocTrk_d0[trkjet_ind])
    d0errs = np.array(mychain.trkjet_assocTrk_d0err[trkjet_ind])
    phis = np.array(mychain.trkjet_assocTrk_phi[trkjet_ind])
    trkjet_phi = mychain.trkjet_phi[trkjet_ind]

    sd0_sign = np.where(np.sin(trkjet_phi - phis) * d0s > 0, 1, -1)
    sd0s = sd0_sign * np.abs(d0s) / d0errs
    return np.mean(sd0s)




# Declare combined histograms for all provided variabels
combined_hists = {var : hist_init() for var in variables.keys()}
for var in combined_hists.keys():
    for mjpt in combined_hists[var].keys():
        for nmjpt in combined_hists[var][mjpt].keys():
            for tag in combined_hists[var][mjpt][nmjpt].keys():
                for flavor in combined_hists[var][mjpt][nmjpt][tag].keys():
                    combined_hists[var][mjpt][nmjpt][tag][flavor] = Histogram('mjpt_' + mjpt + '_nmjpt_' + nmjpt + '_' + tag + '_' \
                            + flavor + '_' + var)
                    combined_hists[var][mjpt][nmjpt][tag][flavor].setup_bins(variables[var]['min'], variables[var]['max'], variables[var]['bin'])

# Main code
for name in os.listdir(directory):
    print 'Processing: %s... ' % (name)
    hists = {var : hist_init() for var in variables.keys()}

    # Get weighting info for the slice
    sum_of_w = 0
    xsec = weight[name.split('.')[3]]['xsec']
    filterEff = weight[name.split('.')[3]]['filterEff']

    # Loop over root files in each mc slice
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

                '''
                print 'trkjet_assocTrk_d0 ='
                print mychain.trkjet_assocTrk_d0
                print 'trkjet_assoc_d0err ='
                print mychain.trkjet_assocTrk_d0err
                print 'trkjet_phi ='
                print mychain.trkjet_phi
                print 'fat_assocTrkjet_ind ='
                print mychain.fat_assocTrkjet_ind
                '''
                
                # Get event weight
                mc_eve_w = mychain.eve_mc_w * mychain.eve_pu_w
                sum_of_w = sum_of_w + mc_eve_w

                for fj in fjFilter():
                    print 'fj', fj
                    mj_ind = fj[0][0]
                    nmj_ind = fj[0][1]
                    fj_ind = fj[1]
                    pt_label = GetPt(fj[0])
                    flavor_label = GetFlavor(fj[0])
                    tag_label = XbbScoreTagger(fj_ind)
                    trkjet_name = 'mjpt_' + pt_label[0] + '_nmjpt_' + pt_label[1] + '_' + tag_label + '_' + flavor_label

                    values = {var : 0 for var in variables.keys()}
                    # TODO: read out variable values for each fat jet
                    for trkjet_ind in fj[0]:
                        print trkjet_ind
                        print Get_meanSd0(trkjet_ind)

                    # Accesses histogram, check existence
                    for var in variables.keys():
                        if hists[var][pt_label[0]][pt_label[1]][tag_label][flavor_label] == 0:
                            hists[var][pt_label[0]][pt_label[1]][tag_label][flavor_label] = \
                                    Histogram(trkjet_name + '_' + var + name.split('.')[3])
                            hists[var][pt_label[0]][pt_label[1]][tag_label][flavor_label].setup_bins\
                                    (variables[var]['min'], variables[var]['max'], variables[var]['bin'])
                            hists[var][pt_label[0]][pt_label[1]][tag_label][flavor_label].add_point(values[var], mc_eve_w)

                        else:
                            hists[var][pt_label[0]][pt_label[1]][tag_label][flavor_label].add_point(values[var], mc_eve_w)
    # Add on slice-wise weight
    for var in hists.keys():
        for mjpt in hists[var].keys():
            for nmjpt in hists[var][mjpt].keys():
                for tag in hists[var][mjpt][nmjpt].keys():
                    for flavor in hists[var][mjpt][nmjpt][tag].keys():
                        if hists[var][mjpt][nmjpt][tag][flavor] == 0:
                            continue
                        else:
                            hists[var][mjpt][nmjpt][tag][flavor].rescale(xsec * filterEff / sum_of_w)
                            combined_hists[var][mjpt][nmjpt][tag][flavor].combine(hists[var][mjpt][nmjpt][tag][flavor])
    print 'Histpgrams for %s has been created.' % (name)

# Store combined histograms
for var in combined_hists.keys():
    for mjpt in combined_hists[var].keys():
        for nmjpt in combined_hists[var][mjpt].keys():
            for tag in combined_hists[var][mjpt][nmjpt].keys():
                for flavor in combined_hists[var][mjpt][nmjpt][tag].keys():
                    combined_hists[var][mjpt][nmjpt][tag][flavor].pickle(args.output[0] + '/' + var)
print 'Combined histograms has been created.'
print 'Done!'
