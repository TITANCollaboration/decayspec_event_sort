from configobj import ConfigObj


class energy_calibration:

    def __init__(self, cal_file):
        self.cal_file = cal_file
        self.read_in_calibration_file()
        return

    def read_in_calibration_file(self):
        print("Going to read in the config file...")
        config = ConfigObj(self.cal_file)
        # Parse config file.
        # finish calibrate_hit

    def calibrate_hit(self, hit):
        return hit

    def calibrate_list(self, hit_list):
        print("Calibrating particle list...")
        for hit_pos in range(0, len(hit_list)):
            hit_list[hit_pos] = self.calibrate_hit(hit_list[hit_pos])
        return hit_list
