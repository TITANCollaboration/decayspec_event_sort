from configobj import ConfigObj
from numpy.polynomial.polynomial import polyval
#from numpy import array
import pandas as pd
import numpy as np

class energy_calibration:

    def __init__(self, cal_file=None):
        self.cal_file = cal_file
        self.cal_dict = {}
        self.MIN_CHAN_COUNT = 10000

        #self.read_in_calibration_file()
        return

    def read_in_calibration_file(self):
        # Read in the calibration file making appropriate dict of polynomial coefficients
        print("Going to read in the config file...")
        config = ConfigObj(self.cal_file)
        for adc in config.keys():
            adc_prefix = int(config[adc]['prefix'])
            for adc_channel in config[adc]:
                if adc_channel != "prefix":
                    # Sorry about this line.. I put the channel + prefix as a dict key and then the coefficients as a numpy array as the value of that key
                    # leads to something like : {12: array([1., 2., 3.]), 13: array([2., 2., 3.]), 14: array([1. , 0.5]), 15: array([1. , 0.5])}
                    self.cal_dict[int(config[adc][adc_channel]['chan']) + adc_prefix] = np.array(list(map(float, config[adc][adc_channel]['cal_coef'].split())))

    def calibrate_hit(self, hit):
        # Performs a polynomial calibration onto an individual pulse height
        hit['pulse_height'] = polyval(hit['pulse_height'], self.cal_dict[hit['chan']], tensor=False)
        return hit

    def calibrate_list(self, hit_list):
        # Loop through all pulse heights to calibrate against
        print("Calibrating particle list...")
        for hit_pos in range(0, len(hit_list)):
            hit_list[hit_pos] = self.calibrate_hit(hit_list[hit_pos])
        return hit_list

    def raw_to_histograms(self, particle_hit_list, min_pulse_height, max_pulse_height, nbins):
        self.hist_list = []  # List to hold dicts of channel # and histogramed data
        nbins_array = np.linspace(1, max_pulse_height, nbins) # We need even bins, if you don't use this you get crazy bins, no one wants crazy bins.
        print("Converting to Pandas Dataframe...")
        if particle_hit_list is None:
            df = pd.read_csv("my_cal.csv")
            print(df)
        else:
            df = pd.DataFrame(particle_hit_list)
        #df.to_csv("my_cal.csv")
        #print(len(df[(df['flags'] == 1) & (df['chan'] == 1)]))
        recorded_channels = df.chan.unique()
        print("Converting channel data to histograms...")
        for my_chan in recorded_channels:
            if len(df[(df['flags'] == 1) & (df['chan'] == my_chan)]) > self.MIN_CHAN_COUNT:
                print("* Processing channel :", my_chan, "with nbins", nbins, "min", min_pulse_height, "max", max_pulse_height)
                self.hist_list.append({'chan': my_chan, 'hist': np.histogram(df[(df['flags'] == 1) &
                                                                        (df['chan'] == my_chan) &
                                                                        (df['pulse_height'] > min_pulse_height) &
                                                                        (df['pulse_height'] < max_pulse_height)].pulse_height.to_numpy(), bins=nbins_array)[0]})
            else:
                print("! Discarding Channel", my_chan, "due to total channel hits being below the min threshold of", self.MIN_CHAN_COUNT, "total counts.")
        #del df
        #return hist_list

# Performance stuff
# 1:20 no calibration
# 4:40 w/ Calibration (normal list)
# 3:50 w/ cdlibration (numpy list for coeff)
