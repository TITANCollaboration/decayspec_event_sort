#!/home/vagrant/anaconda3/envs/pyuproot36/bin/pypy3
# *************************************************************************************
# * Written by : Jon Ringuette
# * Started : May 18th 2021 - yup, still during the plague..
# * Purpose : Pull data from MIDAS online analyzer via REDIS and display time based histograms
#  * Requirements : Python 3, matplotlib, redis, json,  probably something other stuff numpy,scipy...
# *************************************************************************************

import argparse
from lib.temporal_histogram_generator import temporal_histogram_generator


def parse_and_run(args):
    my_online_hist = temporal_histogram_generator(channel=args.channel,
                                                  pulse_height_bin_min=int(args.pulse_height_bin_min),
                                                  pulse_height_bin_max=int(args.pulse_height_bin_max),
                                                  heatmap_type=args.heatmap_type)
    # my_online_hist.display_heatmap()
    if args.heatmap_type == "voltage_v_time":
        my_online_hist.online_voltage_vs_time_heatmap()
    elif args.heatmap_type == "energy_v_time":
        my_online_hist.online_energy_vs_time_heatmap()

    # print(my_online_hist.get_redis_hist_entry()['unix_ts_ms'])
    # print(my_online_hist.get_redis_queue_length())
    # print(my_online_hist.drain_redis_queue())
    return


def main():
    parser = argparse.ArgumentParser(description='Histogram Generator')

    parser.add_argument('--redis_host', dest='redis_hostname', required=False,
                        help="Redis Hostname")
    parser.add_argument('--redis_port', dest='redis_port', required=False,
                        help="Redis port")
    parser.add_argument('--redis_queue', dest='redis_queue', required=False,
                        help="Redis queue")
    parser.add_argument('--heatmap_type', dest='heatmap_type', default="voltage_v_time", required=False,
                        help="Heatmap Types: voltage_v_time, energy_v_time")
    parser.add_argument('--channel', dest='channel', type=int, default=0, required=False,
                        help="ADC channel # to graph (0-15 for MDPP16)")
    parser.add_argument('--ph_bin_min', dest='pulse_height_bin_min', type=int, default=0, required=False,
                        help="Minimum bin # to count towards hit in heatmap (Range: 0-2048)")
    parser.add_argument('--ph_bin_max', dest='pulse_height_bin_max', type=int, default=2048, required=False,
                        help="Maxmum bin # to count towards hit in heatmap (Range: 0-2048)")

    args, unknown = parser.parse_known_args()
    parse_and_run(args)
    return


if __name__ == "__main__":
    main()
