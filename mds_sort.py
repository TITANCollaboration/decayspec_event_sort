# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : March 12th 2020 - Yup, writing this at the beginning of the great plague of 2020.
# * Purpose : To read in MIDAS files that contain MDPP16 and GRIF16 (either/or/both) and
# *           output in ROOT format.  Possibly also parquet at some point.
#  * Requirements : Python 3, UpRoot (optional), MIDAS, tqdm, HDFS (optional)
# *************************************************************************************
import argparse
from lib.midas_event_reader import midas_events


# !!! Add in histogram data output to allow for smaller size data sets

def main():
    parser = argparse.ArgumentParser(description='Midas Decay Spec Sorter')

    parser.add_argument('--midas_files', dest='midas_files', type=str, nargs='+', required=True,
                        help="Path to the Midas file(s) to read, supports wildcards.")
    parser.add_argument('--output_file', dest='output_file', required=True,
                        help="Path to output file")
    parser.add_argument('--bin_div', dest='bin_div', type=int, default=1, required=False,
                        help="Divide by this to create bins.  Going from 64k to 8k set value to 8 (only MDPP16)")
    parser.add_argument('--event_length', dest='event_length', type=int, default=1, required=False,
                        help="Set length of event window, done in ticks @ 100Mhz, 1 tick == 0.001ms")
    parser.add_argument('--cores', dest='cores', type=int, default=2, required=False,
                        help="Number of cpu cores to use while processing.  Note more cores will use more memory as the buffer will be multiplied by cores")
    parser.add_argument('--buffer_size', dest='buffer_size', type=int, default=500000, required=False,
                        help="Buffer size, determines how many hits to read in before sorting and writing.  Larger buffer == more ram used")
    parser.add_argument('--output_format', dest='output_format', default='csv', required=False,
                        help="Format : ROOT, HISTOGRAM, CSV, HDF5 (DEFAULT  : CSV) (Only CSV fully works right now, ROOT is slow)")
    parser.add_argument('--sort_type', dest='sort_type', default='event', required=False,
                        help="Type of sort, defaults to event based, can specify 'raw' as well for no sorting, 'histo' for histogram")
    parser.add_argument('--no_round', dest='no_round', default=1, required=False,
                        help="Don't round the floats that come in from the DAQ's ** Not implimented yet..")
    parser.add_argument('--cal_file', dest='cal_file', required=False, default=None,
                        help="Calibration file")
    parser.add_argument('--ppg_data_file', dest='ppg_data_file', required=False, default=None,
                        help="PPG Data file (csv)")
    parser.add_argument('--ppg_value_range', dest='ppg_value_range', required=False, nargs='+', type=float,
                        default=None,
                        help="min and max values for ppg value to accept event (type: histo).  Ex: --ppg_value_range 1100 1200")

    args, unknown = parser.parse_known_args()
    print("PPG:", args.ppg_value_range)
    my_midas = midas_events(args.event_length,
                            args.sort_type,
                            args.midas_files,
                            args.output_file,
                            args.output_format,
                            args.cores,
                            args.buffer_size,
                            args.cal_file,
                            write_events_to_file=True,
                            ppg_data_file=args.ppg_data_file,
                            ppg_value_range=args.ppg_value_range,
                            bin_div=args.bin_div)
    # my_midas.read_midas_events()
    my_midas.read_midas_files()


if __name__ == "__main__":
    main()
