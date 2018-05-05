#!/usr/bin/env bash
#
# Script for running Garnet_standalone

HIDEWARNERR=0
NCPU=16
NROWS=4
TOPO=Ring
IJRATE=0.2
SYNTH=uniform_random
NCYCLES=10

if [ "$#" -gt 0 ]; then
    NCPU=$1
fi
if [ "$#" -gt 1 ]; then
    NROWS=$2
fi
if [ "$#" -gt 2 ]; then
    TOPO=$3
fi
if [ "$#" -gt 3 ]; then
    IJRATE=$4
fi
if [ "$#" -gt 4 ]; then
    SYNTH=$5
fi

NCOLS=$(($NCPU/$NROWS))
OUTDIR="m5out/"$TOPO-$NCPU"core-"$NROWS"x"$NCOLS-$SYNTH-$IJRATE

# Generate output dir name
if [ -d $OUTDIR ]; then
    MAXOUTDIRS=50
    for ((i=2;i<=MAXOUTDIRS;i++)); do
        NOUTDIR=$OUTDIR"-"$i
        if [ ! -d $NOUTDIR ]; then
            OUTDIR=$NOUTDIR
            break
        fi
    done
fi

# Hide warnings and errors?
if [ $HIDEWARNERR -eq 1 ]; then
    SUPP="-e --stderr-file=/dev/null"
else
    SUPP=""
fi

# Set environment variable for writing extra output files like topology.png
export GEM5OUTDIR=$OUTDIR

./build/NULL/gem5.debug $SUPP -d $OUTDIR configs/example/garnet_synth_traffic.py \
--network=garnet2.0 \
--num-cpus=$NCPU \
--num-dirs=$NCPU \
--topology=$TOPO \
--mesh-rows=$NROWS \
--sim-cycles=$NCYCLES \
--injectionrate=$IJRATE \
--synthetic=$SYNTH \
--tikz
