from configobj import ConfigObj
from numpy.polynomial.polynomial import polyval
import pandas as pd
import numpy as np
import scipy.signal
from lmfit.models import LorentzianModel, GaussianModel
from pprint import pprint
import matplotlib.pyplot as plt
#from lmfit import Model

class energy_calibration:

    def __init__(self, cal_file=None):
        self.cal_file = cal_file
        self.cal_dict = {}
        self.MIN_CHAN_COUNT = 10000
        self.co60_hit_list = None
        self.co60_energy_vals = [1173.228, 1332.492]

        #peak_dict = {'peak_pulse_height': 0, 'peak_center_index': 0, 'est_peak_width': 0, 'est_peak_amp': 0}
        self.co60_peaks = []
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

    def raw_to_histograms(self, particle_hit_list, min_pulse_height, max_pulse_height, nbins, save_dataframe_file=None):
        #  No longer used, have it go directly from MIDAS to histogram now.
        self.co60_hist_list = []  # List to hold dicts of channel # and histogramed data
        nbins_array = np.linspace(1, max_pulse_height, nbins) # We need even bins, if you don't use this you get crazy bins, no one wants crazy bins.
        print("Converting to Pandas Dataframe...")
        if particle_hit_list is None:  # This is used to create an intermediary file so that we can load the dataframe directly without having to decode the
            print("Reading from intermediary DataFrame File :", save_dataframe_file)
            co60_df = pd.read_csv(save_dataframe_file)  # ^ Midas file again
        else:
            co60_df = pd.DataFrame(particle_hit_list)
            if save_dataframe_file is not None:
                print("Writing to intermediary DataFrame File :", save_dataframe_file)
                co60_df.to_csv(save_dataframe_file)
        recorded_channels = co60_df.chan.unique()
        print("Converting channel data to histogram data...")
        for my_chan in recorded_channels:
            if len(co60_df[(co60_df['flags'] == 1) & (co60_df['chan'] == my_chan)]) > self.MIN_CHAN_COUNT:  # Sometimes channels just have noise and not calibration data
                print("* Processing channel :", my_chan, "with nbins", nbins, "min", min_pulse_height, "max", max_pulse_height)
                self.co60_hist_list.append({'chan': my_chan, 'hist': np.histogram(co60_df[(co60_df['flags'] == 1) &
                                                                                  (co60_df['chan'] == my_chan) &
                                                                                  (co60_df['pulse_height'] > min_pulse_height) &
                                                                                  (co60_df['pulse_height'] < max_pulse_height)].pulse_height.to_numpy(), bins=nbins_array)[0]})
            else:
                print("! Discarding Channel", my_chan, "due to total channel hits being below the min threshold of", self.MIN_CHAN_COUNT, "total counts.")
        return

    def find_co60_peaks(self, chan, index):
        # Find the Co 60 peaks, we need a reasonable amount of data to do this, > 10,000 hits but more is better
        # Look for tallest peak and see if that lines up with a found peak using scipy.signal.find_peaks, if it does that's our first Co60 line
        # Then just move to the next found peak index and that is our 2nd Co60 peak.  We could also take a look at widths as the 2 Co60 peaks should also
        # have the smallest widths
        chan_hist = self.co60_hist_list[index]
        # We need around 2000 counts of the first peak..
        peak_indexes, peak_properties = scipy.signal.find_peaks(chan_hist['hist'], height=1000, prominence=2000, width=1, distance=5)  # Find all the major peaks
        first_co60_peak = np.where(chan_hist['hist'] == np.amax(chan_hist['hist']))[0][0]  # Find the 1173 peak, will(should) be the biggest or something is wrong..
        # Trying to move the below under the channel so we get all channels..
        first_co60_peak_index = np.where(peak_indexes == first_co60_peak)[0][0]
        second_co60_peak_index = first_co60_peak_index + 1  # We look just to the right on the biggest peak to find the 1332 peak
        co60_peaks = []
        for my_peak_index in first_co60_peak_index, second_co60_peak_index:
            co60_peaks.append({'est_peak_center': peak_indexes[my_peak_index],
                               'est_peak_width': peak_properties['widths'][my_peak_index],
                               'est_peak_amp': peak_properties['peak_heights'][my_peak_index],
                               'fit_peak_center': None,
                               'fit_peak_fwhm': None,
                               'full_fit_results': None})
        self.co60_hist_list[index].update({'peak_info': co60_peaks})
        pprint(self.co60_hist_list)
        return #self.co60_peaks

    def find_peak_centroid(self, hist_list, peak_info_label, index):
        model = GaussianModel()
        chan_hist = hist_list[index]
        x_vals = np.linspace(1, len(chan_hist['hist']), len(chan_hist['hist']))
        # We need even bins, if you don't use this you get crazy bins, no one wants crazy bins.
        print(chan_hist['chan'])
        for my_peak_index in range(len(chan_hist[peak_info_label])):
            my_peak = hist_list[index][peak_info_label][my_peak_index]
            #x_vals_around_peak = np.linspace(my_peak['est_peak_center'] - 50, my_peak['est_peak_center'] + 50, 100)
            result = model.fit(chan_hist['hist'], x=x_vals, amplitude=my_peak['est_peak_amp'], center=my_peak['est_peak_center'], sigma=1)  # Does the actual fitting

            hist_list[index][peak_info_label][my_peak_index]['fit_peak_center'] = result.params['center'].value
            hist_list[index][peak_info_label][my_peak_index]['fit_peak_fwhm'] = result.params['fwhm'].value
            hist_list[index][peak_info_label][my_peak_index]['full_fit_results'] = result

            print("Center :", result.params['center'].value, "FWHM :", result.params['fwhm'].value)
            #print(result.fit_report())
        return

    def find_co60_centroids(self, index):
        self.find_peak_centroid(self.co60_hist_list, 'peak_info', index)  # Grabbing more of the peak base by *2
        return

    def find_linear_fit_from_co60(self, linear_output_file, index, OVERWRITE=True):
        pulse_height = []
        chan_hist = self.co60_hist_list[index]
        for my_peak_index in range(len(chan_hist['peak_info'])):
            pulse_height.append(self.co60_hist_list[index]['peak_info'][my_peak_index]['fit_peak_center'])

        linear_fit = np.polyfit(pulse_height, self.co60_energy_vals, 1)  # Least squares polynomial fit.
        self.co60_hist_list[index].update({'linear_fit': linear_fit})
        return

    def perform_linear_fit(self, histograms):
        self.co60_hist_list = []  # List to hold dicts of channel # and histogramed data
        index = 0
        for chan_dict_key in histograms.keys():
            if sum(histograms[chan_dict_key]) > 10000:
                self.co60_hist_list.append({'chan': chan_dict_key, 'hist': histograms[chan_dict_key]})
                self.find_co60_peaks(chan_dict_key, index)
                self.find_co60_centroids(index)
                #if cal_output_file is None:
                    #linear_output_file = 'testme.lin'
                #else:
                    #linear_output_file = cal_output_file
                self.find_linear_fit_from_co60("myfile.cal", index)
                index = index + 1
                pprint(self.co60_hist_list)
            else:
                print("index rejected due to too few events:", chan_dict_key)
        return

    def plot_fit(self, cal_source='co60'):
        if cal_source == 'co60':
            hit_list = self.co60_hist_list
            my_title = "Co60 Calibration"
        elif cal_source == 'eu152':
            hit_list = self.eu152_hist_list
            my_title = "Eu152 Calibration"

        chan_index = 0
        fig, axs = plt.subplots(len(hit_list), squeeze=False, sharex=True, sharey=True)

        for my_chan in hit_list:
            x_vals = np.linspace(1, len(my_chan['hist']), len(my_chan['hist']))

            axs[chan_index][0].step(x_vals, my_chan['hist'], label='Chan:' + str(my_chan['chan']))  # Generate line graph that will overlay bar graph
            peak_index = 0

            for my_peak in my_chan['peak_info']:
                axs[chan_index][0].plot(x_vals, my_peak['full_fit_results'].best_fit, label='Best Fit, peak: ' + str(peak_index))
                peak_index = peak_index + 1
            chan_index = chan_index + 1

        plt.title(my_title)
        plt.xlabel("Bin")
        plt.ylabel("Count")
        plt.legend(loc='best')
        plt.show()
        return

# Performance stuff
# 1:20 no calibration
# 4:40 w/ Calibration (normal list)
# 3:50 w/ cdlibration (numpy list for coeff)
