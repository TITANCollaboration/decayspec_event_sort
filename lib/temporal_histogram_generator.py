###################################################
# Library to read in temporal histogram data from REDIS and display in real(ish) time
###################################################

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import redis
import json


class temporal_histogram_generator:
    def __init__(self, redis_hostname="localhost", redis_port="6379", redis_queue='mdpp16:queue', channel=0,
                 pulse_height_bin_min=0, pulse_height_bin_max=2048, egun_voltage_min=2000, egun_voltage_max=2700,
                 egun_voltage_step_size=10, heatmap_type="voltage_v_time", max_time_per_cycle_ms=1000, time_per_cycle_step_size_ms=10):
        self.time_bin_count = int(max_time_per_cycle_ms / time_per_cycle_step_size_ms)
        self.tdc_current = 0
        self.current_time_step = 0
        self.current_voltage = 0 # egun_voltage_min
        self.current_voltage_step = 0
        self.fig = plt.figure()
        self.first_run = True
        self.colorbar_axes = None

        if heatmap_type == "voltage_v_time":
            self.egun_voltage_bin_count = int((egun_voltage_max-egun_voltage_min) / egun_voltage_step_size)
            print("Egun Voltage bin count:", self.egun_voltage_bin_count)
            print("Time bin count:", self.time_bin_count)
            self.heatmap_2darray = np.zeros((self.time_bin_count, self.egun_voltage_bin_count), dtype=np.uint32)

        self.redis_hostname = redis_hostname
        self.redis_port = redis_port
        self.redis_queue = redis_queue
        self.channel = channel
        self.pulse_height_bin_min = pulse_height_bin_min
        self.pulse_height_bin_max = pulse_height_bin_max
        self.egun_voltage_max = egun_voltage_max
        self.egun_voltage_min = egun_voltage_min
        self.heatmap_type = heatmap_type
        self.max_time_per_cycle_ms = max_time_per_cycle_ms
        self.egun_voltage_step_size = egun_voltage_max
        self.time_per_cycle_step_size_ms = time_per_cycle_step_size_ms

        try:
            self.queue_conn = redis.Redis(host=self.redis_hostname, port=self.redis_port)
        except:
            print("Failed to connect to REDIS server")
            exit(0)
        return

    def get_queue_length(self):
        queue_length = self.queue_conn.llen(self.redis_queue)
        return queue_length

    def get_hist_entry_from_queue(self):
        json_from_queue = self.queue_conn.lpop(self.redis_queue)
        myval = json.loads(json_from_queue)  # Decode the JSON contained in the queue entry into list
        return myval

    def drain_queue(self):
        current_queue_length = self.get_queue_length()
        print("Current queue length:", current_queue_length )
#        if self.get_queue_length() != 0:
#            current_queue_length = 1 # self.get_queue_length(()  # Set this back after testing...
#        else:
#            current_queue_length = 0  # testing stuff
        queue_contents = []
        for queue_entry_index in range(0, current_queue_length):
            queue_contents.append(self.get_hist_entry_from_queue())
        return queue_contents


    def process_voltage_vs_time_raw_data(self, frame_value):
        # Get all available data from the queue (redis) then convert it to data that can be
        # applied to the 2d array for creating the heatmap
        queue_contents = self.drain_queue()  # Get all available entries from queue
        for queue_entry in queue_contents:
            #print("Time Diff: ", queue_entry['time_diff'])
            if (queue_entry['egun_voltage'] != self.current_voltage):  # Check if we've moved to a new voltage
                self.current_voltage = queue_entry['egun_voltage']
                self.current_time_step = 0
            if queue_entry['last_tdc_time'] < self.tdc_current:  # Check if we reset the TDC on the DAQ for new time run
                self.current_time_step = 0
            self.tdc_current = queue_entry['last_tdc_time']

                # self.tdc_current = queue_entry()
            sum_hits_in_region = np.sum(np.array(queue_entry['hist'][self.channel])[self.pulse_height_bin_min:self.pulse_height_bin_max])
             # Sum the hist entries in the region of interest to get counts in that region
            #print(sum_hits_in_region)
            self.current_voltage_step = int((self.current_voltage - self.egun_voltage_min) / self.egun_voltage_step_size)
            self.heatmap_2darray[self.current_time_step][self.current_voltage_step] = \
                self.heatmap_2darray[self.current_time_step][self.current_voltage_step] + sum_hits_in_region  # row, column

            if self.current_time_step < (self.max_time_per_cycle_ms/self.time_per_cycle_step_size_ms)-1:  # For testing we need this... not sure if we'll need it in the future
                self.current_time_step = self.current_time_step + 1
            else:
                self.current_time_step = 0
        self.voltage_vs_time_heatmap()
        return

    def display_heatmap(self, extent):
        if self.first_run is True:
            # can also put in vmin and vmax to imshow to auto scale the coloring..
            self.im = plt.imshow(self.heatmap_2darray, cmap='viridis', extent=extent, aspect='auto', origin='lower', vmin=0, vmax=40)
            #self.colorbar = plt.colorbar(cax=self.colorbar_axes)
            self.first_run = False

        else:
            self.im.set_array(self.heatmap_2darray)
            # Uncomment the imshow line here to have it update the full image every time including the colors
            #self.im = plt.imshow(self.heatmap_2darray, cmap='viridis', extent=extent, aspect='auto', origin='lower')

            #norm = plt.Normalize(vmin=0, vmax=500)

            self.colorbar = plt.colorbar(self.im, cax=self.colorbar_axes)
            _, self.colorbar_axes = plt.gcf().get_axes()
            #plt.colorbar(self.im)
        return

    def voltage_vs_time_heatmap(self):
        extent = self.egun_voltage_min, self.egun_voltage_max, 0, self.max_time_per_cycle_ms  # (left, right, bottom, top)
        self.display_heatmap(extent)
        return

    def online_voltage_vs_time_heatmap(self):
        self.process_voltage_vs_time_raw_data(0)
        #plt.colorbar()
        ani = animation.FuncAnimation(self.fig, self.process_voltage_vs_time_raw_data, interval=1000)
        plt.show()

    def pulse_height_vs_time_heatmap(self):
        return


#  channel, TDC, unix_TS, histogram
