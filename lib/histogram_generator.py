###################################################
# Library to read in histogram data or raw data and create complicated histograms
###################################################

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import sqrt, ceil
from scipy.ndimage import gaussian_filter1d
from lib.input_handler import input_handler
import scipy.signal
from lmfit.models import LorentzianModel, GaussianModel, LinearModel
from pprint import pprint
from lmfit.models import ExpressionModel

class hist_gen:
    def __init__(self, input_filename, save_all=False, overlay_files=None, max_pulse_height=8192, min_pulse_height=0, title=None, xlabel=None, ylabel=None, energy_labels=None, y_axis_min=0, y_axis_max=None, zoom=False, zoom_xmin=None, zoom_xmax=None, zoom_ymin=None, zoom_ymax=None, ylog_zoom=None, overlay_multipliers=None, output_filename=None, ylog=False, bin_number=None):
        self.flags = 1  # if there is a flag that needs to be used for the root file raw data
        self.bin_number = bin_number
        self.min_pulse_height = min_pulse_height  # min x value
        self.max_pulse_height = max_pulse_height  # max x value
        self.title = title  # main graph title
        self.xlabel = xlabel  # x axis label, main graph
        self.ylabel = ylabel  # y axis label, main graph
        self.energy_labels = energy_labels  # Which peaks to label
        self.zoom_xmin = zoom_xmin  # x min for zoomed region
        self.zoom_xmax = zoom_xmax  # y min for zoomed region
        self.zoom = zoom
        self.zoom_label = True  # If should label zoomed region
        self.ylog = ylog
        self.ylog_zoom = ylog_zoom  # If zoomed region shold be in log scale
        self.title_font_size = 20  # Title font size
        self.axis_font_size = self.title_font_size  # axis font size
        self.tick_font_size = 20  # Font size for graph tick values
        self.label_font_size = 12  # Font size for label
        self.y_axis_min = y_axis_min  # main graph y min
        self.y_axis_max = y_axis_max  # main graph y max
        self.smearing = False  # if the histogram should be smeared using gaussing smearing
        self.input_filename = input_filename
        self.save_all = save_all  # If a hist datafile should be saved
        self.overlay_files = overlay_files  # Files for overlays on top of main graph
        self.histo_multiplier = 1  # overall multiplier to apply to main graph
        self.overlay_multiplier = 1  # Overall  multiplier to apply to zoomed region
        self.zoom_ymin = zoom_ymin  # zoomed region ymin
        self.zoom_ymax = zoom_ymax  # zoomed region ymaxs
        self.overlay_multipliers = overlay_multipliers  # Multiplies to apply to zoomed region
        #self.overlay_multipliers = [1e4, 1e5, 1e6, 1e7]  # Multiplies to apply to zoomed region
        self.overlay_chan = 99  # channel in hist file for overlay (small zoomed graph)
        self.chan = 99  # channel used for primary graph and for saving to hist format
        self.fit_peak_xmin = 1155
        self.fit_peak_xmax = 1170
        # --zoom_xmin 1140 --zoom_xmax 1180
        self.fit_peak = False
        self.smear_overlay = False
        self.output_filename = output_filename
        self.gothere = 0

    def peak_fitting(self, my_hist, my_axes, min_fit_peak, max_fit_peak):
        #print("Min fit peak", min_fit_peak, "Max fit peak", max_fit_peak)
        # First we find the best peak in the area and then we fit it with a gaussian
        peak_indexes, peak_properties = scipy.signal.find_peaks(my_hist[min_fit_peak:max_fit_peak], prominence=1000, width=1)  # Find all the major peaks
        #print(peak_indexes)
        if not peak_indexes.any():
            return 0, 0
        highest_peak_index = np.unravel_index(peak_properties['prominences'].argmax(), peak_properties['prominences'].shape)[0]  # Find most prominant peak
        #pprint(peak_properties)
        best_index = peak_indexes[highest_peak_index]
        local_energy_axis = np.linspace(1, max_fit_peak-min_fit_peak, max_fit_peak-min_fit_peak, dtype=int)
        gaussian = GaussianModel()
        background = LinearModel()
        model = gaussian + background  # Use Guassian for peak and linear for background
        result = model.fit(my_hist[min_fit_peak:max_fit_peak],
                           x=local_energy_axis,
                           amplitude=my_hist[min_fit_peak+best_index],
                           sigma=1,
                           center=best_index)  # Does the actual fitting
        if result.params['amplitude'].value > 0:
            print(result.fit_report())
            best_fit = result.best_fit
            true_peak_center = min_fit_peak + best_index
            fit_energy_axis = np.linspace(self.fit_peak_xmin,
                                          self.fit_peak_xmax,
                                          self.fit_peak_xmax-self.fit_peak_xmin,
                                          dtype=int)
            my_axes.plot(fit_energy_axis, best_fit)
            return true_peak_center, best_fit
        return 0, 0

    def gaussian_smearing(self, initdata, sigma=1):
        # Apply guassian smearing to data, set via sigma value.
        # sigma = 1 is approx 2.3keV for FWHM
        newdata = gaussian_filter1d(initdata, sigma=sigma)
        return newdata

    def label_peaks(self, axes, my_hist, ymax, label_xmin, label_xmax, height=0.5):
        # Draw a line at center of peak and put a text label indicating the x value
        for my_label in self.energy_labels:
            if (int(my_label) < label_xmax) and (int(my_label) > label_xmin):
                axes.axvline(x=int(my_label)+1, color='red', linestyle='--', ymin=0, ymax=0.75, lw=1)
                axes.text(int(my_label), 20000, str(my_label), rotation=45, fontsize=self.label_font_size)
        return 0

    def sci_notation(self, number, sig_fig=0):
        # Just put's things into 10^? notation
        ret_string = "{0:.{1:d}e}".format(number, sig_fig)
        a, b = ret_string.split("e")
        b = int(b)
        return "10^" + str(b)

    def graph_with_overlays(self, my_axis, energy_axis, my_hist, zoomed):
        # Main graphing function, determines if there is a zoomed region or multipliers
        # it also handles overlays which is just data form a file to add to the main graph or
        # zoomed region
        if (self.overlay_files is not None) and (zoomed is True):
            for my_overlay_file in self.overlay_files:
                if self.overlay_multipliers is None:
                    self.overlay_multipliers = [1]
                for my_multiplier in self.overlay_multipliers:
                    myinput = input_handler(my_overlay_file)
                    my_overlay_df = myinput.read_in_data()

                    if zoomed is True:
                        my_overlay_df = (my_overlay_df[self.zoom_xmin-1:self.zoom_xmax-1] * my_multiplier)

                    else:
                        my_overlay_df = my_overlay_df * my_multiplier
                    length_diff = len(my_hist) - len(my_overlay_df[str(self.overlay_chan)])

                    my_zeros = np.zeros(length_diff)
                    my_overlay_df = np.concatenate((my_overlay_df[str(self.overlay_chan)], my_zeros))

                    length_diff = len(my_hist) - len(my_overlay_df)
                    if self.smear_overlay is True:
                        my_overlay_df = self.gaussian_smearing(my_overlay_df, 1)
                    combined_hist = 0
                    combined_hist = my_hist + my_overlay_df
                    if my_multiplier == 0:
                        my_label = "Background"
                    else:
                        my_label = "NEEC " + self.sci_notation(my_multiplier)
                    linewidth = 0.5
                    if zoomed is True:
                        linewidth = 2
                    my_axis.step(energy_axis, combined_hist, where='mid', label=my_label, linewidth=linewidth)
                    if self.fit_peak is True and (self.fit_peak_xmin >= self.zoom_xmin) and (self.fit_peak_xmax <= self.zoom_xmax):  # make sure zoom is also between the two fit values
                        #self.gothere = self.gothere + 1
                        if my_multiplier > 0:
                            print("Overlay Multiplier:", self.sci_notation(my_multiplier))
                            self.peak_fitting(combined_hist,
                                              my_axis,
                                              self.fit_peak_xmin-self.zoom_xmin,
                                              self.fit_peak_xmax-self.zoom_xmin)
        else:
            if self.smearing is True:
                my_hist = self.gaussian_smearing(my_hist)
            my_axis.step(energy_axis, my_hist)#, where='mid')

    def create_chan_basic_histograms(self, my_hist, energy_axis):
        # Set up all graphing parameters and call graph_with_overlays to actually do the graphing
        my_hist = my_hist * self.histo_multiplier  # apply multiplier to primary graph

        ymax = my_hist.max()
        self.fig, self.axes = plt.subplots(num=None, figsize=(16, 12), dpi=96, facecolor='w', edgecolor='k')  # sharex=True, sharey=True,
        self.axes.tick_params(labelsize=self.tick_font_size)
        if self.ylog is True:
            plt.yscale("log")

        if self.fit_peak is True:
        #    self.min_pulse_height = self.fit_peak_xmin
        #    self.max_pulse_height = self.fit_peak_xmax
            #true_peak_center, best_fit = self.peak_fitting(my_hist, self.axes, self.fit_peak_xmin, self.fit_peak_xmax)
            print("Fix me... sometime..")

        self.graph_with_overlays(self.axes, energy_axis, my_hist, False)

        if (self.energy_labels is not None):
            self.label_peaks(self.axes, my_hist, ymax, self.min_pulse_height, self.max_pulse_height, height=0.03)

        plt.title(self.title, fontsize=self.title_font_size)
        plt.xlabel(self.xlabel, fontsize=self.axis_font_size)
        plt.ylabel(self.ylabel, fontsize=self.axis_font_size)

        if self.zoom is True:
            sub_axes = plt.axes([.5, .5, .37, .35])  # Location of zoomed section in relation to main graph ;  [left, bottom, width, height]
            ymax_sub = energy_axis[self.zoom_xmin:self.zoom_xmax].max()
            self.graph_with_overlays(sub_axes, energy_axis[self.zoom_xmin:self.zoom_xmax], my_hist[self.zoom_xmin:self.zoom_xmax], True)

            sub_axes.set_xlim([self.zoom_xmin, self.zoom_xmax])  # Set x-axis for insert graph
            if (self.zoom_ymin is not None) and (self.zoom_ymax is not None):
                sub_axes.set_ylim([self.zoom_ymin, self.zoom_ymax])

            sub_axes.tick_params(labelsize=self.tick_font_size)

            if (self.energy_labels is not None) and (self.zoom_label is True):
                self.label_peaks(sub_axes, my_hist, ymax_sub, self.zoom_xmin, self.zoom_xmax)
            if self.ylog_zoom is True:
                plt.yscale("log")
        self.axes.set_xlim([self.min_pulse_height, self.max_pulse_height])
        if self.y_axis_max is None:
            self.y_axis_max = my_hist[self.min_pulse_height:self.max_pulse_height].max() * 1.2
        print("Yaxis max", self.y_axis_max)
        self.axes.set_ylim([self.y_axis_min, self.y_axis_max])
        if self.ylog is False:
            self.axes.ticklabel_format(style='plain')
        plt.legend(title='Parameters:', fontsize=self.label_font_size)
        if self.output_filename is None:
            self.output_filename = self.input_filename + '.png'
        print("Saving graph as:", self.output_filename)
        plt.savefig(self.output_filename, dpi=96)  # Save current graph as png file
        plt.show()

        return 0

    def determine_input_type(self, columns):
        # much like the name is, it figures out if we have a root raw file or a pandas histogram
        if 'pulse_height' in columns:
            return 'raw'
        else:
            return 'histo'

    def generate_histo_from_raw(self, mydata_df, channels):
        # read in a raw data file from CSV : chan, pulse_height, flag
        # It will also save this as a histogram file
        energy_axis = None
        my_hist = None
        pulse_height = mydata_df[mydata_df['chan'].isin(channels) &
                                 (mydata_df['flags'] == self.flags) &
                                 (mydata_df['pulse_height'] >= self.min_pulse_height) &
                                 (mydata_df['pulse_height'] <= self.max_pulse_height)]['pulse_height'].to_numpy()
        if len(pulse_height) > 0:
            energy_axis = np.linspace(0, pulse_height.max(), pulse_height.max(), dtype=int)
            my_hist = np.histogram(pulse_height, bins=energy_axis)[0]
            my_hist = np.append(my_hist, [0])  # Sizes kept coming out slightly off so.. fixed it?
        else:
            print("No data found in channel:", channels)
        if self.save_all is True:
            print("Writing file:", self.input_filename + '.hist')
            mydata_df =  pd.DataFrame(data={self.chan: my_hist})
            mydata_df.to_csv(self.input_filename + '.hist', sep='|', header=True, index=False, chunksize=50000, mode='w', encoding='utf-8')

        return energy_axis, my_hist

    def generate_histo_from_histo(self, mydata_df, channels):
        # Read in data from hist file, currently reads in all channels except summed_hist
        for my_chan in channels:
            print("Summing channel:", my_chan)
            if my_chan != 'summed_hist':  # Make sure we don't sum out summing column.. yup..
                mydata_df['summed_hist'] = mydata_df[str(my_chan)] + mydata_df['summed_hist']

        #energy_axis = np.linspace(0, len(mydata_df['summed_hist'].values) + 1, len(mydata_df['summed_hist'].values) + 1, dtype=int)
        energy_axis = np.linspace(0, len(mydata_df['summed_hist'].values), len(mydata_df['summed_hist'].values), dtype=int)
