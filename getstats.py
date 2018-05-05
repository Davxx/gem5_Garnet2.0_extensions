#!/usr/bin/python2
#
# Script for parsing Garnet_standalone stats.txt

from itertools import ifilter

with open("/home/dav/gem5/m5out/HierarchicalRing-256core-16x16-uniform_random-0.02-2/stats.txt", "rt") as f,\
     open("/home/dav/gem5/m5out/HierarchicalRing-256core-16x16-uniform_random-0.02-2/network_stats.txt", "wt") as g:
        if "system.ruby.network.packets_received"
        g.writelines(ifilter(lambda line: "system.ruby.network.average" in line, f))
        g.writelines(ifilter(lambda line: "system.ruby.network.packet" in line, f))
        g.writelines(ifilter(lambda line: "system.ruby.network.packet" in line, f))

