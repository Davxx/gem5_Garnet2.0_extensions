#!/usr/bin/python2
#
# Script for parsing Garnet_standalone stats.txt

import shutil
import os
import sys

if len(sys.argv) > 1:
    if not os.path.isdir(sys.argv[1]):
        sys.exit(1)
else:
    sys.exit(1)

in_file_name = os.path.join(sys.argv[1], "stats.txt")
out_file_name = os.path.join(sys.argv[1], "network_stats.txt")

if os.path.isfile(in_file_name):
    with open(in_file_name, "rt") as fin:
        line = ""
        while True:
            line = fin.readline()
            if not line:
                break
            elif "system.ruby.network.packets_received" in line:
                with open(out_file_name, "wt") as fout:
                    shutil.copyfileobj(fin, fout)
                    break
