import pandas as pd
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

    def create_chan_basic_histograms_from_df(self, mydata_df, channels):
        if channels is None:
            channels = mydata_df.chan.unique()
        self.fig, self.axes = plt.subplots(num=None, figsize=(16, 12), dpi=80, facecolor='w', edgecolor='k') #sharex=True, sharey=True,
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
    def plot_hitogram_from_df_raw(self, mydata_df):
        fig, axs = plt.subplots(1, sharex=True, sharey=True)
        nbins_array_weird = np.linspace(1, max_pulse_height, nbins-1)
        axs.step(nbins_array_weird, mydict['0'])  # Generate line graph that will overlay bar graph
        plt.show()

        return 0
