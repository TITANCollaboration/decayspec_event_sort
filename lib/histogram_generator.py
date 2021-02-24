import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import sqrt, ceil


class hist_gen:
    def __init__(self, max_pulse_height, min_pulse_height, bin_number, title, xlabel, ylabel):
        #self.chan = chan

        self.flags = 1
        self.min_pulse_height = min_pulse_height
        self.max_pulse_height = max_pulse_height
        self.bins = bin_number
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel

    def create_chan_basic_histograms_from_raw_df(self, mydata_df, channels):
        if channels is None:
            channels = mydata_df.chan.unique()
        self.fig, self.axes = plt.subplots(num=None, figsize=(16, 12), dpi=96, facecolor='w', edgecolor='k') #sharex=True, sharey=True,
        mydata_df[mydata_df['chan'].isin(channels) &
                  (mydata_df['flags'] == self.flags) &
                  (mydata_df['pulse_height'] > self.min_pulse_height) &
                  (mydata_df['pulse_height'] < self.max_pulse_height)].hist(column='pulse_height',
                                                                            by='chan',
                                                                            figsize=(20, 20),
                                                                            bins=self.bins,
                                                                            ax=self.axes,
                                                                            histtype='step')
        if len(channels) == 1:
            plt.title(self.title + ' chan: ' + str(channels[0]))
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        plt.show()
        return 0

    # Generic plotter of existing histogram data.  Pass it a histogram in a single dataframe and it'll do it's best.
    # This is mostly used when going from GEANT4's root histogram output to a dataframe to a plot of said histogram..
    # This has been useful suprissingly often...
    def create_chan_basic_histograms_from_histo_df(self, mydata_df, channels):
#        print(mydata_df)
        #print(channels)
        fig, axs = plt.subplots(len(channels), squeeze=False, sharex=True, sharey=True)
        chan_index = 0
        for my_chan in channels:
            nbins_array_weird = np.linspace(1, self.max_pulse_height, len(mydata_df[str(my_chan)].values))
            axs[chan_index][0].step(nbins_array_weird, mydata_df[str(my_chan)].values)  # Generate line graph that will overlay bar graph
            chan_index = chan_index + 1
        if len(channels) == 1:
            plt.title(self.title + ' chan: ' + str(channels[0]))
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        plt.show()

        return 0
