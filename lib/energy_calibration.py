from configobj import ConfigObj
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
        self.co60_hist_list = []
        self.co60_peaks = []
        self.eu152_hist_list = []
        self.eu152_peaks = []
        self.eu152_energy_vals = [121.7817, 244.6974, 344.2785, 778.9045, 964.057, 1112.076, 1408.013]  # Taken from https://www.nndc.bnl.gov/nudat2/decaysearchdirect.jsp?nuc=152EU&unc=nds
        # doubleful : 433.9606 ,
        #peak_dict = {'peak_pulse_height': 0, 'peak_center_index': 0, 'est_peak_width': 0, 'est_peak_amp': 0}
        #self.read_in_calibration_file()
        return

    def read_in_calibration_file(self):
        # Read in the calibration file making appropriate dict of polynomial coefficients
        print("Going to read in the config file...")
        config = ConfigObj(self.cal_file)
        for channel in config.keys():
            self.cal_dict[int(config[channel]['chan'])] = np.array(config[channel]['cal_coef'], dtype=float)
        return

    def extend_cal_object(self, hist_list, config):
        for my_hist in hist_list:
            config['CHAN' + str(my_hist['chan'])] = {}
            config['CHAN' + str(my_hist['chan'])]['chan'] = my_hist['chan']
            config['CHAN' + str(my_hist['chan'])]['cal_coef'] = my_hist['poly_fit'].tolist()
        return

    def write_calibration_file(self, cal_output_file):
        config = ConfigObj()
        config.filename = cal_output_file
        self.extend_cal_object(self.co60_hist_list, config)
        self.extend_cal_object(self.eu152_hist_list, config)
        config.write()
        return

    def calibrate_hit(self, hit):
        # Performs a polynomial calibration onto an individual pulse height
        #print("Hi: ", np.polyval(self.cal_dict[hit['chan']], hit['pulse_height']))
        #print("\n")
        #exit(0)
        if hit['chan'] in self.cal_dict.keys():
            hit['pulse_height'] = round(np.polyval(self.cal_dict[hit['chan']], hit['pulse_height']))
            if hit['pulse_height'] > 65536:
                hit['pulse_height'] = 65536  # Overflow!
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

    def find_peaks(self, index, hist_list, peak_finder_dict):
        chan_hist = hist_list[index]
        tallest_peak = np.amax(chan_hist['hist'])
        tallest_peak_index = np.where(chan_hist['hist'] == tallest_peak)[0][0]  # ONly care about peaks to the right of this for both co60 and eu152
        prominence = tallest_peak * peak_finder_dict['prominence_fraction_of_tallest_peak']
        peak_indexes, peak_properties = scipy.signal.find_peaks(chan_hist['hist'],
                                                                height=peak_finder_dict['min_height'],
                                                                prominence=prominence,
                                                                width=peak_finder_dict['min_width'],
                                                                distance=peak_finder_dict['min_distance_between'])  # Find all the major peaks

        print("Peak Indexs:", peak_indexes)
        # print("Peak Properties:", peak_properties)
        if len(peak_indexes) < peak_finder_dict['num_peaks_needed']:
            print("Could not find the", peak_finder_dict['num_peaks_needed'], " needed peaks... INDEXES FOUND:", peak_indexes)
            exit(1)
        try:
            tallest_peak_index_in_found_peaks = np.where(peak_indexes == tallest_peak_index)[0][0]
        except IndexError:
            print("Tallest peak index:", tallest_peak_index)
            print("Could not match tallest peak to a found peak.. Something went terribly wrong")
            exit(1)
        peak_info = []
        for my_peak_index in range(tallest_peak_index_in_found_peaks, len(peak_indexes)):
            print("My Peak Index:", my_peak_index)

            peak_info.append({'est_peak_center': peak_indexes[my_peak_index],
                              'est_peak_width': peak_properties['widths'][my_peak_index],
                              'est_peak_amp': peak_properties['peak_heights'][my_peak_index],
                              'fit_peak_center': None,
                              'fit_peak_fwhm': None,
                              'full_fit_results': None})
        hist_list[index].update({'peak_info': peak_info})
        print(hist_list)
        return

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

    def find_poly_fit(self, hist_list, energy_vals, linear_output_file, index, degree, OVERWRITE=True):
        pulse_height = []
        chan_hist = hist_list[index]
        for my_peak_index in range(len(chan_hist['peak_info'])):
            pulse_height.append(hist_list[index]['peak_info'][my_peak_index]['fit_peak_center'])

        poly_fit = np.polyfit(pulse_height, energy_vals, degree)  # Least squares polynomial fit.
        hist_list[index].update({'poly_fit': poly_fit})
        return

    def perform_fit(self, histograms, fit_type, cal_output_file):
        index = 0
        eu152_peak_finder_dict = {'prominence_fraction_of_tallest_peak': 1/15,
                                  'min_height': 20,
                                  'min_width': 3,
                                  'min_distance_between': 1,
                                  'num_peaks_needed': 7}

        co60_peak_finder_dict = {'prominence_fraction_of_tallest_peak': 1/3,
                                 'min_height': 100,
                                 'min_width': 3,
                                 'min_distance_between': 5,
                                 'num_peaks_needed': 2}

        for chan_dict_key in histograms.keys():
            if sum(histograms[chan_dict_key]) > 10000:
                if fit_type == 'quad':
                    self.eu152_hist_list.append({'chan': chan_dict_key, 'hist': histograms[chan_dict_key]})
                    self.find_peaks(index, self.eu152_hist_list, eu152_peak_finder_dict)
                    self.find_peak_centroid(self.eu152_hist_list, 'peak_info', index)  # Grabbing more of the peak base by *2
                    self.find_poly_fit(self.eu152_hist_list, self.eu152_energy_vals, "myfile.cal", index, 2)
                    pprint(self.eu152_hist_list)
                elif fit_type == 'linear':
                    self.co60_hist_list.append({'chan': chan_dict_key, 'hist': histograms[chan_dict_key]})
                    #self.find_co60_peaks(index)
                    self.find_peaks(index, self.co60_hist_list, co60_peak_finder_dict)
                    self.find_peak_centroid(self.co60_hist_list, 'peak_info', index)  # Grabbing more of the peak base by *2
                    self.find_poly_fit(self.co60_hist_list, self.co60_energy_vals, "myfile.cal", index, 1)
                    pprint(self.co60_hist_list)
                index = index + 1
            else:
                print("index rejected due to too few events:", chan_dict_key)
        self.write_calibration_file(cal_output_file)
        return

    def eq_text_from_fit(self, poly_fit):
        my_fit_eq = ""
        poly_degree_index = len(poly_fit) - 1
        for poly_fit_term in poly_fit:
            if poly_fit_term > 0:
                my_fit_term = '+' + str(round(poly_fit_term, 3))
            else:
                my_fit_term = str(round(poly_fit_term, 3))
            my_fit_eq = my_fit_eq + my_fit_term
            if poly_degree_index > 1:
                my_fit_eq = my_fit_eq + 'x^' + str(poly_degree_index)
            elif poly_degree_index == 1:
                my_fit_eq = my_fit_eq + 'x'
            poly_degree_index = poly_degree_index - 1
        print("Terms in fit.. ", my_fit_eq)
        return my_fit_eq

    def plot_fit(self, cal_source='co60'):
        if cal_source == 'co60':
            hit_list = self.co60_hist_list
            my_title = "Co60 Found Peaks for Calibration"
        elif cal_source == 'eu152':
            hit_list = self.eu152_hist_list
            my_title = "Eu152 Found Peaks for Calibration"

        chan_index = 0
        fig, axs = plt.subplots(len(hit_list), squeeze=False, sharex=True, sharey=True)

        for my_chan in hit_list:
            x_vals = np.linspace(1, len(my_chan['hist']), len(my_chan['hist']))
            axs[chan_index][0].step(x_vals, my_chan['hist'], label='Chan:' + str(my_chan['chan']))  # Generate line graph that will overlay bar graph
            peak_index = 0
            plt.title(my_title)

            tallest_peak = 0
            rightmost_peak = 0
            for my_peak in my_chan['peak_info']:
                axs[chan_index][0].plot(x_vals, my_peak['full_fit_results'].best_fit, label='Best Fit, peak: ' + str(peak_index))
                axs[chan_index][0].axvline(x=my_peak['fit_peak_center'], color='red', linestyle='--', ymin=0, ymax=0.75)
                axs[chan_index][0].text(my_peak['fit_peak_center'], my_peak['est_peak_amp'], round(my_peak['fit_peak_center'], 3), rotation=45)
                if my_peak['est_peak_amp'] > tallest_peak:
                    tallest_peak = my_peak['est_peak_amp']
                if my_peak['fit_peak_center'] > rightmost_peak:
                    rightmost_peak= my_peak['fit_peak_center']

                peak_index = peak_index + 1
            my_fit_eq = self.eq_text_from_fit(my_chan['poly_fit'])
            axs[chan_index][0].text(rightmost_peak/2, tallest_peak, "Chan: " + str(my_chan['chan']) + "- Fit Equation : " + my_fit_eq, fontsize=15)
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