#        my_hist = np.concatenate(([0], mydata_df['summed_hist'])) # If this is coming from GEANT4 there is no 0 bin
        my_hist = mydata_df['summed_hist']  # if it's coming from MIDAS there is a 0 bin
        print("myhist:", my_hist)

        return energy_axis, my_hist

    def grapher(self, mydata_df, channels, sum_all=True):
        # determine what data we are reading in and call appropriate functions to read and graph
        energy_axis = None
        my_hist = None
        input_type = self.determine_input_type(mydata_df.columns)
        print("Input Type :", input_type)

        if sum_all is True:
            if input_type == 'raw':
                channels = mydata_df.chan.unique()  # Get all available channels
                energy_axis, my_hist = self.generate_histo_from_raw(mydata_df, channels)

            elif input_type == 'histo':  # if we are taking in histogram type data we will need to sum the pandas channel based columns
                mydata_df['summed_hist'] = 0
                channels = mydata_df.columns
                energy_axis, my_hist = self.generate_histo_from_histo(mydata_df, channels)
            print("Summed channels:", channels)
            print("Event Count:", np.sum(my_hist[self.min_pulse_height:self.max_pulse_height]))
            self.create_chan_basic_histograms(my_hist, energy_axis)

        else:  # Loop through each channel
            if channels is not None:
                print("Available Channels in data set :", list(mydata_df.columns))
                for my_chan in channels:
                    print("Graphing channel:", my_chan)
                    if input_type == 'raw':
                        if int(my_chan) in mydata_df['chan'].values:
                            energy_axis, my_hist = self.generate_histo_from_raw(mydata_df, [my_chan])
                        else:
                            print("Could not find data for channel:", my_chan)
                    elif input_type == 'histo':
                        if my_chan in list(mydata_df.columns.astype(int)):
                            energy_axis = np.linspace(1, len(mydata_df[str(my_chan)].values), len(mydata_df[str(my_chan)].values), dtype=int)
                            my_hist = mydata_df[str(my_chan)].values
                        else:
                            print("!! Channel %i was not found found.  Available Channels : %s" % (my_chan, list(mydata_df.columns.astype(int))))
                    if (my_hist is not None) and (energy_axis is not None):
                        self.create_chan_basic_histograms(my_hist, energy_axis)

        return
