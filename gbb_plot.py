import argparse
import os
import sys
import math 
from ROOT import TFile
import matplotlib
matplotlib.use('pdf')
matplotlib.rc('figure', figsize=(8, 5))
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Plot fat_pt histogram for a directory of given input files.')
parser.add_argument('directory', metavar='DIRECTORY', type=str, nargs=1, 
        help='Directory of text files containing locations of ROOT files to process')
args = parser.parse_args()
directory = args.directory[0]

for name in os.listdir(directory):
    fat_pt_values = []
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
                fat_pt = mychain.fat_pt
                [fat_pt_values.append(item) for item in fat_pt]
    plt.hist(fat_pt_values, 200, histtype='step', stacked=True, fill=False, 
            label=name.split('.')[3])
plt.legend()
plt.xlabel('pt (GeV)')
plt.ylabel('jet count')
plt.ticklabel_format(axis="x", style="sci", scilimits=(0,0))
plt.yscale('log')
plt.title('Large R jet pt distribution')
plt.savefig("large_R_jet_pt.png") 

