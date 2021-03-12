import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import sqrt, ceil
from scipy.ndimage import gaussian_filter1d


class hist_gen:
    def __init__(self, max_pulse_height, min_pulse_height, bin_number, title, xlabel, ylabel, energy_labels, y_axis_min, y_axis_max, zoom, zoom_xmin, zoom_xmax):
        self.flags = 1
        self.min_pulse_height = min_pulse_height
        self.max_pulse_height = max_pulse_height
        self.bins = bin_number
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.energy_labels = energy_labels
        self.zoom_xmin = zoom_xmin
        self.zoom_xmax = zoom_xmax
        self.zoom = zoom
        self.zoom_label = True
        self.ylog = False
        self.ylog_zoom = False
        self.title_font_size = 20
        self.axis_font_size = self.title_font_size
        self.tick_font_size = 20
        self.y_axis_min = y_axis_min
        self.y_axis_max = y_axis_max
        self.smoothing = False

    def gaussian_smoothing(self, initdata):
        newdata = gaussian_filter1d(initdata, sigma=2)
        return newdata

    def label_peaks(self, ymax, label_xmin, label_xmax, height=0.5):
        for my_label in self.energy_labels:
            if (int(my_label) < label_xmax) and (int(my_label) > label_xmin):
                plt.axvline(x=int(my_label), color='red', linestyle='--', ymin=0, ymax=0.75, lw=1)
                plt.text(int(my_label), ymax * height, str(my_label), rotation=45)
        return 0

    def create_chan_basic_histograms(self, my_hist, energy_axis):
        ymax = my_hist.max()
        self.fig, self.axes = plt.subplots(num=None, figsize=(16, 12), dpi=96, facecolor='w', edgecolor='k')  # sharex=True, sharey=True,
        self.axes.tick_params(labelsize=self.tick_font_size)
        if self.ylog is True:
            plt.yscale("log")
        if self.smoothing is True:
            my_hist = self.gaussian_smoothing(my_hist)
        print(my_hist)
        self.axes.step(energy_axis, my_hist, where='mid')
        if (self.energy_labels is not None):
            self.label_peaks(ymax, self.min_pulse_height, self.max_pulse_height, height=0.03)

        plt.title(self.title, fontsize=self.title_font_size)
        plt.xlabel(self.xlabel, fontsize=self.axis_font_size)
        plt.ylabel(self.ylabel, fontsize=self.axis_font_size)

        if self.zoom is True:
            sub_axes = plt.axes([.5, .5, .37, .35])  # Location of zoomed section in relation to main graph ;  [left, bottom, width, height]
            ymax_sub = energy_axis[self.zoom_xmin:self.zoom_xmax].max()
            print(energy_axis[self.zoom_xmin:self.zoom_xmax])
            print(my_hist[self.zoom_xmin:self.zoom_xmax])
            sub_axes.step(energy_axis[self.zoom_xmin:self.zoom_xmax], my_hist[self.zoom_xmin:self.zoom_xmax], where='mid')  # Draw insert graph
            sub_axes.set_xlim([self.zoom_xmin, self.zoom_xmax])  # Set x-axis for insert graph
            sub_axes.tick_params(labelsize=self.tick_font_size)

            if (self.energy_labels is not None) and (self.zoom_label is True):
                self.label_peaks(ymax_sub, self.zoom_xmin, self.zoom_xmax)
            if self.ylog_zoom is True:
                plt.yscale("linear")
        self.axes.set_xlim([self.min_pulse_height, self.max_pulse_height])
        if self.y_axis_max is None:
            print("still working on this, please use --ymax..")
        #self.axes.set_ylim([self.y_axis_min, self.y_axis_max])
        plt.show()
        return 0

    def determine_input_type(self, columns):
        if 'pulse_height' in columns:
            return 'raw'
        else:
            return 'histo'

    def generate_histo_from_raw(self, mydata_df, channels):
        energy_axis = None
        my_hist = None
        pulse_height = mydata_df[mydata_df['chan'].isin(channels) &
                                 (mydata_df['flags'] == self.flags) &
                                 (mydata_df['pulse_height'] >= self.min_pulse_height) &
                                 (mydata_df['pulse_height'] <= self.max_pulse_height)]['pulse_height'].to_numpy()
        if len(pulse_height) > 0:
            energy_axis = np.linspace(1, pulse_height.max(), pulse_height.max(), dtype=int)
            my_hist = np.histogram(pulse_height, bins=energy_axis)[0]
            my_hist = np.append(my_hist, [0])  # Sizes kept coming out slightly off so.. fixed it?
        else:
            print("No data found in channel:", channels)
        return energy_axis, my_hist

    def generate_histo_from_histo(self, mydata_df, channels):
        for my_chan in channels:
            print("Summing channel:", my_chan)
            if my_chan != 'summed_hist':  # Make sure we don't sum out summing column.. yup..
                mydata_df['summed_hist'] = mydata_df[str(my_chan)] + mydata_df['summed_hist']
        energy_axis = np.linspace(1, self.max_pulse_height, len(mydata_df['summed_hist'].values), dtype=int)
        my_hist = mydata_df['summed_hist']
        return energy_axis, my_hist

    def grapher(self, mydata_df, channels, sum_all=True):
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
            self.create_chan_basic_histograms(my_hist, energy_axis)

        else:  # Loop through each channel
            if channels is not None:
                #print("Available Channels in data set :", list(mydata_df.columns))
                for my_chan in channels:
                    print("Graphing channel:", my_chan)
                    if input_type == 'raw':
                        if int(my_chan) in mydata_df['chan'].values:
                            energy_axis, my_hist = self.generate_histo_from_raw(mydata_df, [my_chan])
                        else:
                            print("Could not find data for channel:", my_chan)
                    elif input_type == 'histo':
                        print("Histo!")
                        if my_chan in list(mydata_df.columns.astype(int)):
                            print(mydata_df.columns)
                            print("Values?", len(mydata_df[str(my_chan)].values))

                            energy_axis = np.linspace(1, len(mydata_df[str(my_chan)].values), len(mydata_df[str(my_chan)].values), dtype=int)
                            my_hist = mydata_df[str(my_chan)].values
                            print("My energy Axis:", energy_axis)
                    if (my_hist is not None) and (energy_axis is not None):
                        self.create_chan_basic_histograms(my_hist, energy_axis)

        return
