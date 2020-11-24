# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : March 12th 2020 - Yup, writing this at the beginning of the great plague of 2020.
# * Purpose : To read in MIDAS files that contain MDPP16 and GRIF16 (either/or/both) and
# *           output in ROOT format.  Possibly also parquet at some point.
#  * Requirements : Python 3, UpRoot, MIDAS, tqdm
# *************************************************************************************
import argparse
from midas_event_reader import midas_events


def main():

    parser = argparse.ArgumentParser(description='Geant4 Macro Scheduler')

    parser.add_argument('--midas_file', dest='midas_file', required=True,
                        help="Path to the Midas file to read.")
    parser.add_argument('--output_file', dest='output_file', required=True,
                        help="Path to output file")
    parser.add_argument('--event_length', dest='event_length', type=int, default=1, required=False,
                        help="Set length of event window, done in ticks @ 100Mhz, 1 tick == 0.001ms")
    parser.add_argument('--output_format', dest='output_format', default='csv', required=False,
                        help="Format : ROOT, HISTOGRAM (DEFAULT  : CSV) (more to maybe come, or add your own!)")
    parser.add_argument('--sort_type', dest='sort_type', default='event', required=False,
                        help="Type of sort, defaults to event based, can specify 'raw' as well for no sorting")

    args, unknown = parser.parse_known_args()

    my_midas = midas_events(args.event_length, args.sort_type, args.midas_file, args.output_file, args.output_format)
    my_midas.read_midas_events()


if __name__ == "__main__":
    main()
