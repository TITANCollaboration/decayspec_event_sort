# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : January 13 2021 - Still during the plague..
# * Purpose : Create histograms from output of decay spec sorter both raw and otherwise..
#  * Requirements : Python 3, matplotlib, probably something other stuff numpy,scipy...
# *************************************************************************************
import argparse
from lib.input_handler import input_handler
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
    myhist = hist_gen(args.max_pulse_height,
                      args.min_pulse_height,
                      bin_number,
                      title,
                      args.xlabel,
                      args.ylabel,
                      args.energy_labels,
                      args.y_axis_min,
                      args.y_axis_max)
    #if args.channel_num is None:
    #    myhist.create_chan_histogram(mydata_df)
    #else:
    if args.data_type == 'raw':
        myhist.create_chan_basic_histograms_from_raw_df(mydata_df, args.channel_num)
    elif args.data_type == 'histo':
        myhist.create_chan_basic_histograms_from_histo_df(mydata_df, args.channel_num)
    return


def main():

    parser = argparse.ArgumentParser(description='Histogram Generator')

    parser.add_argument('--data_file', dest='input_filename', required=True,
                        help="path to data file from mds_sort")
    parser.add_argument('--chan', dest='channel_num', nargs='+', default=[0], type=int, required=False,
                        help="channel or list of channels to graph --chan 0 1 3")
    parser.add_argument('--xmax', dest='max_pulse_height', type=int, default=65535, required=False,
                        help="Max Pulse Height")
    parser.add_argument('--xmin', dest='min_pulse_height', type=int, default=0, required=False,
                        help="Min Pulse Height")
    parser.add_argument('--ymax', dest='y_axis_max', type=int, default=None, required=False,
                        help="Max Pulse Height")
    parser.add_argument('--ymin', dest='y_axis_min', type=int, default=None, required=False,
                        help="Min Pulse Height")
    parser.add_argument('--nbins', dest='bin_number', type=int, default=65535, required=False,
                        help="Number of bins, will default to the smaller of 1000 or max_pulse_height - min_pulse_height")
    parser.add_argument('--type', dest='data_type', required=False, default='raw',  # wont' require forever..
                        help="Data input type, Histogram 'histo', RAW 'raw' or EVENT 'event'(NOT YET!), raw is the default")
    parser.add_argument('--title', dest='plot_title', required=False, default=None,
                        help="Title for Histogram")
    parser.add_argument('--save_file', dest='save_file', required=False, default=None,
                        help="File to save histogram to (csv)")
    parser.add_argument('--xlabel', dest='xlabel', required=False, default='Pulse Height',
                        help="X Axis Label")
    parser.add_argument('--ylabel', dest='ylabel', required=False, default='Counts',
                        help="Y Axis Label")
    parser.add_argument('--energy_labels', dest='energy_labels', required=False, nargs='+', default=[],
                        help="Y Axis Label")


    args, unknown = parser.parse_known_args()

    parse_and_run(args)

if __name__ == "__main__":
    main()
