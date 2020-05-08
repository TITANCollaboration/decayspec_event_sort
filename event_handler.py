import operator


def sort_events(particle_event_list):
    print("I'm going to sort eventS! it's all very exciting!")
    particle_event_list = sorted(particle_event_list, key=operator.itemgetter('timestamp'))
    # Do something else here I'm guessing...
    return particle_event_list
