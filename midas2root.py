# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : March 12th 2020 - Yup, writing this at the beginning of the great plague of 2020.
# * Purpose : To read in MIDAS files that contain MDPP16 and GRIF16 (either/or/both) and
# *           output in ROOT format.  Possibly also parquet at some point.
#  * Requirements : Python 3, UpRoot, MIDAS, tqdm
# *************************************************************************************
import sys
sys.path.append('/usr/local/packages/midas/python')
import argparse
import midas.file_reader
import mdpp16
import grif16
import sys
from tqdm import tqdm
from event_handler import sort_events
from multiprocessing import Process, Queue, active_children
from output_handler import write_particle_events, open_root_file
from time import sleep


MAX_GRIF16_CHANNELS = 16

# FOR GRIF16 use chan 0-15
# For MDPP16 use chan 100-115


# Number of events to buffer before writing out to file.  The larger the number the more memory you need but the faster it will go
# Setting this to -1 will mean buffer everything before writing, do stuff fast!
# Setting of 1 means I have no memory please write out each entry as you read it.
# This won't be exact and won't take into account multiple events in an entry so... whatever.  This is basically
# just a crude dial if you run into memory problems
MAX_BUFFER_SIZE = 100000  # One MILLION - A million events in memory is ~9MB
MAX_HITS_PER_EVENT = 999  # Maximum number of hits allowed in an EVENT, after that we move on to a new event, this is mostly just a protection against EVENT_LENGTH or
                          # EVENT_EXTRA_GAP being too long causing a MASSIVE EVENT(it's funny because I only work with gammas)
SORT_EVENTS = True

# @ 125Mhz every 'tick' is 8ns
EVENT_LENGTH = 20  # How long an temporal event can be,   we're just using ticks at the moment, maybe someone else wants to do some conversions!?!
EVENT_EXTRA_GAP = 5  # number of ticks to check in addition to EVENT_LENGTH in case one is just hanging out
PROCCESS_NUM_LIMIT = 2  # Max number of processess to spawn for sorting and potentially writing as well

# NOTE!! If event timestamps are out of order in the MIDAS file then there is a chance we will miss events at the MAX_BUFFER_SIZE boundary.
# So it is a good pratctice to set MAX_BUFFER_SIZE large, > 10,000,000
def decode_raw_hit_event(adc_hit_reader_func, bank_data, checkpoint_EOB_timestamp, entries_read_in_buffer, end_of_tevent):
    particle_hit = adc_hit_reader_func(bank_data)
    if particle_hit:
        if entries_read_in_buffer == MAX_BUFFER_SIZE:
            checkpoint_EOB_timestamp = particle_hit[-1]["timestamp"]
        if entries_read_in_buffer > MAX_BUFFER_SIZE:
            if (particle_hit[-1]["timestamp"] - checkpoint_EOB_timestamp) > (EVENT_LENGTH + EVENT_EXTRA_GAP):
                end_of_tevent = True
    return particle_hit, checkpoint_EOB_timestamp, end_of_tevent


def read_in_midas_file(midas_filename="run24286.mid", output_filename="justtesting.root", output_format="ROOT"):
    particle_hits = []
    entries_read_in_buffer = 0
    end_of_tevent = False
    checkpoint_EOB_timestamp = 0
    particle_event_list = []
    processes = []
    current_process_count = 0
    event_count = 0
    event_queue = Queue()

    if MAX_BUFFER_SIZE == -1:  # Probably going to always use buffering...
        buffering = False
    else:
        buffering = True

    print("-----------")
    root_file_handle = open_root_file(output_filename)
    midas_file = midas.file_reader.MidasFile(midas_filename)
    for hit in tqdm(midas_file, unit=' Hitss'):

        for bank_name, bank in hit.banks.items():
            particle_hit = []
            if bank_name == "MDPP":  # Check if this is an event from the MDPP16
                particle_hit, checkpoint_EOB_timestamp, end_of_tevent = decode_raw_hit_event(mdpp16.read_all_bank_events, bank.data, checkpoint_EOB_timestamp, entries_read_in_buffer, end_of_tevent)

            elif bank_name == "GRF4":  # Check if this is an event from the GRIF16
                particle_hit, checkpoint_EOB_timestamp, end_of_tevent = decode_raw_hit_event(grif16.read_all_bank_events, bank.data, checkpoint_EOB_timestamp, entries_read_in_buffer, end_of_tevent)

            if particle_hit:
                particle_hits.extend(particle_hit)

            if buffering is True and entries_read_in_buffer >= MAX_BUFFER_SIZE and end_of_tevent is True:
                if len(active_children()) < PROCCESS_NUM_LIMIT:  # Check if we are maxing out process # limit
                    #current_process_count = current_process_count + 1
                    checkpoint_EOB_timestamp = 0
                    end_of_tevent = False
                    if SORT_EVENTS is True:
                        p = Process(target=sort_events, args=(event_queue, particle_hits, EVENT_LENGTH, EVENT_EXTRA_GAP, MAX_HITS_PER_EVENT), daemon=False)
                        processes.append(p)
                        p.start()
                        current_process_count = current_process_count + 1
                    entries_read_in_buffer = -1
                    particle_hits = []
                    print("Active childeren : ", len(active_children()))
                if len(active_children()) == PROCCESS_NUM_LIMIT:
                    while True:
                        if event_queue.qsize() == current_process_count:
                            break
                        sleep(.1)
                    while event_queue.qsize() > 0:
                        particle_event_list.extend(event_queue.get())
                    for proc in processes:
                        proc.join()
                    current_process_count = 0
                    #  write out the queue here! or at least empty the queue into a new buffer... but might as well dump it
                    write_particle_events(particle_event_list, root_file_handle)
                    particle_event_list = []  # Make sure to clear the list after we write out the data so we don't write it multiple times.

        entries_read_in_buffer = entries_read_in_buffer + 1
    print("We're out of the main loop now")
    if len(particle_hits) != 0:
        sort_events(event_queue, particle_hits, EVENT_LENGTH, EVENT_EXTRA_GAP, MAX_HITS_PER_EVENT)
        while event_queue.qsize() > 0:
            particle_event_list.extend(event_queue.get())
        write_particle_events(particle_event_list, root_file_handle)

        #write out queue
        #write_particle_events(particle_events, output_filename, output_format)
    else:
        print("No events found to write...")
    print("Event Count : %i" % len(particle_event_list))
    return 0


def main():

    parser = argparse.ArgumentParser(description='Geant4 Macro Scheduler')

    parser.add_argument('--midas_file', dest='midas_file', required=True,
                        help="Path to the Midas file to read.")
    parser.add_argument('--output_file', dest='output_file', required=True,
                        help="Path to output file")
    parser.add_argument('--output_format', dest='output_format', required=False,
                        help="Format : ROOT, HISTOGRAM (DEFAULT  : ROOT) (more to maybe come, or add your own!)")

    parser.set_defaults(output_format="ROOT")

    args, unknown = parser.parse_known_args()

    read_in_midas_file(args.midas_file, args.output_file, args.output_format)


if __name__ == "__main__":
    main()
