# *************************************************************************************
# Reads in data in GRF4 format
# *************************************************************************************

MAX_GRIF16_CHANNELS = 16  # This thing has 16 channels... so...


def read_header(bank0data, show_header=True):
    chan = -1
    print(bank0data)
    if ((bank0data & 0xF0000000) >> 28) == 8:
        print("We have a Header!")
        chan = (bank0data & 0xFFFF0) >> 4  # I think this is right....

    return chan  # nword is the number of words in the bank


def test_for_footer(word_data):
    data_sig = (word_data >> 30) & 0x3
    if data_sig == 3:  # If this is true we got a footer! woo!
        event_counter_slash_timestamp = word_data & 0x3FFFFFFF  # grab 30 bits
        return event_counter_slash_timestamp
    else:
        return 0


def read_all_bank_events(bank_data):
    particle_events = []
    packet_type_7_count = 0
    #print(bank_data)
    chan = read_header(bank_data[0])
    num_words = len(bank_data)
    for data_pos in range(1, num_words):  # We have to words per event, one for ADC another for TDC
        print("Data pos : %i - " % (data_pos + 1),  end='')
        data_sig = ((bank_data[data_pos] & 0xF0000000) >> 28)
        print("Data Sig", data_sig, " - ", bank_data[data_pos])
        if 0 <= data_sig <= 7:  # This should be a pulse_heigh packet
            if packet_type_7_count == 1:
                print("     - Pulse Height %i" % (bank_data[data_pos] & 0x01ffffff))
        #    data_sig = (bank_data[current_word] >> 30) & 0x3
            packet_type_7_count = packet_type_7_count + 1  # There are two different packets both that come up as 7 so the first one is the pulse height the 2nd is the cfd & int stuff

        #print(bank_data[data_pos])
#        event_counter_slash_timestamp = test_for_footer(bank_data[data_pos])
#        if event_counter_slash_timestamp == 0:

        #particle_events.append(read_single_event(bank_data[data_pos], chan,  False))
        #    print("     Event Counter_slash_timestamp : %i" % event_counter_slash_timestamp)
    return particle_events
