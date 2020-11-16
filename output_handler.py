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

# *************************************************************************************
# write_root_file()
# Takes in a list of dict's, converts to a pandas dataframe and then writes that pandas
# pandas dataframe out to a root TTREE
# *************************************************************************************
def extend_root_file(particle_events, file_handle):
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


def extend_hdf_file(particle_events, file_name):
    pd_particle_events = pd.DataFrame(particle_events)  # convert list of dict's into pandas dataframe
    pd_particle_events.to_hdf(file_name, key='stage', mode='a')


def extend_csv_file(particle_events, file_name, first_write):
    print("Going to write CSV file!")
    pd_particle_events = pd.DataFrame(particle_events)  # convert list of dict's into pandas dataframe
    pd_particle_events.to_csv(file_name, sep='|', header=first_write, index=False, chunksize=50000, mode='a', encoding='utf-8')


def open_root_file(output_filename):
    print("going to open a root file!")
    file_handle = uproot.recreate(output_filename)
    file_handle["EVENT_NTUPLE"] = uproot.newtree({"pulse_height": uproot.newbranch(numpy.dtype(">i8"), size="hit_count"),
                                                  "chan": uproot.newbranch(numpy.dtype(">i8"), size="hit_count"),
                                                  "timestamp": uproot.newbranch(numpy.dtype(">i8"))}, compression=None)
    return file_handle


def show_histogram(particle_events):
    import matplotlib as plt
    import seaborn as sns

    pd_particle_events = pd.DataFrame(particle_events)  # convert list of dict's into pandas dataframe
    myhist = pd_particle_events[pd_particle_events['chan'] == 0].hist(column='pulse_height', bins=1000)
    plt.pyplot.show()
    #myhist.plot()
    #plt.show()
    #return 0


# *************************************************************************************
# write_particle_events()
# Determine what file type is chosen, default to ROOT and select the appropriate function
# *************************************************************************************
def write_particle_events(particle_events, file_handle, file_name, format, first_write):
    if format.upper() == "ROOT":
    #    print("hi")
        extend_root_file(particle_events, file_handle)
    if format.upper() == "HISTOGRAM":
        show_histogram(particle_events)
    if format == "HDF5":
        extend_hdf_file(particle_events, file_name)
    if format.upper() == "CSV":
        extend_csv_file(particle_events, file_name, first_write)
