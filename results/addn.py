#!/usr/bin/python2
import sys
import os
import numpy as np

if len(sys.argv) < 1:
    sys.exit(0)

dirname = sys.argv[1]

found = False
idx = []
dynamic = 0.0
leakage = 0.0
total = np.array([])
noc = np.array([])
die = np.array([])
with open(os.path.join(dirname, "ext.txt"), "rt") as f:
    for line in f:
        if len(line) >= 2:
            split = line.split()

            if len(split) == 3:
                if split[0] == "Dynamic":
                    dynamic += float(split[2])
                elif split[0] == "Leakage":
                    leakage += float(split[2])

print "dynamic:", dynamic
print "leakage:", leakage
