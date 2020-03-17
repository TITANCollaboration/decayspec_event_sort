# *************************************************************************************
#  This file should handle the class definition and a generic way to writing out
#  the data so other formats can easily be added.
# *************************************************************************************
import uproot
import pandas as pd
import numpy
#class Particle_Event:

#    def __init__(self, chan, pulse_height, timestamp, flags):
#        self.chan = chan
#        self.pulse_height = pulse_height
#        self.timestamp = timestamp
#        self.flags = flags


def write_root_file(particle_events, output_filename):
    root_branch_dict = {"chan": numpy.int32, "pulse_height": numpy.int32, "timestamp": numpy.int32, "flags": numpy.int32}
    with uproot.recreate(output_filename) as root_output_file:
        print("Woo ready to write file stuffs!")
    #    print(particle_events)
        root_output_file["EVENT_TTREE"] = uproot.newtree(root_branch_dict, compression=uproot.LZ4(1), flushsize="2")

        # REDO ALL OF THIS WITH root_pandas....
        pd_particle_events = pd.DataFrame(particle_events)
        mychan = pd_particle_events[["chan"]].to_numpy()
        mypulse = pd_particle_events[["pulse_height"]].to_numpy()
        mytimestamp = pd_particle_events[["timestamp"]].to_numpy()
        myflags = pd_particle_events[["flags"]].to_numpy()
        #root_output_file["EVENT_TTREE"].extend({"chan": mychan,
        #                                        "pulse_height": mypulse,
        #                                        "timestamp": mytimestamp,
        #                                        "flags": myflags})
        #root_output_file = uproot.newtree(particle_events, title="EVENT_TTREE")
        root_output_file["EVENT_TTREE"].extend({"chan": pd_particle_events[["chan"]].to_numpy(),
                                                "pulse_height": pd_particle_events[["pulse_height"]].to_numpy(),
                                                "timestamp": pd_particle_events[["timestamp"]].to_numpy(),
                                                "flags": pd_particle_events[["flags"]].to_numpy()})
        #for d in particle_events:
        #    root_output_file["EVENT_TTREE"].extend(dict(d))

def write_particle_events(particle_events, output_filename, format="ROOT"):
    if format == "ROOT":
        write_root_file(particle_events, output_filename)
    print("write this shit out!!")
