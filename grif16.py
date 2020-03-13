def read_header(bank0data, show_header=True):

    hsig  = (bank0data >> 30) & 0x3
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


def read_event(bank_data, show_event=True):
    adc_value = -1
    chan = (bank_data >> 16) & 0x1F
    if chan < MAX_MDPP16_CHANNELS:
        adc_value = (bank_data >> 0) & 0xFFFF

    if show_event is True:
        print("----Event----")
        print("Channel : %i,  - ADC Value : %i" % (chan, adc_value))
        print("-------------")
