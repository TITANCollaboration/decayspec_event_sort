# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : March 12th 2020 - Yup, writing this at the beginning of the great plague of 2020.
# * Purpose : To read in MIDAS files that contain MDPP16 and GRIF16 (either/or/both) and
# *           output in ROOT format.  Possibly also parquet at some point.
#  * Requirements : Python 3, UpRoot, MIDAS, tqdm
# *************************************************************************************

import argparse
import midas.file_reader
import mdpp16
import grif16
from tqdm import tqdm
from output_handler import write_particle_events

MAX_GRIF16_CHANNELS = 16

# FOR GRIF16 use chan 0-15
# For MDPP16 use chan 100-115


# Number of events to buffer before writing out to file.  The larger the number the more memory you need but the faster it will go
# Setting this to -1 will mean buffer everything before writing, do stuff fast!
# Setting of 1 means I have no memory please write out each entry as you read it.
# This won't be exact and won't take into account multiple events in an entry so... whatever.  This is basically
# just a crude dial if you run into memory problems
MAX_BUFFER_SIZE = -1


def read_in_midas_file(midas_filename="run24286.mid", output_filename="justtesting.root", output_format="ROOT"):
    particle_events = []
    num_entries = 0
    entries_read_in_buffer = 0
    if MAX_BUFFER_SIZE == -1:
        buffering = False
    else:
        buffering = True

    print("Printing only the top 400 entries at the moment")
    print("-----------")
    midas_file = midas.file_reader.MidasFile(midas_filename)
    for event in tqdm(midas_file, unit=' Events'):
        #if num_entries >= 40000:  # this is just in here to make testing easier..
        #        break
        # print("\n----=BEGIN=----")
        # bank_names = ", ".join(b.name for b in event.banks.values())
        # print("Event # %s of type ID %s contains banks %s" % (event.header.serial_number, event.header.event_id, bank_names))

        for bank_name, bank in event.banks.items():
            if bank_name == "MDPP":
                particle_events.extend(mdpp16.read_all_bank_events(bank.data))
            elif bank_name == "GRF4":
            #    print("We got a GRIF16 event!!")
                particle_events.extend(grif16.read_all_bank_events(bank.data))
#                particle_events.extend(grif16.read_events(bank.data))

            if buffering is True and entries_read_in_buffer >= MAX_BUFFER_SIZE:
                entries_read_in_buffer = -1
                write_particle_events(particle_events, output_filename)
                particle_events = []

        num_entries = num_entries + 1
        entries_read_in_buffer = entries_read_in_buffer + 1

    print("Particle Event count : %i" % len(particle_events))
    if len(particle_events) != 0:
        write_particle_events(particle_events, output_filename, output_format)
    else:
        print("No events found to write...")
    # return particle_events
        # print("----=END=----")

    return particle_events


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
