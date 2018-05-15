#!/usr/bin/python2
#
# Script for parsing GarnetStandalone debug prints

import ntpath
import subprocess
import sys

# Options
in_file = "debug.txt" # default file name in case no args supplied
greps = ["command line:", "vc_busy_counter"]
mixed_greps = False
sorting = True


def exit_verbose(s):
    print s
    sys.exit(1)

if len(sys.argv) > 1:
    in_file = sys.argv[1]
    if not ntpath.isfile(in_file):
        exit_verbose("File {0} does not exist.".format(in_file))
else:
    exit_verbose("Usage: ./grepdebug.py filename")

dir_name, base_name = ntpath.split(in_file)
fn, ext = ntpath.splitext(base_name)
if len(dir_name) > 0:
    dir_name += "/"

out_file = ntpath.join(dir_name, fn + "_parsed" + ext) 
out_file_sorted = ntpath.join(dir_name, fn + "_parsed_sorted" + ext)

with open(in_file, "rt") as fin, open(out_file, "wt") as fout:
    if mixed_greps:
         for line in fin:
            for grep in greps:
                if grep in line:
                    fout.write(line)
                    break
    else:
        for grep in greps:
            for line in fin:
                if grep in line:
                    fout.write(line)
            fin.seek(0)
    print "Parsed debug info written to: " + out_file

if sorting:
    proc = subprocess.Popen("sort -rV " + out_file + " -o " + out_file_sorted,
                            shell=True)
    proc.wait()
    print "Sorted debug info written  to: " + out_file_sorted
