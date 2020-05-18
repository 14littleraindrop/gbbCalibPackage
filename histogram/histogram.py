import cPickle as pickle
import numpy as np
import os

class Histogram(object):
    def __init__(self, name):
        self.name = name
        self.data = dict()

    def setup_bins(self, minimum, maximum, num_bins):
        bin_values = np.linspace(minimum, maximum, num_bins)
        for val in bin_values:
            self.data[val] = 0.0

    def bins(self):
        return sorted(self.data.keys())

    def frequencies(self):
        return [self.data[key] for key in sorted(self.data.keys())]

    def add_point(self, value, weight=1):
        if len(self.bins()) == 0:
            raise ValueError('histogram has no bins')
        difference = value - np.array(sorted(self.bins()))
        index = np.where(difference > 0, difference, np.inf).argmin()
        self.data[sorted(self.bins())[index]] += weight

    def rescale(self, weight):
        for b in self.bins():
            self.data[b] *= weight

    def combine(self, other):
        for b in self.bins():
            self.data[b] += other.data[b]

    def pickle(self, directory=''):
        with open(os.path.join(directory, self.name + '.pickle'), 'wb') as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

