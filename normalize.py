#!/usr/bin/python2
import sys
import numpy as np

if len(sys.argv) < 1:
    sys.exit(0)

def norm(a):
    mini = 1e12
    for e in a:
        if e < mini:
            mini = e
    return a / mini

cores = sys.argv[1]

found = False
idx = []
throughput = np.array([])
latency = np.array([])
with open("results", "rt") as f:
    for line in f:
        if len(line) >= 2:
            if line[-2] == ':':
                if found:
                    break
                if line[0:-2] == cores:
                    found = True

            if found:
                split = line.split()

                if len(split) == 3:
                    throughput = np.append(throughput,[float(split[0])])
                    latency = np.append(latency,[float(split[2])])
                elif len(split) == 2:
                    idx.append(line.strip())


print "Latencies:"
for (i, e) in enumerate(norm(latency)):
    print idx[i]
    print round(e,2)
print


print "Throughputs:"
for (i, e) in enumerate(norm(throughput)):
    print idx[i]
    print round(e,2)
print

