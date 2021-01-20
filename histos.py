# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : January 13 2021 - Still during the plague..
# * Purpose : Create histograms from output of decay spec sorter both raw and otherwise..
#  * Requirements : Python 3, matplotlib, probably something other stuff numpy,scipy...
# *************************************************************************************
import argparse
from lib.read_in_data import input_handler
from lib.histogram_generator import hist_gen


def parse_and_run(args):
    myinput = input_handler(args.input_filename)
    mydata_df = myinput.read_in_data()
    if args.bin_number > (args.max_pulse_height-args.min_pulse_height):
        bin_number = args.max_pulse_height-args.min_pulse_height
    else:
        bin_number = args.bin_number

    if args.plot_title is None:
        title = args.input_filename
    else:
        title = args.plot_title
    myhist = hist_gen(args.max_pulse_height, args.min_pulse_height, bin_number, title, args.xlabel, args.ylabel)
    #if args.channel_num is None:
    #    myhist.create_chan_histogram(mydata_df)
    #else:
    myhist.create_chan_basic_histograms(mydata_df, args.channel_num)
    return


def main():

    parser = argparse.ArgumentParser(description='Histogram Generator')

    parser.add_argument('--data_file', dest='input_filename', required=True,
                        help="path to data file from mds_sort")
    parser.add_argument('--chan', dest='channel_num', nargs='+', type=int, required=False,  # wont' require forever..
                        help="channel or list of channels to graph --chan 0 1 3")
    parser.add_argument('--xmax', dest='max_pulse_height', type=int, default=65535, required=False,  # wont' require forever..
                        help="Max Pulse Height")
    parser.add_argument('--xmin', dest='min_pulse_height', type=int, default=0, required=False,  # wont' require forever..
                        help="Min Pulse Height")
    parser.add_argument('--nbins', dest='bin_number', type=int, default=65535, required=False,  # wont' require forever..
                        help="Number of bins, will default to the smaller of 1000 or max_pulse_height - min_pulse_height")
    parser.add_argument('--type', dest='data_type', required=False, default='raw',  # wont' require forever..
                        help="Data input type, RAW 'raw' or EVENT 'event', raw is the default")
    parser.add_argument('--title', dest='plot_title', required=False, default=None,  # wont' require forever..
                        help="Title for Histogram")
    parser.add_argument('--xlabel', dest='xlabel', required=False, default='Pulse Height',  # wont' require forever..
                        help="X Axis Label")
    parser.add_argument('--ylabel', dest='ylabel', required=False, default='Counts',  # wont' require forever..
                        help="Y Axis Label")

    args, unknown = parser.parse_known_args()

    parse_and_run(args)

if __name__ == "__main__":
    main()
