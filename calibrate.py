# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : January 13 2021 - Still during the plague..
# * Purpose : Create histograms from output of decay spec sorter both raw and otherwise..
#  * Requirements : Python 3, matplotlib, probably something other stuff numpy,scipy...
# *************************************************************************************
import argparse
from lib.midas_event_reader import midas_events
from lib.energy_calibration import energy_calibration
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
    event_length = 1  # This isn't a needed concept here so we just set it to one tick of the clock which disables event based stuff
    energy_cal = energy_calibration()

    if args.bin_number > (args.max_pulse_height-args.min_pulse_height):
        bin_number = args.max_pulse_height-args.min_pulse_height
    else:
        bin_number = args.bin_number

    if args.cal_type == 'linear':
        my_midas = midas_events(event_length, 'raw', args.co60_midas_files, None, None, args.cores, args.buffer_size, None, False)
    else:
        my_midas = midas_events(event_length, 'raw', args.eu152_midas_files, None, None, args.cores, args.buffer_size, None, False)

    if LOAD_FROM_DF_FILE is True:
        energy_cal.raw_to_histograms(None, args.min_pulse_height, args.max_pulse_height, bin_number, "my_cal2.csv")
    else:
        my_midas.read_midas_files()
        energy_cal.raw_to_histograms(my_midas.particle_hit_buffer, args.min_pulse_height, args.max_pulse_height, args.bin_number)
    energy_cal.find_co60_peaks()
    energy_cal.find_co60_centroids()
    if args.linear_output_file is None:
        linear_output_file = 'testme.lin'
    else:
        linear_output_file = args.linear_output_file
    energy_cal.find_linear_fit_from_co60(linear_output_file)
    #plt.hist(my_chan_hist, bins=bin_number, histtype='step')
    #plt.show()

    return

#  !! CHECK ON hit list to PANDAS conversion, might have to do something to keep the memory more restrained before going to histograms
def main():

    parser = argparse.ArgumentParser(description='Decay Spec Array Calibrator')
    parser.add_argument('--cores', dest='cores', type=int, default=2, required=False,
                        help="Number of cpu cores to use while processing.  Note more cores will use more memory as the buffer will be multiplied by cores")
    parser.add_argument('--buffer_size', dest='buffer_size', type=int, default=500000, required=False,
                        help="Buffer size, determines how many hits to read in before sorting and writing.  Larger buffer == more ram used")
    parser.add_argument('--co60_midas_files', dest='co60_midas_files', type=str, nargs='+', required=False,
                        help="Path to the Midas file(s) to read, supports wildcards. Must be 60Co files")
    parser.add_argument('--eu152_midas_files', dest='eu152_midas_files', type=str, nargs='+', required=False,
                        help="Path to the Midas file(s) to read, supports wildcards. Must be 152eu files")
    parser.add_argument('--linear_input_file', dest='linear_input_file', required=False,
                        help="File containing linear fits for detectors")
    parser.add_argument('--linear_output_file', dest='linear_output_file', required=False,
                        help="File to write linear calibrations to")
    parser.add_argument('--quad_output_file', dest='quad_output_file', required=False,
                        help="File to write Quadratic calibrations to")
    parser.add_argument('--chan', dest='channel_num', nargs='+', type=int, required=False,  # wont' require forever..
                        help="channel or list of channels to graph --chan 0 1 3")
    parser.add_argument('--xmax', dest='max_pulse_height', type=int, default=60000, required=False,  # Set a little low to throw out any junk at the end
                        help="Max Pulse Height")
    parser.add_argument('--xmin', dest='min_pulse_height', type=int, default=1, required=False,  # wont' require forever..
                        help="Min Pulse Height")
    parser.add_argument('--nbins', dest='bin_number', type=int, default=60000, required=False,  # wont' require forever..
                        help="Number of bins, will default to the smaller of 1000 or max_pulse_height - min_pulse_height")
    parser.add_argument('--cal_type', dest='cal_type', required=False, default='linear',  # wont' require forever..
                        help="Calibration Type: linear or quadratic, for the quadratic you must already have a linear fit file generated via 60Co")

    args, unknown = parser.parse_known_args()

    parse_and_run(args)

if __name__ == "__main__":
    main()
