# *************************************************************************************
# Reads in data in GRF4 format
# *************************************************************************************

MAX_GRIF16_CHANNELS = 16  # This thing has 16 channels... so...
GRIF16_CHAN_PREFIX = 0


def read_header(bank0data, show_header=True):
    chan = -1
    if ((bank0data & 0xF0000000) >> 28) == 8:
        chan = (bank0data & 0xFFFF0) >> 4  # I think this is right....
    return chan


def test_for_footer(word_data):
    data_sig = (word_data >> 30) & 0x3
    if data_sig == 3:  # If this is true we got a footer! woo!
        event_counter_slash_timestamp = word_data & 0x3FFFFFFF  # grab 30 bits
        return event_counter_slash_timestamp
    else:
        return 0


def read_all_bank_events(bank_data):
    particle_events = []
    other_packet_count = 0
    integration_length = 0
    timestamp = 0
    pileup = 0
    chan = read_header(bank_data[0])
    num_words = len(bank_data)
    for data_pos in range(1, num_words):  # We have two words per event, one for ADC another for TDC
        data_sig = ((bank_data[data_pos] & 0xF0000000) >> 28)
        # So the way this is apparently done is we have to throw out a few words as they are just header info
        # This seems to be (if you're following along with the GRIF-16 fragment format doc) words I-V and
        # in our setup we apparently do not get a II (type 0xd) packet.  Pulse height doesn't get it's own
        # packet type so you just have to pick it out and it can come in a number of flavors data_sig 0-7
        # then it's the
        if data_sig == 10:  # Hex (0xa) of course, get's the low bits of the timestamp
            timestamp = bank_data[data_pos] & 0x0fffffff
        if data_sig == 11:  # Hex (0xb) high bits of the timestamp
            timestamp |= (bank_data[data_pos] & 0x0003fff) << 28
        if (0 <= data_sig <= 7):
            if data_pos < 4:
                pileup = bank_data[data_pos] & 0x001F
            elif data_pos > 4:  # Things are position sensitive so to sure to check this
                other_packet_count = other_packet_count + 1
                if other_packet_count == 1:
                    # The first "other packet" should be our pulse height ((word VIII))
                    #pulse_height = (bank_data[data_pos] & 0x01ffffff)
                    # In the GRIFFIN code I found they decode 25 bits for this (above) but in the documentation it
                    # mentions 26bits (below).  Tobias asked that I change it to 26bits which didn't have much
                    # impact.. I don't know... maybe leave it at 26bits for now unless we find a problem
                    pulse_height = (bank_data[data_pos] & 0x03ffffff)
                    # This is all a little weird, will need to verify with actual data.
                    integration_length |= ((bank_data[data_pos] & 0x7c000000) >> 17)
                if other_packet_count == 2:
                    integration_length |= (bank_data[data_pos] & 0x7FC00000) >> 22
    integrated_pulse_height = 0
    if integration_length != 0:
        integrated_pulse_height = pulse_height / integration_length
        myparticle_event = {"timestamp": timestamp, "chan": (chan + GRIF16_CHAN_PREFIX), "pulse_height": integrated_pulse_height, "flags": pileup}
    #    print("TimeStamp %i   -  Pulse Height %i" % (timestamp, integrated_pulse_height))
        particle_events.append(myparticle_event)

    # print("Pileup : %i   -   Time stamp : %i" % (pileup, timestamp))
    return particle_events
