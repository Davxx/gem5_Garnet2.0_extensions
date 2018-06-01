#!/usr/bin/python2
#
# Plot latency numbers for simulation stats in outdir to latency_file

import os
import sys

## Parse stats.txt for the specified key and return the associated value as float
def getStatsForString(stats_file, key):
    with open(stats_file, "rt") as f:
        for line in f:
            if key in line:
                split = line.split()
                return float(split[-1])
    return 0.0

if len(sys.argv) < 4:
    print("Usage: %s <simulation directory> " \
          "<latency output file> <injection rate>" % sys.argv[0])

outdir = sys.argv[1]
latency_file = sys.argv[2]
injrate = float(sys.argv[3])
stats_file = os.path.join(outdir, "stats.txt")
latest_latency_file = os.path.join(outdir, "../latest_latency.txt")

latency = getStatsForString(stats_file, "system.ruby.network.average_packet_latency")

if latency > -1:
    with open(latency_file, "a") as f:
        f.write("{0:f}   {1:f}\n".format(injrate, latency))

    with open(latest_latency_file, "w") as f:
        f.write("{0:d}".format(int(latency)))
