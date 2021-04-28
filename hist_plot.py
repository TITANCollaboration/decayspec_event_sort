# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : January 13 2021 - Still during the plague..
# * Purpose : Create histograms from output of decay spec sorter both raw and otherwise..
#  * Requirements : Python 3, matplotlib, probably something other stuff numpy,scipy...
# *************************************************************************************
import argparse
from lib.input_handler import input_handler
from lib.histogram_generator import hist_gen
import pathlib

def parse_and_run(args):
    sum_all = False
    zoom_xmin = None
    zoom_xmax = None
    if args.channels is None:
        sum_all = True

    myinput = input_handler(args.input_filename)
    mydata_df = myinput.read_in_data()
#    if args.bin_number > (args.max_pulse_height-args.min_pulse_height):
#        bin_number = args.max_pulse_height-args.min_pulse_height
#    else:
#        bin_number = args.bin_number

    if args.plot_title is None:
        title = args.input_filename
    else:
        title = args.plot_title
    if args.zoom is True:
        if (args.zoom_xmin is None) or (args.zoom_xmin < args.min_pulse_height):
            zoom_xmin = args.min_pulse_height
        else:
            zoom_xmin = args.zoom_xmin
        if (args.zoom_xmax is None) or (args.zoom_xmax > args.max_pulse_height):
            zoom_xmax = args.max_pulse_height
        else:
            zoom_xmax = args.zoom_xmax

    input_file_wo_suffix = args.input_filename[:-5]

    myhist = hist_gen(input_filename=input_file_wo_suffix,
                      save_all=args.save_all,
                      overlay_files=args.overlay_files,
                      max_pulse_height=args.max_pulse_height,
                      min_pulse_height=args.min_pulse_height,
                      title=title,
                      xlabel=args.xlabel,
                      ylabel=args.ylabel,
                      energy_labels=args.energy_labels,
                      y_axis_min=args.y_axis_min,
                      y_axis_max=args.y_axis_max,
                      zoom=args.zoom,
                      zoom_xmin=zoom_xmin,
                      zoom_xmax=zoom_xmax,
                      zoom_ymin=args.zoom_ymin,
                      zoom_ymax=args.zoom_ymax,
                      ylog_zoom=args.ylog_zoom,
                      overlay_multipliers=args.overlay_multipliers,
                      output_filename=args.output_filename,
                      ylog=args.ylog)

    myhist.grapher(mydata_df, args.channels, sum_all)
    return


def main():

    parser = argparse.ArgumentParser(description='Histogram Generator')

    parser.add_argument('--data_file', dest='input_filename', required=True,
                        help="path to data file .hist or .root")
    parser.add_argument('--output_file', dest='output_filename', required=False,
                        help="path to png file to save graph as.  By default it will be saved as the same name as the data_file with a .png extension")
    parser.add_argument('--overlay_files', dest='overlay_files', type=str, nargs='+', default=None, required=False,
                        help="Read in overlay file(s), supports wildcards.")
    parser.add_argument('--save', action='store_true', dest='save_all', required=False,
                        help="path to data file you wish to save pandas histogram data to for future use.")
    parser.add_argument('--chan', dest='channels', nargs='+', default=None, type=int, required=False,
                        help="channel or list of channels to graph --chan 0 1 3, **if not specified will SUM all channels")
    parser.add_argument('--xmax', dest='max_pulse_height', type=int, default=65535, required=False,
                        help="Max Pulse Height")
    parser.add_argument('--xmin', dest='min_pulse_height', type=int, default=0, required=False,
                        help="Min Pulse Height")
    parser.add_argument('--ymax', dest='y_axis_max', type=float, default=None, required=False,
                        help="Max Pulse Height")
    parser.add_argument('--ymin', dest='y_axis_min', type=float, default=0, required=False,
                        help="Min Pulse Height")
    parser.add_argument('--nbins', dest='bin_number', type=int, default=65535, required=False,
                        help="(deprecated)Number of bins, will default to the smaller of 1000 or max_pulse_height - min_pulse_height")
    parser.add_argument('--title', dest='plot_title', required=False, default=None,
                        help="Title for Histogram")
#    parser.add_argument('--save_file', dest='save_file', required=False, default=None,
#                        help="File to save histogram to (csv)")
    parser.add_argument('--xlabel', dest='xlabel', required=False, default='Pulse Height',
                        help="X Axis Label")
    parser.add_argument('--ylabel', dest='ylabel', required=False, default='Counts',
                        help="Y Axis Label")
    parser.add_argument('--energy_labels', dest='energy_labels', required=False, nargs='+', default=[],
                        help="Y Axis Label")
    parser.add_argument('--zoom', action='store_true', dest='zoom', required=False,  # wont' require forever..
                        help="Enable Zoomed window")
    parser.add_argument('--ylog_zoom', action='store_true', dest='ylog_zoom', required=False,  # wont' require forever..
                        help="Use log scale for zoom")
    parser.add_argument('--ylog', action='store_true', dest='ylog', required=False,  # wont' require forever..
                        help="Use log scale for yaxis")
    parser.add_argument('--zoom_xmin',  dest='zoom_xmin', default=None, type=int, required=False,  # wont' require forever..
                        help="Min bin # for zoom region")
    parser.add_argument('--zoom_xmax',  dest='zoom_xmax', default=None, type=int, required=False,  # wont' require forever..
                        help="Max bin # for zoom region")
    parser.add_argument('--zoom_ymin',  dest='zoom_ymin', default=None, type=float, required=False,  # wont' require forever..
                        help="Min yval for zoom region")
    parser.add_argument('--zoom_ymax',  dest='zoom_ymax', default=None, type=float, required=False,  # wont' require forever..
                        help="Max yval for zoom region")
    parser.add_argument('--overlay_multipliers', dest='overlay_multipliers', type=float, nargs='+', default=None, required=False,
                        help="List of multipliers to apply to overlay")
    args, unknown = parser.parse_known_args()

    parse_and_run(args)

if __name__ == "__main__":
    main()
