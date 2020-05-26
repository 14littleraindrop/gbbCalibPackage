import argparse
import glob
import json
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

parser = argparse.ArgumentParser(description='Plot histogram for all pickle file in directory generated by \
        hist_maker.py with each subjet pt slice one plot.')
parser.add_argument('--dir', type=str, nargs=1,
        help='Directory of input pickled files, generated by hist_sort.py', required=True)
parser.add_argument('--config', type=str, nargs=1, help='Config file to use (JSON)', required=True)
parser.add_argument('--output', type=str, nargs=1, help='Output directory name', required=True)
parser.add_argument('--fit', type=str, nargs=1, help='Fitting status. Options: postfit, prefit')
parser.add_argument('--ave', type=str, nargs=1, default=['True'], help='Default is plotting the average of each bin. \
        Plotting regular histogram use False')
args = parser.parse_args()

directory = args.dir[0]
os.mkdir(args.output[0])

with open(args.config[0]) as f:
    config = json.load(f)
mjpt_bins = config['pt_bins']['mjet']
nmjpt_bins = config['pt_bins']['nmjet']
flavors = config['flavors']
variables = config['variables']

# Generate list of pt labels
pt_labels = ['mjpt_l' + str(mjpt_bins[0]) + '_nmjpt_l' + str(nmjpt_bins[0]),\
        'mjpt_l' + str(mjpt_bins[0]) + '_nmjpt_g' + str(nmjpt_bins[0]) + 'l' + str(nmjpt_bins[1]),\
        'mjpt_l' + str(mjpt_bins[0]) + '_nmjpt_g' + str(nmjpt_bins[1]),\
        'mjpt_g' + str(mjpt_bins[0]) + 'l' + str(mjpt_bins[1]) + '_nmjpt_l' + str(nmjpt_bins[0]),\
        'mjpt_g' + str(mjpt_bins[0]) + 'l' + str(mjpt_bins[1]) + '_nmjpt_g' + str(nmjpt_bins[0]) + 'l' + str(nmjpt_bins[1]),\
        'mjpt_g' + str(mjpt_bins[0]) + 'l' + str(mjpt_bins[1]) + '_nmjpt_g' + str(nmjpt_bins[1]),\
        'mjpt_g' + str(mjpt_bins[1]) + '_nmjpt_l' + str(nmjpt_bins[0]),\
        'mjpt_g' + str(mjpt_bins[1]) + '_nmjpt_g' + str(nmjpt_bins[0]) + 'l' + str(nmjpt_bins[1]),\
        'mjpt_g' + str(mjpt_bins[1]) + '_nmjpt_g' + str(nmjpt_bins[1])]

for var in os.listdir(directory):
    os.mkdir(args.output[0] + '/' + var)
    print 'Processing variable: %s...' % (var)
    for pt_label in pt_labels:
        print 'Plotting pt region: %s...' % (pt_label)

        accum_hist_post_tag = Histogram('post_tag')
        accum_hist_pre_tag = Histogram('pre_tag')
        accum_hist_post_tag.setup_bins(variables[var]['min'], variables[var]['max'], variables[var]['bin'])
        accum_hist_pre_tag.setup_bins(variables[var]['min'], variables[var]['max'], variables[var]['bin'])

        for flavor in ['BB', 'BL', 'CC', 'CL', 'LL']:
            hist_tag_name = pt_label + '_2TAG' + '_' + flavor + '_' + var + '.pickle'
            hist_notag_name = pt_label + '_NOT2TAG' + '_' + flavor + '_' + var + '.pickle'

            with open(os.path.join(directory, var, hist_tag_name), 'rb') as f:
                hist_post_tag = pickle.load(f)
            with open(os.path.join(directory, var, hist_notag_name), 'rb') as f:
                hist_pre_tag = pickle.load(f)
            hist_pre_tag.combine(hist_post_tag)
            
            if args.ave[0] == 'True':
                hist_post_tag.rescale(1 / (hist_post_tag.bins()[1] - hist_post_tag.bins()[0]))
                hist_pre_tag.rescale(1 / (hist_pre_tag.bins()[1] - hist_pre_tag.bins()[0]))

            if flavor == 'BB':
                color = 'mediumblue'
            elif flavor == 'BL':
                color = 'cornflowerblue'
            elif flavor == 'CC':
                color = 'seagreen'
            elif flavor == 'CL':
                color = 'mediumspringgreen'
            else:
                color = 'gold'

            plt.figure(1)
            plt.bar(hist_post_tag.bins(), hist_post_tag.frequencies(), width = (hist_post_tag.bins()[1] - hist_post_tag.bins()[0]), color = color, edgecolor = 'black',\
                    linewidth = 0.5, bottom = accum_hist_post_tag.frequencies(), label = flavor)
            plt.figure(2)
            plt.bar(hist_pre_tag.bins(), hist_pre_tag.frequencies(), width = (hist_pre_tag.bins()[1] - hist_pre_tag.bins()[0]), color = color, edgecolor = 'black', \
                    linewidth = 0.5, bottom = accum_hist_pre_tag.frequencies(), label = flavor)

            accum_hist_post_tag.combine(hist_post_tag)
            accum_hist_pre_tag.combine(hist_pre_tag)

        plt.figure(1)
        plt.legend()
        plt.xlabel(var)
        if var == 'mjmeanSd0' or var == 'nmjmeanSd0':
            if args.ave[0] == 'True':
                plt.ylabel('dN/dSd0')
        else:
            plt.ylabel('Frequency')
        plt.ylim(0, None)
        plt.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
        plt.title(var + '_' + args.fit[0] + '_posttag_' + pt_label)
        plt.savefig(args.output[0] + '/' + var + '/' + var + '_' + args.fit[0] + '_posttag_' + pt_label + '.png')
        plt.clf()

        plt.figure(2)
        plt.legend()
        plt.xlabel(var)
        if var == 'mjmeanSd0' or var == 'nmjmeanSd0':
            if args.ave[0] == 'True':
                plt.ylabel('dN/dSd0')
        else:
            plt.ylabel('Frequency')
        plt.ylim(0, None)
        plt.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
        plt.title(var + '_' + args.fit[0] + '_pretag_' + pt_label)
        plt.savefig(args.output[0] + '/' + var + '/' + var + '_' + args.fit[0] + '_pretag_' + pt_label + '.png')
        plt.clf()
    print 'Done ploting variable: %s!!' % (var)
print 'Done!!!'
