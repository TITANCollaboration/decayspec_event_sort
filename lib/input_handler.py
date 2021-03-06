import pandas as pd
import pathlib
import csv

class input_handler:

    def __init__(self, input_filename, type=None):
        self.input_filename = input_filename
        self.file_suffix = pathlib.Path(input_filename).suffix
        self.type = type

    def read_in_data(self, separator='|'):
        if (self.type == 'plain_csv'):
            self.read_in_plain_csv()
            return self.mydata_plain_csv
        elif (self.file_suffix == '.csv') or (self.file_suffix == '.hist'):
            print("Processing CSV file:", self.input_filename)
            self.read_in_csv(separator)
        elif self.file_suffix == '.root':
            self.read_in_root()
        return self.mydata_df

    def read_in_histo_csv(self):
        with open(self.input_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter='|')
            for row in csv_reader:
                print(row)

    def read_in_plain_csv(self):
        self.mydata_plain_csv = []
        try:
            with open(self.input_filename, newline='') as csv_file:
                reader = csv.DictReader(csv_file)
            for row in reader:
                self.mydata_plain_csv.append(row)
        except:
            print("Something went wrong reading in file :", self.input_filename)
            exit(1)
        return 0

    def read_in_csv(self, separator='|'):
        try:
            self.mydata_df = pd.read_csv(self.input_filename, sep=separator, engine='c')
        except:
            print("Something went wrong reading in file :", self.input_filename)
            exit(1)
        return 0

    def read_in_pandas_histogram(self):
        my_hist_dict = {}
        df = pd.read_csv(self.input_filename, sep='|')
        for my_column in df.columns:
            my_hist_dict.update({my_column: df[my_column].values})
        return my_hist_dict

    def read_in_root(self):
        # This could be useful to write?
        import uproot
        root_file = uproot.open(self.input_filename)
        pulse_height = root_file["EVENT_NTUPLE"]["pulse_height"].array().astype(int)
        mydict = {'pulse_height': pulse_height, 'chan': 99, 'flags': 1}
        self.mydata_df = pd.DataFrame(data=mydict)
        # More stuff here, maybe convert to a pandas dataframe? Maybe this is fine? so many questions..
        return 0
