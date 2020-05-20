import operator

#    myparticle_event = {"timestamp": tdc_value, "chan": (chan + MDPP16_CHAN_PREFIX), "pulse_height": adc_value, "flags": flags}
def sort_events(particle_hit_list, event_length, event_extra_gap, max_hits_per_event):
    particle_event_list = []
    particle_hit_list = sorted(particle_hit_list, key=operator.itemgetter('timestamp'))
    for particle_hit in particle_hit_list:
        if not particle_event_list:
            particle_event_list.append({'pulse_height': [particle_hit['pulse_height']], 'chan': [particle_hit['chan']], 'timestamp': particle_hit['timestamp']})
        # check if the timestamp is in the range of a temporal event and that we aren't seeing the event from the same detector, this might get weird and maybe we should care
        # as it could have an impact on events after it..
        elif ((particle_hit['timestamp'] - particle_event_list[-1]['timestamp']) < (event_length + event_extra_gap)): # and (particle_hit['chan'] not in particle_event_list[-1]['chan']):
            particle_event_list[-1]['pulse_height'].append(particle_hit['pulse_height'])
            particle_event_list[-1]['chan'].append(particle_hit['chan'])
        else:
            particle_event_list.append({'pulse_height': [particle_hit['pulse_height']], 'chan': [particle_hit['chan']], 'timestamp': particle_hit['timestamp']})

    return particle_event_list
