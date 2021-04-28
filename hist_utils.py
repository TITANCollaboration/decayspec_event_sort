#!/home/vagrant/anaconda3/envs/pyuproot36/bin/pypy3
# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : January 13 2021 - Still during the plague..
# * Purpose : Create histograms from output of decay spec sorter both raw and otherwise..
#  * Requirements : Python 3, matplotlib, probably something other stuff numpy,scipy...
# *************************************************************************************
import argparse
from lib.input_handler import input_handler
import pathlib
from scipy.ndimage import gaussian_filter1d
import pandas as pd
import numpy as np

class spectrum:
    def __init__(self, chan, smear, scale):
        #self.input_filename = input_filename
        self.spectrum = None
        self.smear = smear
        self.scale = scale
        self.mychan = chan
        return

    def read_spectrum(self, input_filename):
        self.input_filename = input_filename
        my_input_handler = input_handler(input_filename)
        self.spectrum = my_input_handler.read_in_data()

    def scale_spectrum(self):
        print("Scaling:", self.scale)
        self.spectrum_scaled = self.spectrum * self.scale
        self.spectrum = self.spectrum_scaled

        if self.smear is not None:
            self.smear_spectrum()
        return

    def smear_spectrum(self):
        print("Smearing: ", self.smear)
        self.spectrum = pd.DataFrame(gaussian_filter1d(self.spectrum[str(self.mychan)], sigma=self.smear), columns=[str(self.mychan)])
        return

    def write_spectrum(self, output_filename=None):
        if output_filename is None:
            output_filename = self.input_filename[:-5]
            if self.scale is not None:
                output_filename = output_filename + "_scaled_" + str(self.scale)
            if self.smear is not None:
                output_filename = output_filename + "_smeared_" + str(self.smear)
            output_filename = output_filename + ".hist"
        print("Writing:", output_filename)
        self.spectrum.to_csv(output_filename, sep='|', header=True, index=False, chunksize=50000, mode='w', encoding='utf-8')
        return


def parse_and_run(args):
    my_chan = args.chan
    myspectrum = spectrum(my_chan, args.smear, args.scale)

    if args.asc is not None:
        myspectrum = spectrum(my_chan, args.smear, args.scale)
        myspectrum.read_spectrum(args.asc)
        bin_num = 1

        f = open(args.asc[:-5] + ".asc", "w")
        for count in myspectrum.spectrum[str(my_chan)]:
            line_output = str(bin_num) + "," + str(round(count)) + '\n'
            bin_num = bin_num + 1
            f.write(line_output)
        f.close()
        exit(0)
    if (args.smear is not None) and (args.scale is None):
        myspectrum.read_spectrum(args.input_filename)
        myspectrum.smear_spectrum()
        myspectrum.write_spectrum()
        exit(0)

    if args.scale is not None:
        myspectrum.read_spectrum(args.input_filename)
        myspectrum.scale_spectrum()
        myspectrum.write_spectrum()
        exit(0)

    if args.sum_files is not None:
        if args.output_file is None:
            print("Must specify the output file via --output_file")
            exit(1)
        hist_size = 8192
        combined_hist_pd = pd.DataFrame(0, index=np.arange(hist_size), columns=[str(my_chan)])
        for my_hist in args.sum_files:
            print("Summing:", my_hist)
            zero_hist = None
            myinput = input_handler(my_hist)
            data_pd = myinput.read_in_data()
            if data_pd.size < hist_size:  # Need to make all the columns match in size before adding together
                zero_hist = pd.DataFrame(0, index=np.arange(hist_size-data_pd.size), columns=[str(my_chan)])
                data_pd = data_pd.append(zero_hist, ignore_index=True)
            combined_hist_pd = combined_hist_pd + data_pd
        print("Writing sum to:", args.output_file)
        combined_hist_pd.to_csv(args.output_file, sep='|', header=True, index=False, chunksize=50000, mode='w', encoding='utf-8')

    return


def main():

    parser = argparse.ArgumentParser(description='Histogram Generator')

    parser.add_argument('--data_file', dest='input_filename', default=None, required=False,
                        help="input filename (.hist)")
    parser.add_argument('--output_file', dest='output_file', default=None, required=False,
                        help="Output file")
    parser.add_argument('--chan', dest='chan', type=str, default=99, required=False,
                        help="channel to perform operations on, default is 99")
    parser.add_argument('--scale', dest='scale', type=float, default=None, required=False,
                        help="Scape Factor")
    parser.add_argument('--smear', type=float, dest='smear', default=None, required=False,
                        help="smear histogram, parameter is sigma")
    parser.add_argument('--sum_files',  dest='sum_files', default=None, type=str, nargs='+',
                        required=False, help="Sum multiple histograms of the same chan # --output required")
    parser.add_argument('--to_asc',  dest='asc', default=None, required=False,
                        help="Export to RADWARE asc file (Specify input hist, output will be same name with .asc extension)")
    args, unknown = parser.parse_known_args()

    parse_and_run(args)


if __name__ == "__main__":
    main()
