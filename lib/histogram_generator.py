import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import sqrt, ceil


class hist_gen:
    def __init__(self, max_pulse_height, min_pulse_height, bin_number, title, xlabel, ylabel, energy_labels, y_axis_min, y_axis_max):
        #self.chan = chan

        self.flags = 1
        self.min_pulse_height = min_pulse_height
        self.max_pulse_height = max_pulse_height
        self.bins = bin_number
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.energy_labels = energy_labels
        self.zoom_xmin = 1140
        self.zoom_xmax = 1180
        self.zoom = True
        self.zoom_label = True
        self.ylog = True
        self.ylog_zoom = False
        self.title_font_size = 20
        self.axis_font_size = self.title_font_size
        self.tick_font_size = 20
        self.y_axis_min = y_axis_min
        self.y_axis_max = y_axis_max

    def label_peaks(self, ymax, label_xmin, label_xmax, height=0.5):
        for my_label in self.energy_labels:
            if (int(my_label) < label_xmax) and (int(my_label) > label_xmin):
                plt.axvline(x=int(my_label), color='red', linestyle='--', ymin=0, ymax=0.75, lw=1)
                plt.text(int(my_label), ymax * height, str(my_label), rotation=45)
        return 0

    def create_chan_basic_histograms_from_raw_df(self, mydata_df, channels):
        auto_title = False

        if channels is None:
            channels = mydata_df.chan.unique()
        pulse_height = mydata_df[mydata_df['chan'].isin(channels) &
                                 (mydata_df['flags'] == self.flags) &
                                 (mydata_df['pulse_height'] > self.min_pulse_height) &
                                 (mydata_df['pulse_height'] < self.max_pulse_height)]['pulse_height'].to_numpy()

        energy_axis = np.linspace(1, pulse_height.max(), pulse_height.max(), dtype=int)
        my_hist = np.histogram(pulse_height, bins=energy_axis)[0]
        my_hist = np.append(my_hist, [0])  # Sizes kept coming out slightly off so fixed it?
        ymax = my_hist.max()
        self.fig, self.axes = plt.subplots(num=None, figsize=(16, 12), dpi=96, facecolor='w', edgecolor='k')  # sharex=True, sharey=True,
        self.axes.tick_params(labelsize=self.tick_font_size)
        if self.ylog is True:
            plt.yscale("log")
        self.axes.step(energy_axis, my_hist, where='mid')
        if (self.energy_labels is not None):
            self.label_peaks(ymax, self.min_pulse_height, self.max_pulse_height, height=0.03)

        if (auto_title is True) and (len(channels) == 1):
            plt.title(self.title + ' chan: ' + str(channels[0]))
        else:
            plt.title(self.title, fontsize=self.title_font_size)

        plt.xlabel(self.xlabel, fontsize=self.axis_font_size)
        plt.ylabel(self.ylabel, fontsize=self.axis_font_size)

        if self.zoom is True:
            sub_axes = plt.axes([.5, .5, .37, .35])  # Location of zoomed section in relation to main graph ;  [left, bottom, width, height]
            ymax_sub = energy_axis[self.zoom_xmin:self.zoom_xmax].max()
            sub_axes.step(energy_axis[self.zoom_xmin:self.zoom_xmax], my_hist[self.zoom_xmin:self.zoom_xmax], where='mid')  # Draw insert graph
            sub_axes.set_xlim([self.zoom_xmin, self.zoom_xmax])  # Set x-axis for insert graph
            sub_axes.tick_params(labelsize=self.tick_font_size)

            if (self.energy_labels is not None) and (self.zoom_label is True):
                self.label_peaks(ymax_sub, self.zoom_xmin, self.zoom_xmax)
            if self.ylog_zoom is True:
                plt.yscale("linear")
        self.axes.set_xlim([self.min_pulse_height, self.max_pulse_height])

        self.axes.set_ylim([2e2, 1e6])
        plt.show()
        return 0

    # Generic plotter of existing histogram data.  Pass it a histogram in a single dataframe and it'll do it's best.
    # This is mostly used when going from GEANT4's root histogram output to a dataframe to a plot of said histogram..
    # This has been useful suprissingly often...
    def create_chan_basic_histograms_from_histo_df(self, mydata_df, channels):
        print(mydata_df.columns)
        try:
            print("Available Channels in data set :", list(mydata_df.columns.astype(int)))
            if channels[0] not in list(mydata_df.columns.astype(int)):
                print("Could not find channel:", channels[0], "in dataset.  Please use --chan #")
                exit(1)
        except:
            print("Probably a root file.")
        fig, axs = plt.subplots(len(channels), squeeze=False, sharex=True, sharey=True)
        chan_index = 0
        for my_chan in channels:
            nbins_array_weird = np.linspace(1, self.max_pulse_height, len(mydata_df[str(my_chan)].values))
            axs[chan_index][0].step(nbins_array_weird, mydata_df[str(my_chan)].values)  # Generate line graph that will overlay bar graph
            chan_index = chan_index + 1
        if len(channels) == 1:
            plt.title(self.title + ' chan: ' + str(channels[0]))
        if self.energy_labels is not None:
            self.label_peaks()
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        plt.show()

        return 0
