# *************************************************************************************
# Reads in data in MDPP format, you can find the complete docs with bit shceme @
# https://www.mesytec.com/products/datasheets/MDPP-16_SCP-RCP.pdf
# We are using it in RCP mode so there may be a difference or two if you are using it
# in SCP mode
# *************************************************************************************
from pprint import pprint

MAX_MDPP16_CHANNELS = 16  # This thing has 16 channels... so...
MDPP16_CHAN_PREFIX = 100


def read_header(bank0data, show_header=True):

    hsig = (bank0data >> 30) & 0x3
    subhead = (bank0data >> 28) & 0x3
    mod_id = (bank0data >> 16) & 0xFF
    tdc_res = (bank0data >> 13) & 0x7
    adc_res = (bank0data >> 10) & 0x7
    numwords = (bank0data >> 0) & 0x3FF

    if show_header is True:
        print("   ----HEADER---- ")
        print("     hsig : %i  -  subhead : %i  - mod_id %i" % (hsig, subhead, mod_id))
        print("     tdc_res : %i  -  adc_res : %i  -  numword : %i" % (tdc_res, adc_res, numwords))
    return numwords  # nword is the number of words in the bank


def read_footer(word_data):
    debug = False
    data_sig = (word_data >> 30) & 0x3
    if data_sig == 3:  # If this is true we got a footer! woo!
        event_counter_slash_timestamp = (word_data >> 0) & 0x3FFFFFFF  # grab 30 bits
        if debug is True:
            print("------Footer------")
            print("TS:", event_counter_slash_timestamp)

        return event_counter_slash_timestamp
    else:
        return 0


def read_words_for_events(bank_data, show_event=True):
    #  I think I'm going to read these things in pairs as that is what they are.. besides the footer.  I will check
    #  that in the read_all_bank_events
    show_all_data = False
    event_count = 0
    adc_value = -1
    tdc_value = -1
    low_ts = -1
    high_ts = -1
    chan = -1
    trigchan = -1
    flags = 1  # Setting to 1 to match the pileup flag for the grif16, it means nothing here
    # event_counter_slash_timestamp = -1
    myparticle_events = []

    for current_word in range(0, len(bank_data)):
        adc_value = -1
        if bank_data[current_word] == 4294967295:  # This is all 1's and seems to just be a filler event so disgard
            continue
        data_sig = (bank_data[current_word] >> 30) & 0x3
        if data_sig == 3:
            low_ts = (bank_data[current_word] >> 0) & 0x3FFFFFFF
            #print("Lower TS:", low_ts)
            continue
            #print("What!?!? a datasig with 3!?!?")
            #exit(1)
        sub_header = (bank_data[current_word] >> 28) & 0x3
        chan = (bank_data[current_word] >> 16) & 0x3F  # Need to grab channel and trigger flag and combine together

        if (chan < MAX_MDPP16_CHANNELS) and (sub_header == 1):  # Less than 16
            # Note that I'm rounding the pulse_height.  These come in as decimals but I don't see a point in keeping it that way
            # I will probably add a command line switch for this or maybe not.. best laid plans and what not.. -jonr
            adc_value = round((bank_data[current_word] >> 0) & 0xFFFF)
            myparticle_events.append({"chan": (chan + MDPP16_CHAN_PREFIX), "pulse_height": adc_value})
            event_count = event_count + 1

            #print("Chan:", chan, "ADC:", adc_value)
        elif sub_header == 2:
            high_ts = (bank_data[current_word] >> 0) & 0xFFFF
            #print("High TS:", high_ts)

        if show_all_data is True:
            print("   ----Event----")
            print("     Sig : %i,  Sub: %i, Channel : %i, - ADC Value : %i  - TDC Value : %i" % (data_sig, sub_header, chan, adc_value, tdc_value))
    # Set values to object to return, remember we are using a prefix of +100 for MDPP16 channel addressing
    if (low_ts != -1) and (high_ts != -1):
        timestamp = low_ts + (high_ts*2**30)
        #print("High TS:", high_ts)
#        print("Timestamp:", timestamp)

    if show_event is True:
        print("   ----Event----")
        print("     Sig : %i,  Sub: %i, Channel : %i, - trigChan: %i, - ADC Value : %i  - TDC Value : %i" % (data_sig, sub_header, chan, trigchan, adc_value, tdc_value))
    return myparticle_events, timestamp, event_count


def read_all_bank_events(bank_data):
    particle_events_list = []
    new_particle_events = []
    flags = 0

    # num_words = read_header(bank_data[0], False)
    new_particle_events, timestamp, event_count = read_words_for_events(bank_data[1:], False)

    for event in new_particle_events:
        particle_events_list.append({'timestamp': timestamp, 'chan': event['chan'], 'pulse_height': event['pulse_height'], 'flags': flags})

    return particle_events_list
