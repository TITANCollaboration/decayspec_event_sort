import pandas as pd
import pathlib


class input_handler:

    def __init__(self, input_filename):
        self.input_filename = input_filename
        self.file_suffix = pathlib.Path(input_filename).suffix

    def read_in_data(self):
        if self.file_suffix == '.csv':
            print("Processing CSV file:", self.input_filename)
            self.read_in_csv()
        return self.mydata_df

    def read_in_csv(self):
        try:
            self.mydata_df = pd.read_csv(self.input_filename, sep='|', engine='c')
        except:
            print("Something went wrong reading in file :", self.input_filename)
            exit(1)
        #print(self.mydata_df)
        return 0
