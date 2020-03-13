# Written by : Jon Ringuette
# Started : March 12th 2020
# Yup, writing this at the beginning of the great plague of 2020.


import midas.file_reader
import mdpp16
import grif16


MAX_GRIF16_CHANNELS = 16


def read_in_midas_file(midas_filename="run00233.mid.lz4"):
    mfile = midas.file_reader.MidasFile(midas_filename)
    num_entries = 0
    print("Printing only the top 10 entries at the moment")
    print("-----------")
    for event in mfile:
        if num_entries >= 400:
            break
        print("\n----=BEGIN=----")

        bank_names = ", ".join(b.name for b in event.banks.values())
        print("Event # %s of type ID %s contains banks %s" % (event.header.serial_number, event.header.event_id, bank_names))

        for bank_name, bank in event.banks.items():
            if bank_name == "MDPP":
        #        for data_pos in range(1, mdpp16.read_header(bank.data[0]) + 1):
                mdpp16.read_all_bank_events(bank.data)
            elif bank_name == "GRF4":
        #        for data_pos in range(1, grif16.read_header(bank.data[0])):
                grif16.read_events(bank.data[data_pos])

        num_entries = num_entries + 1
        print("----=END=----")
