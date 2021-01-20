# *************************************************************************************
#  This file should handle the class definition and a generic way to writing out
#  the data so other formats can easily be added.
# *************************************************************************************
import pandas as pd
#import sys
#from root_pandas import to_root # This is used for the to_root() method
import uproot
import awkward
import numpy
import csv


class output_handler:

    def __init__(self, filename, file_type, raw_output=False, first_write=True):
        print("My File Type : ", file_type)
        self.filename = filename
        self.file_type = file_type.upper()
        self.first_write = first_write
        self.raw_output = raw_output
        self.file_handle = None

    # *************************************************************************************
    # write_root_file()
    # Takes in a list of dict's, converts to a pandas dataframe and then writes that pandas
    # pandas dataframe out to a root TTREE
    # *************************************************************************************
    def write_root_file(self, particle_events, file_handle):
        print("Getting AWkward..")
        a = awkward.fromiter(particle_events)
        print("Writing ROOT file ...")
        file_handle["EVENT_NTUPLE"].extend({"pulse_height": a.contents["pulse_height"],
                                            "chan": a.contents["chan"],
                                            "timestamp": a.contents["timestamp"],
                                            "hit_count": a.contents["hit_count"]})
    #    file_handle["EVENT_NTUPLE"]["pulse_height"].newbasket(a.contents["pulse_height"])
    #    file_handle["EVENT_NTUPLE"]["chan"].newbasket(a.contents["chan"])
    #    file_handle["EVENT_NTUPLE"]["timestamp"].newbasket(a.contents["timestamp"])
    #    file_handle["EVENT_NTUPLE"]["hit_count"].newbasket(a.contents["hit_count"])

        # For more info on root_pandas : https://github.com/scikit-hep/root_pandas
        #pd_particle_events.to_root(output_filename, key='EVENT_NTUPLE')  # write out pandas dataframe to ROOT file, yup, that's it...

        return 0

    def write_hdf_file(self, particle_events):
        # See about getting rid of the converting to pandas step.. Move to h5py
        pd_particle_events = pd.DataFrame(particle_events)  # convert list of dict's into pandas dataframe
        pd_particle_events.to_hdf(self.filename, key='stage', mode='a')

    def write_csv_file_pandas(particle_events, filename, first_write):
        # while simple this is rather slow and memory intensive, especially the converting to pandas part
        print("Converting to Pandas Dataframe")
        pd_particle_events = pd.DataFrame(particle_events)  # convert list of dict's into pandas dataframe
        print("Writing to CSV file :", filename)

        pd_particle_events.to_csv(filename, sep='|', header=first_write, index=False, chunksize=50000, mode='a', encoding='utf-8')

    def write_csv_file(self, particle_events):
        print("\nWriting to CSV file :", self.filename)
        column_names = particle_events[0].keys()
        mode_flag = 'a'
        if self.first_write is True:
            mode_flag = 'w'

        with open(self.filename, mode_flag, encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=column_names, delimiter='|')
            if self.first_write is True:
                writer.writeheader()
            for data in particle_events:
                writer.writerow(data)

    def open_root_file(self):
        print("going to open a root file!")
        self.file_handle = uproot.recreate(self.filename)
        self.file_handle["EVENT_NTUPLE"] = uproot.newtree({"pulse_height": uproot.newbranch(numpy.dtype(">i8"), size="hit_count"),
                                                           "chan": uproot.newbranch(numpy.dtype(">i8"), size="hit_count"),
                                                           "timestamp": uproot.newbranch(numpy.dtype(">i8"))}, compression=None)

    def show_histogram(self, particle_events):
        import matplotlib as plt
        import seaborn as sns
        # histos.py takes care of this initial funcationality but I will switch it over to be able to output
        # histogram data
        #pd_particle_events = pd.DataFrame(particle_events)  # convert list of dict's into pandas dataframe
        #myhist = pd_particle_events[pd_particle_events['chan'] == 0].hist(column='pulse_height', bins=1000)
        #plt.pyplot.show()
        #myhist.plot()
        #plt.show()
        #return 0

    # *************************************************************************************
    # write_particle_events()
    # Determine what file type is chosen, default to ROOT and select the appropriate function
    # *************************************************************************************
    def write_events(self, particle_events):
        if self.file_type.upper() == "ROOT":
            if self.first_write:
                self.file_handle = self.open_root_file()
            self.write_root_file(particle_events)
        if self.file_type.upper() == "HISTOGRAM":
            self.show_histogram(particle_events)
        if self.file_type == "HDF5":
            self.write_hdf_file(particle_events)
        if self.file_type == "CSV":
            self.write_csv_file(particle_events)
        self.first_write = False
