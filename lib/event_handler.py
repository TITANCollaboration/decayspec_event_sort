import operator
from lib.energy_calibration import energy_calibration
import numpy as np
import pandas as pd
from lib.input_handler import input_handler
from pprint import pprint

class event_handler:
    def __init__(self, sort_type, event_length, event_extra_gap, max_hits_per_event, calibrate, cal_file, ppg_data_file=None, ppg_value_range=None, max_pulse_height=2**16, min_bin=0, max_bin=301.13627937, num_of_bins=2**16):
        self.sort_type = sort_type
        self.event_length = event_length
        self.event_extra_gap = event_extra_gap
        self.max_hits_per_event = max_hits_per_event
        self.calibrate = calibrate
        self.ppg_data_file = ppg_data_file
        self.ppg_value_range = ppg_value_range

        self.min_bin = min_bin
        self.max_bin = max_bin
        self.num_of_bins = num_of_bins
        self.total_count = 0
        self.max_pulse_height = max_pulse_height
        if sort_type == "histo":
            self.histo_data_dict = {}
        if self.calibrate:
            self.energy_calibration = energy_calibration(cal_file)
            self.energy_calibration.read_in_calibration_file()
        # events = event_handler(self.sort_type, event_queue, self.EVENT_LENGTH, self.EVENT_EXTRA_GAP, self.MAX_HITS_PER_EVENT)
        if self.ppg_data_file is not None:
            self.missed_hits_later = 0
            self.missed_hits_begin = 0
            self.first_change_timestamp = {}
            self.first_change_timestamp['mdpp16_timestamp'] = None
            self.first_change_timestamp['grif16_timestamp'] = None
            print("Reading in PPG Data file:", self.ppg_data_file)
            csv_reader_object = input_handler(self.ppg_data_file)
            ppg_data_list_tmp = csv_reader_object.read_in_data(separator=',')
            self.ppg_data_list = ppg_data_list_tmp.to_dict('records')
            ppg_data_list_tmp = 0  # Just cleaning up the memory from the pandas df
            for ppg_entry in self.ppg_data_list:  # Find first usable entry
                if ppg_entry['ppg_action'] == "start":  # Make sure we are strting with a real start entry..
                    self.first_change_timestamp['mdpp16_timestamp'] = ppg_entry['mdpp16_timestamp']  # Get the first timestamp listed in the ppg data file for each ADC
                    self.first_change_timestamp['grif16_timestamp'] = ppg_entry['grif16_timestamp']
                    break

    def adc_name_from_channel(self, channel):
        adc_name = ""
        if channel < 16:
            adc_name = "grif16"
        elif channel >= 100:
            adc_name = "mdpp16"
        return adc_name

    def time_correlate_ppg_data(self, particle_hit_list):
        # time_correlate_ppg_data: The idea here is that it will look to see if the timestamp corresponds to one of the ranges in the
        #                          ppg time correlation file and if so it'll add that bit of data, this is mainly going to be used for
        #                          EBIT DT5 voltage values
        # Something like this but completely different:
        # ppg_data_list

        current_ppg_data_time_index = 0

        for hit_event in particle_hit_list:
            ppg_match_found = False
            ppg_adc_timestamp_column = self.adc_name_from_channel(hit_event['chan']) + "_timestamp"  # determine which dict entry to use

            # we might have collected data before the ppg started sending us data so set those ppg_value's to -1
            if hit_event['timestamp'] < self.first_change_timestamp[ppg_adc_timestamp_column]:
                hit_event['ppg_value'] = -1
                self.missed_hits_begin = self.missed_hits_begin + 1
                continue

            for my_ppg_index in range(current_ppg_data_time_index, len(self.ppg_data_list)):
                # Find first pairing, if its not a pairing then continue to incriment
                if (self.ppg_data_list[my_ppg_index]['ppg_action'] != 'start') or (self.ppg_data_list[my_ppg_index+1]['ppg_action'] != 'end'):
                    continue
                # if both conditions met we have a ppg value
                elif (hit_event['timestamp'] >= self.ppg_data_list[my_ppg_index][ppg_adc_timestamp_column]) and \
                     (hit_event['timestamp'] <= self.ppg_data_list[my_ppg_index+1][ppg_adc_timestamp_column]):

                    hit_event['ppg_value'] = self.ppg_data_list[my_ppg_index]['ppg_value']
                #    print("Hit TS:", hit_event['timestamp'], "PPG Start TS:", self.ppg_data_list[my_ppg_index][ppg_adc_timestamp_column], "PPG END TS:", self.ppg_data_list[my_ppg_index+1][ppg_adc_timestamp_column], "PPG Value:", self.ppg_data_list[my_ppg_index]['ppg_value'])
                    ppg_match_found = True
                    current_ppg_data_time_index = my_ppg_index  # Set it so that we start looking at this time next time, may take this out if we get a lot of OfO events?
                    break
            if ppg_match_found is not True:
                hit_event['ppg_value'] = -1
                # print("! MISSED Hit TS:", hit_event['timestamp'])
                self.missed_hits_later = self.missed_hits_later + 1
        return

    def sort_events(self, event_queue, particle_hit_list):
        if self.sort_type == 'event':
            self.sort_event_based_thread_safe(event_queue, particle_hit_list)
        elif self.sort_type == 'raw':
            self.raw_sorter(event_queue, particle_hit_list)
        elif self.sort_type == 'histo':
            self.histo_sorter(particle_hit_list)
        else:
            print("Could not finding an appropriate sorter.  The specified one was:", self.sort_type)
        return

    def histo_sorter(self, particle_hit_list):
        # Testing if it's better to make use of np.histogram for better bining
        ph_list_buffer = {}
        if self.calibrate:
            particle_hit_list = self.energy_calibration.calibrate_list(particle_hit_list)
        if self.ppg_data_file is not None:
            self.time_correlate_ppg_data(particle_hit_list)
        for particle_hit in particle_hit_list:
            if particle_hit['chan'] not in ph_list_buffer.keys():
                ph_list_buffer.update({particle_hit['chan']: []})
                #self.histo_data_dict.update({particle_hit['chan']: []})
            if particle_hit['pulse_height'] < self.max_pulse_height:
                if (self.ppg_value_range is not None):
                    if (particle_hit['ppg_value'] >= self.ppg_value_range[0]) and (particle_hit['ppg_value'] <= self.ppg_value_range[1]):
                        print("WARNING! This has not been extensively tested!")
                        ph_list_buffer[particle_hit['chan']].append(particle_hit['pulse_height'])
                else:
                    ph_list_buffer[particle_hit['chan']].append(particle_hit['pulse_height'])
        # Now do np.histogram on each channel and sum the histograms I think
        for buffer_chan_key in ph_list_buffer.keys():
            ph_list_buffer[buffer_chan_key].sort()
            #print("LArgest value:", ph_list_buffer[buffer_chan_key][-1])
            if buffer_chan_key not in self.histo_data_dict.keys():
                self.histo_data_dict[buffer_chan_key] = np.zeros(1) # Create an array of a single 0 if no data exists yet for the channel
        #    print("We get here..", ph_list_buffer[buffer_chan_key]
            self.histo_data_dict[buffer_chan_key] = np.histogram(ph_list_buffer[buffer_chan_key],
                                                                 bins=self.num_of_bins,
                                                                 range=(self.min_bin, self.max_bin))[0] + self.histo_data_dict[buffer_chan_key]
        #print(self.histo_data_dict[buffer_chan_key])
        return

    """def histo_sorter(self, particle_hit_list):
        # This one is weird and has issues running mutliprocessor due to the size of the dicts + arrays
        if self.calibrate:
            # print("Before:", len(particle_hit_list))
            particle_hit_list = self.energy_calibration.calibrate_list(particle_hit_list)
            # print("After:", len(particle_hit_list))
        if self.ppg_data_file is not None:
            self.time_correlate_ppg_data(particle_hit_list)
        for particle_hit in particle_hit_list:
            if particle_hit['chan'] not in self.histo_data_dict.keys():
                self.histo_data_dict.update({particle_hit['chan']: np.zeros(self.max_pulse_height, dtype=int)})
            if particle_hit['pulse_height'] < self.max_pulse_height:
                if (self.ppg_value_range is not None):
                    if (particle_hit['ppg_value'] >= self.ppg_value_range[0]) and (particle_hit['ppg_value'] <= self.ppg_value_range[1]):
                        self.histo_data_dict[particle_hit['chan']][particle_hit['pulse_height']] = self.histo_data_dict[particle_hit['chan']][particle_hit['pulse_height']] + 1
                else:
                    self.histo_data_dict[particle_hit['chan']][particle_hit['pulse_height']] = self.histo_data_dict[particle_hit['chan']][particle_hit['pulse_height']] + 1
        return 0"""

    def raw_sorter(self, event_queue, particle_hit_list):
        # This is mostly a dummy function
        if self.calibrate:
            particle_hit_list = self.energy_calibration.calibrate_list(particle_hit_list)
        if self.ppg_data_file is not None:
            self.time_correlate_ppg_data(particle_hit_list)
            print("Missed beginning:", self.missed_hits_begin, "Missed Later:", self.missed_hits_later)
        return

    def sort_event_based_thread_safe(self, event_queue, particle_hit_list):
        print("Performing Event Based Sorting...")
        particle_event_list = []
        particle_hit_list = sorted(particle_hit_list, key=operator.itemgetter('timestamp'))
        for particle_hit in particle_hit_list:
            if self.calibrate:
                particle_hit['pulse_height'] = self.energy_calibration.calibrate_hit(particle_hit)

            if not particle_event_list:
                event_hit_count = 1
                particle_event_list.append({'pulse_height': [particle_hit['pulse_height']],
                                            'chan': [particle_hit['chan']],
                                            'timestamp': particle_hit['timestamp'],
                                            'hit_count': 1})
                """ check if the timestamp is in the range of a temporal event and that we aren't seeing the
                event from the same detector, this might get weird and maybe we should care as it could have
                an impact on events after it.. """
            elif ((particle_hit['timestamp'] - particle_event_list[-1]['timestamp']) < (self.event_length + self.event_extra_gap)):  # and (particle_hit['chan'] not in particle_event_list[-1]['chan']):
                event_hit_count = event_hit_count + 1
                particle_event_list[-1]['pulse_height'].append(particle_hit['pulse_height'])
                particle_event_list[-1]['chan'].append(particle_hit['chan'])
                particle_event_list[-1]['hit_count'] = event_hit_count
            else:
                event_hit_count = 1
                particle_event_list.append({'pulse_height': [particle_hit['pulse_height']],
                                            'chan': [particle_hit['chan']],
                                            'timestamp': particle_hit['timestamp'],
                                            'hit_count': event_hit_count})
        event_queue.put(particle_event_list)
        return
