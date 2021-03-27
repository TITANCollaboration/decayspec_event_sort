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

class spectrum:
    def __init__(self, smear):
        #self.input_filename = input_filename
        self.spectrum = None
        self.smear = smear
        return

    def read_spectrum(self, input_filename):
        self.input_filename = input_filename
        my_input_handler = input_handler(input_filename)
        self.spectrum = my_input_handler.read_in_data()

    def scale_spectrum(self, scale_factor):
        print(self.spectrum['99'])
        self.spectrum_scaled = self.spectrum * scale_factor
        self.spectrum = self.spectrum_scaled
        self.scale_factor = scale_factor
        print(self.spectrum['99'])
        #exit(0)
        if self.smear is not None:
            self.spectrum = pd.DataFrame(gaussian_filter1d(self.spectrum['99'], sigma=self.smear), columns=['99'])
        print(self.spectrum['99'])
        return

    def write_spectrum(self, output_filename=None):
        if output_filename is None:
            output_filename = self.input_filename[:-5] + "_scaled_" + str(self.scale_factor) + ".hist"
        self.spectrum.to_csv(output_filename, sep='|', header=True, index=False, chunksize=50000, mode='w', encoding='utf-8')
        return

def parse_and_run(args):
    if args.asc is not None:
        myspectrum = spectrum(args.smear)
        myspectrum.read_spectrum(args.input_filename)
        bin_num = 0
        for count in myspectrum.spectrum['99']:
            print(bin_num, ", ", round(count))
            bin_num = bin_num + 1
        #f = open(args.input_filename[:-5] + ".asc", "w")
        #f.write("Now the file has more content!")
        #f.close()

    if args.scale_factor is not None:
        myspectrum = spectrum(args.smear)
        myspectrum.read_spectrum(args.input_filename)
        myspectrum.scale_spectrum(args.scale_factor)
        myspectrum.write_spectrum()
    if args.sum is not None:
        myinput1 = input_handler("../8pi_actual_bg_24hr_7dets_scaled_7day.hist")
        data1 = myinput1.read_in_data()
        myinput2 = input_handler("../sb129m1_bg_only_cascade_60s_2e5_1hr_scaled_to_7day_smeared.hist")
        data2 = myinput2.read_in_data()

        combined_data_pd = data1 + data2
        combined_data_pd.to_csv("../total_background_7day_no_neec.hist", sep='|', header=True, index=False, chunksize=50000, mode='w', encoding='utf-8')
    return


def main():

    parser = argparse.ArgumentParser(description='Histogram Generator')

    parser.add_argument('--output_file', dest='output_file', required=False,
                        help="Output file")
    parser.add_argument('--scale_factor', dest='scale_factor', type=float, default=None, required=False,
                        help="Scape Factor")
    parser.add_argument('--input_file', dest='input_filename', default=None, required=False,
                        help="input filename (.hist)")
    parser.add_argument('--smear', type=float, dest='smear', default=None, required=False,
                    help="smear histogram, parameter is sigma")
    parser.add_argument('--sum',  dest='sum', default=None, required=False,
                    help="Sum multiple histograms (work in progress)")
    parser.add_argument('--to_asc',  dest='asc', default=None, required=False,
                    help="Sum multiple histograms (work in progress)")
    args, unknown = parser.parse_known_args()

    parse_and_run(args)

if __name__ == "__main__":
    main()
