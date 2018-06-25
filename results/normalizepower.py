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
dynamic = np.array([])
leakage = np.array([])
total = np.array([])
noc = np.array([])
die = np.array([])
with open("resultspower", "rt") as f:
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
                    dynamic = np.append(dynamic,[float(split[0])])
                    leakage = np.append(leakage,[float(split[1])])
                    noc = np.append(noc,[float(split[2])])
                    die = np.append(die,[float(split[3])])
                elif len(split) == 2:
                    idx.append(line.strip())
total = dynamic+leakage
mi = mindex(total)
dynamic = dynamic / total[mi]
leakage = leakage / total[mi]

print "dynamic:"
for (i, e) in enumerate(dynamic):
    print idx[i]
    print round(e,2)
print

print "leakage:"
for (i, e) in enumerate(leakage):
    print idx[i]
    print round(e,2)
print

print "noc:"
for (i, e) in enumerate(norm(noc)):
    print idx[i]
    print round(e,2)
print

print "die:"
for (i, e) in enumerate(norm(die)):
    print idx[i]
    print round(e,2)
print


