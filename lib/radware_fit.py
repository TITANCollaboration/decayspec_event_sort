# *************************************************************************************
# * Written by : Connor Natzke
# * Started : July 2021 - Still during the plague..
# * Purpose : Fit peaks and return areas
# * Requirements : Python 3, matplotlib, probably something other stuff numpy,scipy...
# * Modified by : Jon Ringuette - Aug 2021
# *************************************************************************************

import lmfit as lm
import numpy as np

from scipy.special import erfc
from scipy.integrate import quad
from numpy import sqrt, exp, pi
import scipy.signal


class radware_fit:
    def __init__(self, prominence=1000):
        self.histogram = None
        self.prominence = prominence
        return

    @staticmethod
    def gaussian(x, centroid, sigma):
        # basic gaussian
        #    return (amplitude / (sqrt(2 * pi) * sigma)) * exp(-(x - centroid)**2 / (2 * sigma**2))
        return exp(-(x - centroid)**2 / (2 * sigma**2))

    @staticmethod
    def skewed_gaussian(x, amplitude, centroid, sigma, R):
        # skewed gaussian
        return amplitude * (1.0 - R / 100.0) * radware_fit.gaussian(x, centroid, sigma)

    @staticmethod
    def peak_bg_function(x, amplitude, centroid, sigma, R, beta):
        # background function
        return R * amplitude / 100.0 * exp((x - centroid) / beta) * erfc((x - centroid) / (sqrt(2.0) * pi) + sigma / (sqrt(2.0) * beta))

    @staticmethod
    def peak_function(x, amplitude, centroid, sigma, R, beta):
        # actual gamma peak
        return radware_fit.skewed_gaussian(x, amplitude, centroid, sigma, R) + radware_fit.peak_bg_function(x, amplitude, centroid, sigma, R, beta)

    @staticmethod
    def step_bg_function(x, amplitude, centroid, sigma, step):
        # basic background function
        return abs(step) * amplitude / 100.0 * erfc((x - centroid) / (sqrt(2.0) * sigma))

    @staticmethod
    def quadratic_bg_function(x, c0, c1, c2, offset):
        return c0 + c1 * (x - offset) + c2 * (x - offset)**2

    @staticmethod
    def total_bg_function(x, amplitude, centroid, sigma, step, c0, c1, c2, offset):
        return radware_fit.step_bg_function(x, amplitude, centroid, sigma, step) + radware_fit.quadratic_bg_function(x, c0, c1, c2, offset)

    @staticmethod
    def total_peak_function(x, amplitude, centroid, sigma, R, beta, step, c0, c1, c2, offset):
        # sum of peak and bg
        return radware_fit.peak_function(x, amplitude, centroid, sigma, R, beta) + radware_fit.total_bg_function(x, amplitude, centroid, sigma, step, c0, c1, c2, offset)

    def get_peak_area(self, fit, limit_low, limit_high):
        # integrates peak function and background function. Then finds the difference
        params = fit.params
        peak_area = quad(radware_fit.peak_function, limit_low, limit_high, args=(
            params['amplitude'].value, params['centroid'].value, params['sigma'].value, params['R'].value, params['beta'].value))
        bg_area = quad(radware_fit.total_bg_function, limit_low, limit_high, args=(
            params['amplitude'].value, params['centroid'].value, params['sigma'].value, params['step'].value, params['c0'].value, params['c1'].value, params['c2'].value, params['offset'].value))
        net_area = peak_area[0] - bg_area[0]
        print(peak_area)
        print(bg_area)
        print(f'Peak Area: {peak_area[0]}')
        return

    def find_best_peak_in_region(self):
        print("Hello!")
        peak_indexes, peak_properties = scipy.signal.find_peaks(self.histogram[self.min_x:self.max_x], prominence=self.prominence, width=1)  # Find all the major peaks
        #print(peak_indexes)
        if not peak_indexes.any():
            return 0, 0
        highest_peak_index = np.unravel_index(peak_properties['prominences'].argmax(), peak_properties['prominences'].shape)[0]  # Find most prominant peak
        #pprint(peak_properties)
        center = peak_indexes[highest_peak_index]
        amplitude = self.histogram[self.min_x+center]
        return center, amplitude

    def radware_peak_fit(self):
        # building composite model
        self.centroid, amplitude = self.find_best_peak_in_region()
        print("hi")
        print("Found centroid from scipy:", self.centroid, "Amplitude:", amplitude)
        model = lm.Model(radware_fit.total_peak_function)

        initial_sigma = sqrt(5 + 1.33 * self.centroid / 1000. + 0.9 * (self.centroid / 1000)**2) / 2.35
        initial_beta = initial_sigma / 2.
        # set initial parameters
        params = lm.Parameters()
        params.add("amplitude", value=amplitude)
        params.add("centroid", value=self.centroid)
        params.add("sigma", value=initial_sigma, min=0.01, max=10.)
        params.add("beta", value=initial_beta, min=0.000001, max=10., vary=False)
        params.add("R", value=0., min=0.000001, max=100., vary=False)
        params.add("step", value=0.218, min=0., max=100.)
        params.add("c0", value=1.0)
        params.add("c1", value=1.0)
        params.add("c2", value=0.0, vary=False)
        params.add("offset", value=0.0, vary=False)

        self.x = np.linspace(1, self.max_x-self.min_x, self.max_x-self.min_x, dtype=int)
        # Removing y_err for now
        # fit_results = model.fit(self.y, x=self.x, params=params, weights=1.0 / self.y_err, scale_covar=False)
        print("hist:", self.histogram[self.min_x:self.max_x])
        print("x:", self.x)
        fit_results = model.fit(self.histogram[self.min_x:self.max_x], x=self.x, params=params, weights=1.0, scale_covar=False)
        return fit_results

    def fit_peak(self, histogram, min_x, max_x):
        self.histogram = histogram
        self.min_x = min_x
        self.max_x = max_x
        # get bins around peak
#        peak = 1460
#        x = histogram.axis().edges()[peak - 20: peak + 20]
#        y = histogram.values()[peak - 20: peak + 20]
        #y_err = histogram.errors()[peak - 20: peak + 20]

        fit = self.radware_peak_fit()
        print(fit.fit_report())
        diff_between_points = (self.max_x - self.min_x)
        print("hi")
        peak_area = self.get_peak_area(fit, 0, diff_between_points)
        print("Peak Area:", peak_area)

        return fit
