#!/usr/bin/env bash
#
# Script for running Garnet_standalone

HIDEWARNERR=0
NCPU=16
NROWS=2
TOPO=Ring
IJRATE=0.2
ROUTINGALGO=0
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
    ROUTINGALGO=$5
fi
if [ "$#" -gt 5 ]; then
    SYNTH=$6
fi

# Supplement output dir name with routing algorithm
case "$ROUTINGALGO" in
    0) RALGNAME=weighted_table_routing ;;
    1) RALGNAME=mesh_xy ;;
    2) RALGNAME=random_routing ;;
    3) RALGNAME=adaptive_routing ;;
    *) RALGNAME=unknown_routing ;;
esac

NCOLS=$(($NCPU/$NROWS))
OUTDIR="m5out/"$TOPO-$NCPU"core-"$NROWS"x"$NCOLS-$SYNTH-$IJRATE-$RALGNAME

# Generate output dir name
if [ -d $OUTDIR ]; then
    MAXOUTDIRS=99
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

# ‘uniform_random’, ‘tornado’, ‘bit_complement’, ‘bit_reverse’, ‘bit_rotation’, ‘neighbor’, ‘shuffle’, and ‘transpose’.

./build/NULL/gem5.debug --dot-config=config.dot $SUPP -d $OUTDIR configs/example/garnet_synth_traffic.py \
--network=garnet2.0 \
--num-cpus=$NCPU \
--num-dirs=$NCPU \
--topology=$TOPO \
--mesh-rows=$NROWS \
--sim-cycles=$NCYCLES \
--injectionrate=$IJRATE \
--synthetic=$SYNTH \
--routing-algorithm=$ROUTINGALGO \
--link-width-bits=32 \
--vcs-per-vnet=4 \
--inj-vnet=0 \
--tikz

python getnetworkstats.py $OUTDIR
