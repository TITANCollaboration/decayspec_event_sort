from configobj import ConfigObj
from numpy.polynomial.polynomial import polyval
from numpy import array


class energy_calibration:

    def __init__(self, cal_file):
        self.cal_file = cal_file
        self.cal_dict = {}
        self.read_in_calibration_file()
        return

    def read_in_calibration_file(self):
        # Read in the calibration file making appropriate dict of polynomial coefficients
        print("Going to read in the config file...")
        config = ConfigObj(self.cal_file)
        for adc in config.keys():
            adc_prefix = int(config[adc]['prefix'])
            for adc_channel in config[adc]:
                if adc_channel != "prefix":
                    # Sorry about this line.. I put the channel + prefix as a dict key and then the coefficients as a numpy array as the value of that key
                    # leads to something like : {12: array([1., 2., 3.]), 13: array([2., 2., 3.]), 14: array([1. , 0.5]), 15: array([1. , 0.5])}
                    self.cal_dict[int(config[adc][adc_channel]['chan']) + adc_prefix] = array(list(map(float, config[adc][adc_channel]['cal_coef'].split())))

    def calibrate_hit(self, hit):
        # Performs a polynomial calibration onto an individual pulse height
        hit['pulse_height'] = polyval(hit['pulse_height'], self.cal_dict[hit['chan']], tensor=False)
        return hit

    def calibrate_list(self, hit_list):
        # Loop through all pulse heights to calibrate against
        print("Calibrating particle list...")
        for hit_pos in range(0, len(hit_list)):
            hit_list[hit_pos] = self.calibrate_hit(hit_list[hit_pos])
        return hit_list

# Performance stuff
# 1:20 no calibration
# 4:40 w/ Calibration (normal list)
# 3:50 w/ cdlibration (numpy list for coeff)
