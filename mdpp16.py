# *************************************************************************************
# Reads in data in MDPP format, you can find the complete docs with bit shceme @
# https://www.mesytec.com/products/datasheets/MDPP-16_SCP-RCP.pdf
# We are using it in RCP mode so there may be a difference or two if you are using it
# in SCP mode
# *************************************************************************************

MAX_MDPP16_CHANNELS = 16  # This thing has 16 channels... so...
MDPP16_CHAN_PREFIX = 100

def read_header(bank0data, show_header=True):

    hsig = (bank0data >> 30) & 0x3
    subhead = (bank0data >> 24) & 0x3F
    mod_id = (bank0data >> 16) & 0xFF
    tdc_res = (bank0data >> 13) & 0x7
    adc_res = (bank0data >> 10) & 0x7
    numwords = (bank0data >> 0) & 0x3FF

    if show_header is True:
        print("   ----HEADER---- ")
        print("     hsig : %i  -  subhead : %i  - mod_id %i" % (hsig, subhead, mod_id))
        print("     tdc_res : %i  -  adc_res : %i  -  nword : %i" % (tdc_res, adc_res, nword))
    return numwords  # nword is the number of words in the bank


def test_for_footer(word_data):
    data_sig = (word_data >> 30) & 0x3
    if data_sig == 3:  # If this is true we got a footer! woo!
        event_counter_slash_timestamp = word_data & 0x3FFFFFFF  # grab 30 bits
        return event_counter_slash_timestamp
    else:
        return 0


def read_single_event(bank_data, show_event=True):
    #  I think I'm going to read these things in pairs as that is what they are.. besides the footer.  I will check
    #  that in the read_all_bank_events
    num_words_per_event = 2
    adc_value = -1
    tdc_value = -1
    chan = -1
    trigchan = -1
    flags = 0
    # event_counter_slash_timestamp = -1
    for current_word in range(num_words_per_event):
        data_sig = (bank_data[current_word] >> 30) & 0x3

        # Taking the trigger flag and channel number together, this 6 bit address runs from 0 to 15 for amplitudes,
        # 16 to 31 for time, and 32 / 33 are trigger0 / trigger1 time
        trigchan = (bank_data[current_word] >> 16) & 0x3F
        chan = (bank_data[current_word] >> 16) & 0x1F
        if chan < MAX_MDPP16_CHANNELS:
            adc_value = (bank_data[current_word] >> 0) & 0xFFFF
        if chan > MAX_MDPP16_CHANNELS and chan < (MAX_MDPP16_CHANNELS * 2) + 2:
            tdc_value = (bank_data[current_word] >> 0) & 0xFFFF

    # Set values to object to return, remember we are using a prefix of +100 for MDPP16 channel addressing
    myparticle_event = {"timestamp": tdc_value, "chan": (chan + MDPP16_CHAN_PREFIX), "pulse_height": adc_value, "flags": flags}

    if show_event is True:
        print("   ----Event----")
        print("     Sig : %i,  Channel : %i, - trigChan: %i, - ADC Value : %i  - TDC Value : %i" % (data_sig, chan, trigchan, adc_value, tdc_value))
    return myparticle_event


def read_all_bank_events(bank_data):
    particle_events = []

    for data_pos in range(1, read_header(bank_data[0], False) + 1, 2):  # We have two words per event, one for ADC another for TDC
        event_counter_slash_timestamp = test_for_footer(bank_data[data_pos])
        if event_counter_slash_timestamp == 0:
            particle_events.append(read_single_event([bank_data[data_pos], bank_data[data_pos + 1]], False))
        #    print("     Event Counter_slash_timestamp : %i" % event_counter_slash_timestamp)
    return particle_events
