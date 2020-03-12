import midas.file_reader

MAX_MDPP16_CHANNELS = 16
MAX_GRIF16_CHANNELS = 16


def read_mdpp16_header(bank0data, show_header=True):

    hsig = (bank0data >> 30) & 0x3
    subhead = (bank0data >> 24) & 0x3F
    mod_id = (bank0data >> 16) & 0xFF
    tdc_res = (bank0data >> 13) & 0x7
    adc_res = (bank0data >> 10) & 0x7
    nword = (bank0data >> 0) & 0x3FF

    if show_header is True:
        print("----HEADER---- ")
        print("hsig : %i  -  subhead : %i  - mod_id %i" % (hsig, subhead, mod_id))
        print("tdc_res : %i  -  adc_res : %i  -  nword : %i" % (tdc_res, adc_res, nword))
        print("--------------")
    return nword  # nword is the number of words in the bank


def read_mdpp16_event(bank_data, show_event=True):
    adc_value = -1
    chan = (bank_data >> 16) & 0x1F
    if chan < MAX_MDPP16_CHANNELS:
        adc_value = (bank_data >> 0) & 0xFFFF

    if show_event is True:
        print("----Event----")
        print("Channel : %i,  - ADC Value : %i" % (chan, adc_value))
        print("-------------")


def read_in_midas_file(midas_filename="run00233.mid.lz4"):
    mfile = midas.file_reader.MidasFile(midas_filename)
    num_entries = 0
    print("Printing only the top 10 entries at the moment")
    print("-----------")
    for event in mfile:
        if num_entries >= 100:
            break
        print("\n----=BEGIN=----")

        bank_names = ", ".join(b.name for b in event.banks.values())
        print("Event # %s of type ID %s contains banks %s" % (event.header.serial_number, event.header.event_id, bank_names))

        for bank_name, bank in event.banks.items():
            if bank_name == "MDPP":
                for data_pos in range(1, read_mdpp16_header(bank.data[0])):
                    read_mdpp16_event(bank.data[data_pos])

        num_entries = num_entries + 1
        print("----=END=----")
