import argparse
import os
import sys
import math 
from ROOT import *

parser = argparse.ArgumentParser(description='Plot fat_pt histogram for a directory of given input files.')
parser.add_argument('directory', metavar='DIRECTORY', type=str, nargs=1, 
        help='Directory of text files containing locations of ROOT files to process')
args = parser.parse_args()
directory = args.directory[0]

c1 = TCanvas('c1', 'title')

files = dict()

for name in os.listdir(directory):
    with open(os.path.join(directory, name), 'r') as f:
        for line in f.readlines():
            tfile = TFile(line.strip())
            if name in files:
                files[name].append(tfile)
            else:
                files[name] = [tfile]

hists = []
for name in files.keys():
    hist = TH1F("fat_pt_" + name, "pt_" + name, 200, 0, 1600000)
    hists.append(hist)
    for tfile in files[name]:
        mychain = tfile.Get('FlavourTagging_Nominal')
        entries = mychain.GetEntriesFast()
        print "The number of entries is: ", entries

        for i in range(entries):
            nb = mychain.GetEntry(i)
            if nb <= 0:
                continue
            fat_pt = mychain.fat_pt
            [hist.Fill(n) for n in fat_pt]
    hist.Draw('same')

c1.Update()
c1.SaveAs("fat_jet.pdf")
