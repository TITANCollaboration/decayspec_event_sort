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
    print("hi")
    return


def main():

    parser = argparse.ArgumentParser(description='Histogram Generator')

    parser.add_argument('--redis_host', dest='redis_hostname', required=False,
                        help="Redis Hostname")
    parser.add_argument('--redis_port', dest='redis_port', required=False,
                        help="Redis port")

    args, unknown = parser.parse_known_args()
    parse_and_run(args)
    return


if __name__ == "__main__":
    main()
