import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import sqrt, ceil
from scipy.ndimage import gaussian_filter1d
from lib.input_handler import input_handler

#from lib.output_handler import output_handler


class hist_gen:
    def __init__(self, input_filename, save_all, overlay_files, max_pulse_height, min_pulse_height, bin_number, title, xlabel, ylabel, energy_labels, y_axis_min, y_axis_max, zoom, zoom_xmin, zoom_xmax):
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
        self.ylog_zoom = True
        self.title_font_size = 20
        self.axis_font_size = self.title_font_size
        self.tick_font_size = 20
        self.label_font_size = 12
        self.y_axis_min = y_axis_min
        self.y_axis_max = y_axis_max
        self.smoothing = False
        self.input_filename = input_filename
        self.save_all = save_all
        self.overlay_files = overlay_files
        self.histo_multiplier = 1
        self.overlay_multiplier = 1
        self.y_axis_sub_min = 1e3
        self.y_axis_sub_max = 3e4

    def gaussian_smoothing(self, initdata, sigma=1):
        #p = np.poly1d([0.0000007, 0.00183744, 1.1])  # Griffin smearing
        newdata = gaussian_filter1d(initdata, sigma=sigma)
        return newdata

    def label_peaks(self, axes, my_hist, ymax, label_xmin, label_xmax, height=0.5):
        for my_label in self.energy_labels:
            if (int(my_label) < label_xmax) and (int(my_label) > label_xmin):
                axes.axvline(x=int(my_label), color='red', linestyle='--', ymin=0, ymax=0.75, lw=1)
                axes.text(int(my_label), 20000, str(my_label), rotation=45, fontsize=self.label_font_size)
        return 0

    def graph_with_overlays(self, my_axis, energy_axis, my_hist, zoomed):
        self.overlay_multipliers = [1, 100, 1000, 10000]  # , 100]
        #background_data_actual = input_handler('../8pi_bg_1hr.hist')
        #background_data_df = background_data_actual.read_in_data()
        #self.overlay_multipliers = [100, 10, 2, 1]
        if self.overlay_files is not None:
            for my_overlay_file in self.overlay_files:

                for my_multiplier in self.overlay_multipliers:
                    myinput = input_handler(my_overlay_file)
                    my_overlay_df = myinput.read_in_data()
                                    #my_overlay_df = np.concatenate(([0], my_overlay_df))
                    #my_overlay_df = my_overlay_df * self.overlay_multiplier#* self.histo_multiplier  # Just turning 1 day into 8..
                    if zoomed is True:
                        my_overlay_df = (my_overlay_df[self.zoom_xmin-1:self.zoom_xmax-1] * my_multiplier)
                    else:
                        my_overlay_df = my_overlay_df * my_multiplier
                        #print(my_overlay_df)
                    length_diff = len(my_hist) - len(my_overlay_df['99'])
                    my_zeros = np.zeros(length_diff)
                    my_overlay_df = np.concatenate((my_overlay_df['99'], my_zeros))

                    length_diff = len(my_hist) - len(my_overlay_df)

                    combined_hist = 0
                    combined_hist = my_hist + my_overlay_df
                    if self.smoothing is True:
                        combined_hist = self.gaussian_smoothing(combined_hist)
                    my_label = "NEEC x" + str(my_multiplier)
                    linewidth = 1
                    if zoomed is True:
                        linewidth = 2
                    my_axis.step(energy_axis, combined_hist, where='mid', label=my_label, linewidth=linewidth)
        else:
            if self.smoothing is True:
                my_hist = self.gaussian_smoothing(my_hist)
            #combo_hist = background_data_df['99'] + my_hist
            #my_axis.step(energy_axis, my_hist, where='mid')
            my_axis.step(energy_axis, my_hist, where='mid')


    def create_chan_basic_histograms(self, my_hist, energy_axis):
        my_hist = my_hist * self.histo_multiplier  # turn 1 day into 8
        ymax = my_hist.max()
        self.fig, self.axes = plt.subplots(num=None, figsize=(16, 12), dpi=96, facecolor='w', edgecolor='k')  # sharex=True, sharey=True,
        self.axes.tick_params(labelsize=self.tick_font_size)
        if self.ylog is True:
            plt.yscale("log")

        self.graph_with_overlays(self.axes, energy_axis, my_hist, False)

        if (self.energy_labels is not None):
            self.label_peaks( self.axes, my_hist, ymax, self.min_pulse_height, self.max_pulse_height, height=0.03)

        plt.title(self.title, fontsize=self.title_font_size)
        plt.xlabel(self.xlabel, fontsize=self.axis_font_size)
        plt.ylabel(self.ylabel, fontsize=self.axis_font_size)

        if self.zoom is True:
            sub_axes = plt.axes([.5, .5, .37, .35])  # Location of zoomed section in relation to main graph ;  [left, bottom, width, height]
            ymax_sub = energy_axis[self.zoom_xmin:self.zoom_xmax].max()

            self.graph_with_overlays(sub_axes, energy_axis[self.zoom_xmin:self.zoom_xmax], my_hist[self.zoom_xmin:self.zoom_xmax], True)

            sub_axes.set_xlim([self.zoom_xmin, self.zoom_xmax])  # Set x-axis for insert graph
            sub_axes.set_ylim([self.y_axis_sub_min, self.y_axis_sub_max])

            sub_axes.tick_params(labelsize=self.tick_font_size)

            if (self.energy_labels is not None) and (self.zoom_label is True):
                self.label_peaks(sub_axes, my_hist, ymax_sub, self.zoom_xmin, self.zoom_xmax)
            if self.ylog_zoom is True:
                plt.yscale("log")
        self.axes.set_xlim([self.min_pulse_height, self.max_pulse_height])
        if self.y_axis_max is None:
            self.y_axis_max = my_hist[self.min_pulse_height:self.max_pulse_height].max() * 1.2
        self.axes.set_ylim([self.y_axis_min, self.y_axis_max])
        self.axes.ticklabel_format(style='plain')
        plt.legend(title='Parameters:', fontsize=self.label_font_size)
        myfilename = self.input_filename + '.png'
        plt.savefig(myfilename, dpi=96)
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
        if self.save_all is True:
