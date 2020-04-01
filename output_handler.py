# *************************************************************************************
#  This file should handle the class definition and a generic way to writing out
#  the data so other formats can easily be added.
# *************************************************************************************
import pandas as pd
from root_pandas import to_root # This is used for the to_root() method


# *************************************************************************************
# write_root_file()
# Takes in a list of dict's, converts to a pandas dataframe and then writes that pandas
# pandas dataframe out to a root TTREE
# *************************************************************************************
def write_root_file(particle_events, output_filename):
    print("Writing ROOT file ...")
    pd_particle_events = pd.DataFrame(particle_events)  # convert list of dict's into pandas dataframe
    # For more info on root_pandas : https://github.com/scikit-hep/root_pandas
    pd_particle_events.to_root(output_filename, key='EVENT_NTUPLE')  # write out pandas dataframe to ROOT file, yup, that's it...
    return 0


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
def write_particle_events(particle_events, output_filename, format="ROOT"):
    if format == "ROOT":
        write_root_file(particle_events, output_filename)
    if format == "HISTOGRAM":
        show_histogram(particle_events)
