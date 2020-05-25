import operator


def sort_events(event_queue, particle_hit_list, event_length, event_extra_gap, max_hits_per_event):
    particle_event_list = []
    particle_hit_list = sorted(particle_hit_list, key=operator.itemgetter('timestamp'))
    for particle_hit in particle_hit_list:
        #event_hit_count = 0
        if not particle_event_list:
            event_hit_count = 1
            particle_event_list.append({'pulse_height': [particle_hit['pulse_height']], 'chan': [particle_hit['chan']], 'timestamp': particle_hit['timestamp'], "hit_count": 1})
        # check if the timestamp is in the range of a temporal event and that we aren't seeing the event from the same detector, this might get weird and maybe we should care
        # as it could have an impact on events after it..
        elif ((particle_hit['timestamp'] - particle_event_list[-1]['timestamp']) < (event_length + event_extra_gap)): # and (particle_hit['chan'] not in particle_event_list[-1]['chan']):
            event_hit_count = event_hit_count + 1
            particle_event_list[-1]['pulse_height'].append(particle_hit['pulse_height'])
            particle_event_list[-1]['chan'].append(particle_hit['chan'])
            particle_event_list[-1]['hit_count'] = event_hit_count
        else:
            event_hit_count = 1
            particle_event_list.append({'pulse_height': [particle_hit['pulse_height']], 'chan': [particle_hit['chan']], 'timestamp': particle_hit['timestamp'], 'hit_count': event_hit_count})
    event_queue.put(particle_event_list)
    return
