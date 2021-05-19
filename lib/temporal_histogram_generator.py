###################################################
# Library to read in temporal histogram data from REDIS and display in real(ish) time
###################################################

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import redis
import json


class temporal_histogram_generator:
    def __init__(self, redis_hostname="localhost", redis_port="6379", redis_queue='mdpp16:queue', channel=0,
                 pulse_height_bin_min=0, pulse_height_bin_max=2048, egun_voltage_min=2000, egun_voltage_max=2700
                 egun_voltage_step_size=10):
        self.redis_hostname = redis_hostname
        self.redis_port = redis_port
        self.redis_queue = redis_queue
        self.channel = channel
        self.pulse_height_bin_min = pulse_height_bin_min
        self.pulse_height_bin_max = pulse_height_bin_max

        try:
            self.queue_conn = redis.Redis(host=self.redis_hostname, port=self.redis_port)
        except:
            print("Failed to connect to REDIS server")
            exit(0)
        return

    def get_queue_length(self):
        queue_length = self.queue_conn.llen(self.redis_queue)
        return queue_length

    def get_hist_entry_from_queue(self):
        json_from_queue = self.queue_conn.lpop(self.redis_queue)
        myval = json.loads(json_from_queue)  # Decode the JSON contained in the queue entry into list
        return myval

    def drain_queue(self):
        current_queue_length = 2 # self.get_queue_length(()  # Set this back after testing...
        queue_contents = []
        for queue_entry_index in range(0, current_queue_length):
            queue_contents.append(self.get_hist_entry_from_queue())
        return queue_contents

#  channel, TDC, unix_TS, histogram
