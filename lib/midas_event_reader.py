import sys
sys.path.append('/usr/local/packages/midas/python')
#import midas.file_reader
from midas import file_reader
import lib.mdpp16 as mdpp16
import lib.grif16 as grif16
from tqdm import tqdm
from lib.event_handler import event_handler
from multiprocessing import Process, Queue, SimpleQueue, active_children
from time import sleep
from lib.output_handler import output_handler
import importlib
from pprint import pprint


class midas_events:

    def __init__(self, event_length, sort_type, midas_files, output_file, output_format, cores, buffer_size, cal_file, write_events_to_file=False, ppg_data_file=None, ppg_value_range=None, bin_div=1):
        if cal_file:
            self.calibrate = True
        else:
            self.calibrate = False
        self.bin_div = bin_div
        self.my_midas_file = None
        self.write_events_to_file = write_events_to_file
        self.particle_hit_buffer = []
        self.sort_type = sort_type
        self.midas_files = midas_files
        self.output_file = output_file
        self.output_format = output_format
        self.ppg_data_file = ppg_data_file
        self.ppg_value_range = ppg_value_range
        self.checkpoint_EOB_timestamp = 0
        self.entries_read_in_buffer = 0
        self.histo_dict = {}
        self.end_of_tevent = False
        self.MAX_GRIF16_CHANNELS = 16
        # FOR GRIF16 use chan 0-15
        # For MDPP16 use chan 100-115

        # Number of events to buffer before writing out to file.  The larger the number the more memory you need but the faster it will go
        # Setting this to -1 will mean buffer everything before writing, do stuff fast!
        # Setting of 1 means I have no memory please write out each entry as you read it.
        # This won't be exact and won't take into account multiple events in an entry so... whatever.  This is basically
        # just a crude dial if you run into memory problems
        self.MAX_BUFFER_SIZE = buffer_size  # Number of hits to read in before sorting.

        self.MAX_HITS_PER_EVENT = 999  # Maximum number of hits allowed in an EVENT, after that we move on to a new event, this is mostly just a protection against EVENT_LENGTH or
                                       # EVENT_EXTRA_GAP being too long causing a MASSIVE EVENT(it's funny because I only work with gammas)

        # @ 125Mhz every 'tick' is 8ns
        self.EVENT_LENGTH = event_length  # How long an temporal event can be,   we're just using ticks at the moment, maybe someone else wants to do some conversions!?!
        self.EVENT_EXTRA_GAP = 5  # number of ticks to check in addition to EVENT_LENGTH in case one is just hanging out
        self.PROCCESS_NUM_LIMIT = cores  # Max number of processess to spawn for sorting and potentially writing as well
        self.cal_file = cal_file
        # NOTE!! If event timestamps are out of order in the MIDAS file then there is a chance we will miss events at the MAX_BUFFER_SIZE boundary.
        # So it is a good pratctice to set MAX_BUFFER_SIZE large, > 10,000,000
        # But be careful that you do not go over the timestamp theshold where the timestamp is recycled ~ 2x a day at 100Mhz
        self.total_hits = 0
        self.total_pileups = 0
        self.total_over_16k = 0
        self.event_queue = Queue()
        self.bad_packet = 0
        self.current_process_count = 0
        self.processes = []
        self.particle_event_list = []
        self.particle_hits = []
        self.event_queue = Queue()


    def decode_raw_hit_event(self, adc_hit_reader_func, bank_data):
        particle_hit = adc_hit_reader_func(bank_data, self.bin_div)
        if particle_hit != []:
            if self.entries_read_in_buffer == self.MAX_BUFFER_SIZE:
                self.checkpoint_EOB_timestamp = particle_hit[-1]["timestamp"]
            if self.entries_read_in_buffer > self.MAX_BUFFER_SIZE:
                if (particle_hit[-1]["timestamp"] - self.checkpoint_EOB_timestamp) > (self.EVENT_LENGTH + self.EVENT_EXTRA_GAP):
                    self.end_of_tevent = True
            if particle_hit[0]['flags'] > 1:
                self.total_pileups = self.total_pileups + 1
                if particle_hit[0]['pulse_height'] > 65535:
                    self.total_over_16k = self.total_over_16k + 1
                else:
                    self.bad_packet = self.bad_packet + 1
            self.total_hits = self.total_hits + len(particle_hit)
        #    if len(particle_hit) > 1:
        #        print("Len:", particle_hit)
        return particle_hit

    def check_and_write_queue(self, event_queue, particle_event_list, myoutput):
        if self.sort_type == 'event':
            while event_queue.qsize() > 0:
                particle_event_list.extend(event_queue.get())
        if self.sort_type == 'histo':
            from lib.energy_calibration import energy_calibration
            energy_cal = energy_calibration(self.cal_file)
            #particle_event_list = energy_cal.calibrate_histograms(particle_event_list)
            self.histo_dict = particle_event_list
            #pprint(sum(particle_event_list[1]))
        if self.write_events_to_file is True:
            myoutput.write_events(particle_event_list)
        return []

    def run_threaded_sort(self, event_queue, events, myoutput):
        if len(active_children()) < self.PROCCESS_NUM_LIMIT:  # Check if we are maxing out process # limit
            self.checkpoint_EOB_timestamp = 0
            self.end_of_tevent = False
            p = Process(target=events.sort_events, args=(event_queue, self.particle_hits), daemon=False)
            self.processes.append(p)
            p.start()

            self.current_process_count = self.current_process_count + 1
            self.particle_hits = []
            self.entries_read_in_buffer = -1
            print("\nActive childeren : ", len(active_children()))

        if len(active_children()) == self.PROCCESS_NUM_LIMIT:
            while event_queue.qsize() == 0:  # Drain the master queue
                sleep(.1)
            self.particle_event_list = self.check_and_write_queue(event_queue, self.particle_event_list, myoutput)

            for proc in self.processes:
                proc.join()
            self.current_process_count = 0

    def read_midas_files(self):

        # read_midas_files : Loops around an array of files that were passed in order to process multiple subruns
        # via wildcards passed on the CLI
        myoutput = None

        if self.write_events_to_file is True:
            myoutput = output_handler(self.output_file, self.output_format, self.sort_type)

        events = event_handler(self.sort_type, self.EVENT_LENGTH, self.EVENT_EXTRA_GAP, self.MAX_HITS_PER_EVENT, self.calibrate, self.cal_file, ppg_data_file=self.ppg_data_file, ppg_value_range=self.ppg_value_range)
        num = 0  # This is just so we don't delete the MidasFile memory which causes a seg fault with pypy, it's weird, probably Midas memory deallocation error
        my_midas_file = {}
        write_events_to_file_init_value = self.write_events_to_file
        self.write_events_to_file = False  # Temporarily turn this off until on the last file
        total_num_of_files = len(self.midas_files)
        for my_file in self.midas_files:
            num = num + 1
            if num == total_num_of_files:
                self.write_events_to_file = write_events_to_file_init_value
            my_midas_file[num] = file_reader.MidasFile(my_file)
            print(my_file)
            odb_start = my_midas_file[num].get_bor_odb_dump()
            pprint(odb_start.data["Runinfo"])
            self.read_midas_events(my_midas_file[num], myoutput, events)
        return

    def read_midas_events(self, my_midas_file, myoutput, events):
        self.particle_hits = []
        for hit in tqdm(my_midas_file, unit=' Hits'):
            for bank_name, bank in hit.banks.items():
                particle_hit = []
                if bank_name == "MDPP":  # Check if this is an event from the MDPP16
                #    total_events = total_events + 1
                    particle_hit = self.decode_raw_hit_event(mdpp16.read_all_bank_events, bank.data)
                elif bank_name == "GRF4":  # Check if this is an event from the GRIF16
                    particle_hit = self.decode_raw_hit_event(grif16.read_all_bank_events, bank.data)

                if particle_hit:
                    self.particle_hits.extend(particle_hit)

                if (self.entries_read_in_buffer >= self.MAX_BUFFER_SIZE) and self.end_of_tevent is True:
                    if self.sort_type == 'histo':
                        self.end_of_tevent = False
                        # Yes, this histogram stuff is special and I had issues integrating it into the multiprocessor stuff due to weird queue deadlocks due to size of buffer
                        events.sort_events(0, self.particle_hits)
                        self.particle_hits = []
                        self.entries_read_in_buffer = -1

                    elif self.sort_type == 'raw':
                        events.sort_events(0, self.particle_hits)
                        self.particle_hits = self.check_and_write_queue(0, self.particle_hits, myoutput)  # the output of this function is just []
                        self.entries_read_in_buffer = -1
                        self.end_of_tevent = False

                    elif self.sort_type == 'event':
                        self.run_threaded_sort(self.event_queue, events, myoutput)
                    else:
                        print("Sort type not found..")
                        exit(1)

            self.entries_read_in_buffer = self.entries_read_in_buffer + 1

        if (len(self.particle_hits) > 0) or (self.sort_type == 'histos'):  # Check if we should sort and that there are hits to sort..
            print("Processing remaining events in queue...")
            if self.sort_type == 'event':
                events.sort_events(self.event_queue, self.particle_hits)
            elif self.sort_type == 'histo':
                events.sort_events(0, self.particle_hits)
                self.particle_event_list = events.histo_data_dict
            elif self.sort_type == "raw":
                events.sort_events(0, self.particle_hits)
                self.particle_event_list = self.particle_hits
            self.particle_event_list = self.check_and_write_queue(self.event_queue, self.particle_event_list, myoutput)

        print("Total hits", self.total_hits, "Total Pileups:", self.total_pileups, "Over 16bits:", self.total_over_16k, "Bad Packet:", self.bad_packet)
        return 0