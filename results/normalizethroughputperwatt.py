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

def mindex(a):
    mini = 1e12
    x = 0
    for (i, e) in enumerate(a):
        if e < mini:
            mini = e
            x = i
    return x


cores = sys.argv[1]

found = False
idx = []
throughput = np.array([])
dynamic = np.array([])
leakage = np.array([])
power = np.array([])
area = np.array([])
throughput_per_watt = np.array([])
watt_per_area = np.array([])
with open("resultspower2", "rt") as f:
    for line in f:
        if len(line) >= 2:
            if line[-2] == ':':
                if found:
                    break
                if line[0:-2] == cores:
                    found = True

            if found:
                split = line.split()

                if len(split) == 4:
                    throughput = np.append(throughput,[float(split[0])])
                    dynamic = np.append(dynamic,[float(split[1])])
                    leakage = np.append(leakage,[float(split[2])])
                    area = np.append(area,[float(split[3])])
                elif len(split) == 2:
                    idx.append(line.strip())
power = dynamic+leakage
mi = mindex(power)
leakage_frac = leakage / (dynamic + leakage)
dynamic = dynamic / power[mi]
leakage = leakage / power[mi]
throughput_per_watt = throughput / power
throughput_per_core = np.array([])
watt_per_area = power / area

print "throughput:"
for (i, e) in enumerate(throughput):
    print idx[i]

    cores = idx[i].split("_")[0]
    throughput_per_core = np.append(throughput_per_core, [e / float(cores)])

    print round(e,2)
print

print "normalized throughput per core:"
for (i, e) in enumerate(norm(throughput_per_core)):
    print idx[i]
    print round(e,2)
print

print "normalized power:"
for (i, e) in enumerate(norm(power)):
    print idx[i]
    print round(e,2)
print

print "normalized area:"
for (i, e) in enumerate(norm(area)):
    print idx[i]
    print round(e,2)
print

print "throughput per watt:"
for (i, e) in enumerate(throughput_per_watt):
    print idx[i]
    print round(e,2)
print

print "watt per area:"
for (i, e) in enumerate(watt_per_area):
    print idx[i]
    print round(e,2)
print "\n\n"

print "normalized throughput per watt:"
for (i, e) in enumerate(norm(throughput_per_watt)):
    print idx[i]
    print round(e,2)
print

print "normalized watt per area:"
for (i, e) in enumerate(norm(watt_per_area)):
    print idx[i]
    print round(e,2)
print

print "leakage power frac:"
for (i, e) in enumerate(leakage_frac):
    print idx[i]
    print round(e,2)
print

