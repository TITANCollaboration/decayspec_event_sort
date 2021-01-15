import sys
sys.path.append('/usr/local/packages/midas/python')
import midas.file_reader
import lib.mdpp16 as mdpp16
import lib.grif16 as grif16
from tqdm import tqdm
from lib.event_handler import event_handler
from multiprocessing import Process, Queue, SimpleQueue, active_children
from time import sleep
from lib.output_handler import output_handler


class midas_events:

    def __init__(self, event_length, sort_type, midas_files, output_file, output_format, cores, buffer_size, cal_file, write_events_to_file):
        if cal_file:
            self.calibrate = True
        else:
            self.calibrate = False

        self.write_events_to_file = write_events_to_file
        self.particle_hit_buffer = []
        self.sort_type = sort_type
        self.midas_files = midas_files
        self.output_file = output_file
        self.output_format = output_format
        self.checkpoint_EOB_timestamp = 0
        self.entries_read_in_buffer = 0

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

    def decode_raw_hit_event(self, adc_hit_reader_func, bank_data):
        particle_hit = adc_hit_reader_func(bank_data)
        if particle_hit:
            if self.entries_read_in_buffer == self.MAX_BUFFER_SIZE:
                self.checkpoint_EOB_timestamp = particle_hit[-1]["timestamp"]
            if self.entries_read_in_buffer > self.MAX_BUFFER_SIZE:
                if (particle_hit[-1]["timestamp"] - self.checkpoint_EOB_timestamp) > (self.EVENT_LENGTH + self.EVENT_EXTRA_GAP):
                    self.end_of_tevent = True
        return particle_hit

    def check_and_write_queue(self, event_queue, particle_event_list, myoutput):
        while event_queue.qsize() > 0:
            particle_event_list.extend(event_queue.get())
        if self.write_events_to_file is True:
            myoutput.write_events(particle_event_list)
        else:
            self.particle_hit_buffer.extend(particle_event_list)
        return []
        # particle_event_list = []  # Make sure to clear the list after we write out the data so we don't write it multiple times.

    def read_midas_files(self):
        # read_midas_files : Loops around an array of files that were passed in order to process multiple subruns
        # via wildcards passed on the CLI
        for my_file in self.midas_files:
            midas_file = midas.file_reader.MidasFile(my_file)
            print(my_file)
            self.read_midas_events(midas_file)

        return

    def read_midas_events(self, midas_file):
        particle_hits = []
        particle_event_list = []
        processes = []
        current_process_count = 0
        event_queue = Queue()

        myoutput = output_handler(self.output_file, self.output_format, self.sort_type)

        events = event_handler(self.sort_type, self.EVENT_LENGTH, self.EVENT_EXTRA_GAP, self.MAX_HITS_PER_EVENT, self.calibrate, self.cal_file)

        #midas_file = midas.file_reader.MidasFile(self.midas_file)
        for hit in tqdm(midas_file, unit=' Hits'):

            for bank_name, bank in hit.banks.items():
                particle_hit = []
                if bank_name == "MDPP":  # Check if this is an event from the MDPP16
                    particle_hit = self.decode_raw_hit_event(mdpp16.read_all_bank_events, bank.data)

                elif bank_name == "GRF4":  # Check if this is an event from the GRIF16
                    particle_hit = self.decode_raw_hit_event(grif16.read_all_bank_events, bank.data)

                if particle_hit:
                    particle_hits.extend(particle_hit)
                if (self.entries_read_in_buffer >= self.MAX_BUFFER_SIZE) and self.end_of_tevent is True:

                    if len(active_children()) < self.PROCCESS_NUM_LIMIT:  # Check if we are maxing out process # limit
                        self.checkpoint_EOB_timestamp = 0
                        self.end_of_tevent = False
                        p = Process(target=events.sort_events, args=(event_queue, particle_hits), daemon=False)
                        processes.append(p)
                        p.start()

                        current_process_count = current_process_count + 1
                        particle_hits = []
                        self.entries_read_in_buffer = -1
                        print("\nActive childeren : ", len(active_children()))

                    if len(active_children()) == self.PROCCESS_NUM_LIMIT:
                        while event_queue.qsize() == 0:  # Drain the master queue
                            sleep(.1)
                        particle_event_list = self.check_and_write_queue(event_queue, particle_event_list, myoutput)

                        for proc in processes:
                            proc.join()
                        current_process_count = 0
            self.entries_read_in_buffer = self.entries_read_in_buffer + 1

        if len(particle_hits) > 0:  # Check if we should sort and that there are hits to sort..
            print("Processing remaining events in queue...")
            events.sort_events(event_queue, particle_hits)
            particle_event_list = self.check_and_write_queue(event_queue, particle_event_list, myoutput)
        return 0
