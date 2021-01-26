# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : January 13 2021 - Still during the plague..
# * Purpose : Create histograms from output of decay spec sorter both raw and otherwise..
#  * Requirements : Python 3, matplotlib, probably something other stuff numpy,scipy...
# *************************************************************************************
import argparse
from lib.midas_event_reader import midas_events
from lib.energy_calibration import energy_calibration
from lib.input_handler import input_handler

#from matplotlib import pyplot as plt
# Should be able to suck in multiple .mid files and figure out what channels were used.

# From NuDat for 60Co
#     1173.228 3  	     99.85 % 3 	  1.1715 4
#	  1332.492 4  	     99.9826 % 6 	  1.332260 9
#	  2158.57 3  	      0.00120 % 20 	  2.6E-5 4   - Don't really care about this one.
#https://www.nndc.bnl.gov/nudat2/decaysearchdirect.jsp?nuc=60CO&unc=nds
# Probably convert to numpy histogram : https://numpy.org/doc/stable/reference/generated/numpy.histogram.html
# Find peaks using from scipy.signal import find_peaks
# Find peak boundaries maybe using some of my old particle physics 1 Code
# fit peak using lmfit https://millenia.cars.aps.anl.gov/software/python/lmfit/examples/example_use_pandas.html#sphx-glr-examples-example-use-pandas-py
# find highest peak and next big peak to the right of it


def parse_and_run(args):
    LOAD_FROM_DF_FILE = True
    energy_cal = energy_calibration()

    save_hist = False
    if args.save_hist_file is not None:
        save_hist = True

    my_midas = midas_events(1, 'histo', args.midas_files, args.save_hist_file, 'csv', args.cores, args.buffer_size, None, save_hist)

    if args.load_hist_file is not None:
        hist_input = input_handler(args.load_hist_file)
        my_midas.histo_dict = hist_input.read_in_pandas_histogram()
    else:
        my_midas.read_midas_files()

    if args.cal_type == 'linear':
        energy_cal.perform_linear_fit(my_midas.histo_dict)
    else:
        print("Quad fit here!")

    if args.lin_plot:
        energy_cal.plot_fit(cal_source='co60')
    if args.quad_plot:
        energy_cal.plot_fit(cal_source='eu152')

    return

#  !! CHECK ON hit list to PANDAS conversion, might have to do something to keep the memory more restrained before going to histograms
def main():

    parser = argparse.ArgumentParser(description='Decay Spec Array Calibrator')
    parser.add_argument('--cores', dest='cores', type=int, default=2, required=False,
                        help="Number of cpu cores to use while processing.  Note more cores will use more memory as the buffer will be multiplied by cores")
    parser.add_argument('--buffer_size', dest='buffer_size', type=int, default=500000, required=False,
                        help="Buffer size, determines how many hits to read in before sorting and writing.  Larger buffer == more ram used")
    parser.add_argument('--midas_files', dest='midas_files', type=str, nargs='+', default=None, required=False,
                        help="Path to the Midas file(s) to read, supports wildcards.")
    parser.add_argument('--load_hist', dest='load_hist_file', default=None, required=False,
                        help="Histogram file to read in to avoid re-reading MIDAS data")
    parser.add_argument('--save_hist', dest='save_hist_file', default=None, required=False,
                        help="File name of to write histogram to for quicker loads with --load_hist")
    parser.add_argument('--quad_output_file', dest='quad_output_file', required=False,
                        help="File to write Quadratic calibrations to")
    parser.add_argument('--xmax', dest='max_pulse_height', type=int, default=60000, required=False,  # Set a little low to throw out any junk at the end
                        help="*DISABLED* Max Pulse Height")
    parser.add_argument('--xmin', dest='min_pulse_height', type=int, default=1, required=False,  # wont' require forever..
                        help="*DISABLED* Min Pulse Height")
    parser.add_argument('--cal_type', dest='cal_type', required=False, default='linear',  # wont' require forever..
                        help="Calibration Type: linear or quadratic, for the quadratic you must already have a linear fit file generated via 60Co")
    parser.add_argument('--lin_plot', action='store_true', dest='lin_plot', required=False,  # wont' require forever..
                        help="Plot Linear fit of Co60")
    parser.add_argument('--quad_plot', action='store_true', dest='quad_plot', required=False,  # wont' require forever..
                        help="Plot Quadratic fit of Eu152")

    args, unknown = parser.parse_known_args()

    parse_and_run(args)

if __name__ == "__main__":
    main()