#            myoutput = output_handler(self.input_filename + '.hist', 'histo', 'histo')
            print("Writing file:", self.input_filename + '.hist')
            mydata_df =  pd.DataFrame(data={'99': my_hist})
            mydata_df.to_csv(self.input_filename + '.hist', sep='|', header=True, index=False, chunksize=50000, mode='w', encoding='utf-8')

#            myoutput.write_events(my_hist)
            #print("fix me")
        return energy_axis, my_hist

    def generate_histo_from_histo(self, mydata_df, channels):
        for my_chan in channels:
            print("Summing channel:", my_chan)
            if my_chan != 'summed_hist':  # Make sure we don't sum out summing column.. yup..
                mydata_df['summed_hist'] = mydata_df[str(my_chan)] + mydata_df['summed_hist']
        #energy_axis = np.linspace(1, self.max_pulse_height, len(mydata_df['summed_hist'].values), dtype=int)
        energy_axis = np.linspace(1, len(mydata_df['summed_hist'].values) + 1, len(mydata_df['summed_hist'].values) + 1, dtype=int)
        my_hist = np.concatenate(([0], mydata_df['summed_hist']))
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
                print("Available Channels in data set :", list(mydata_df.columns))
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
                            energy_axis = np.linspace(1, len(mydata_df[str(my_chan)].values), len(mydata_df[str(my_chan)].values), dtype=int)
                            my_hist = mydata_df[str(my_chan)].values
                    if (my_hist is not None) and (energy_axis is not None):
                        self.create_chan_basic_histograms(my_hist, energy_axis)

        return
