import operator


class event_handler:
    def __init__(self, sort_type, event_length, event_extra_gap, max_hits_per_event):
        self.sort_type = sort_type
        # self.event_queue =
        self.event_length = event_length
        self.event_extra_gap = event_extra_gap
        self.max_hits_per_event = max_hits_per_event

        # events = event_handler(self.sort_type, event_queue, self.EVENT_LENGTH, self.EVENT_EXTRA_GAP, self.MAX_HITS_PER_EVENT)
    def sort_events(self, event_queue, particle_hit_list):
        if self.sort_type == 'event':
            self.sort_event_based(event_queue, particle_hit_list)
        elif self.sort_type =='raw':
            print("RAW output selected")
            self.raw_sorter(event_queue, particle_hit_list)
        else:
            print("Could not finding an appropriate sorter.  The specified one was:", self.sort_type)
        return

    def raw_sorter(self, event_queue, particle_event_list):
        # This is mostly a dummy function
        print("Performing Raw Sorting...")
        event_queue.put(particle_event_list)
        return

    def sort_event_based(self, event_queue, particle_hit_list):
        print("Performing Event Based Sorting...")
        particle_event_list = []
        particle_hit_list = sorted(particle_hit_list, key=operator.itemgetter('timestamp'))
        for particle_hit in particle_hit_list:
            if not particle_event_list:
                event_hit_count = 1
                particle_event_list.append({'pulse_height': [particle_hit['pulse_height']], 'chan': [particle_hit['chan']], 'timestamp': particle_hit['timestamp'], "hit_count": 1})
            # check if the timestamp is in the range of a temporal event and that we aren't seeing the event from the same detector, this might get weird and maybe we should care
            # as it could have an impact on events after it..
            elif ((particle_hit['timestamp'] - particle_event_list[-1]['timestamp']) < (self.event_length + self.event_extra_gap)): # and (particle_hit['chan'] not in particle_event_list[-1]['chan']):
                event_hit_count = event_hit_count + 1
                particle_event_list[-1]['pulse_height'].append(particle_hit['pulse_height'])
                particle_event_list[-1]['chan'].append(particle_hit['chan'])
                particle_event_list[-1]['hit_count'] = event_hit_count
            else:
                event_hit_count = 1
                particle_event_list.append({'pulse_height': [particle_hit['pulse_height']], 'chan': [particle_hit['chan']], 'timestamp': particle_hit['timestamp'], 'hit_count': event_hit_count})
        event_queue.put(particle_event_list)
        return
