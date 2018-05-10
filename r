#!/usr/bin/env bash
#
# Script for running Garnet_standalone simulations
#
# Usage: ./r n_cpus n_rows topology_py_file routing_algorithm \
#            flit_injection_rate synthetic_traffic_type n_cycles
#
#                 n_cpus: number of cpu's
#                 n_rows: number of rows in the topology structure
#       topology_py_file: name of the .py-file in configs/topologies/
#      routing_algorithm: routing algorithm in network, implemented in
#                         src/mem/ruby/network/garnet2.0/RoutingUnit.cc:
#                         0: Weight-based table
#                         1: XY (for Mesh)
#                         2: Random (custom)
#                         3: Adaptive (custom)
#    flit_injection_rate: traffic injection rate in packets/node/cycle
# synthetic_traffic_type: uniform_random, tornado, bit_complement, bit_reverse,
#                         bit_rotation, neighbor, shuffle, transpose
#               n_cycles: total number of cycles for which the simulation should run

# Defaults:
HIDEWARNERR=0           # Bool: hide warnings and errors
GARNETDEBUG=1           # Bool: enable Ruby/Garnet2.0 debug printing
NVCS=4                  # Number of virtual channels (VC) per virtual network
LINKWIDTHBITS=32        # Width in bits for all links inside the network
DEADLOCKTHRESHOLD=500     # Network-level deadlock threshold
NCPU=16
NROWS=2
TOPO=Ring
IJRATE=0.2
ROUTINGALGO=0
SYNTH=uniform_random
NCYCLES=10000

# Send between specific router id's. -1: disable
SENDER_ID=-1
DEST_ID=-1


if [ "$#" -gt 0 ] && [[ $1 =~ ^[0-9]+$ ]]; then
    NCPU=$1
else
    # Print help info
    sed -n "3,20p" r
    exit
fi
if [ "$#" -gt 1 ]; then
    NROWS=$2
fi
if [ "$#" -gt 2 ]; then
    TOPO=$3
fi
if [ "$#" -gt 3 ]; then
    ROUTINGALGO=$4
fi
if [ "$#" -gt 4 ]; then
    IJRATE=$5
fi
if [ "$#" -gt 5 ]; then
    SYNTH=$6
fi
if [ "$#" -gt 6 ]; then
    NCYCLES=$7
fi

# Suffix output dir name with routing algorithm
case "$ROUTINGALGO" in
    0) RALGNAME=weighted_table_routing ;;
    1) RALGNAME=mesh_xy_routing ;;
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

if [ $HIDEWARNERR -eq 1 ]; then
    HIDEWARNERR="-e --stderr-file=/dev/null"
else
    HIDEWARNERR=""
fi

if [ $GARNETDEBUG -eq 1 ]; then
    GARNETDEBUG="--debug-flags=RubyNetwork,GarnetSyntheticTraffic"
else
    GARNETDEBUG=""
fi


SEND_TO=""
if [ ! $SENDER_ID -eq -1 ]; then
    SEND_TO+="--single-sender-id=$SENDER_ID"
fi
if [ ! $DEST_ID -eq -1 ]; then
    SEND_TO+=" --single-dest-id=$DEST_ID"
fi

# Set environment variable for recognizing simulation type in gem5 .py-files
export GEM5SIMTYPE=GarnetStandalone

./build/NULL/gem5.debug -v $GARNETDEBUG $HIDEWARNERR -d $OUTDIR configs/example/garnet_synth_traffic.py \
--network=garnet2.0 \
--num-cpus=$NCPU \
--num-dirs=$NCPU \
--topology=$TOPO \
--mesh-rows=$NROWS \
--sim-cycles=$NCYCLES \
--injectionrate=$IJRATE \
--synthetic=$SYNTH \
--routing-algorithm=$ROUTINGALGO \
--link-width-bits=$LINKWIDTHBITS \
--vcs-per-vnet=$NVCS \
--buffers-per-data-vc=8 \
--buffers-per-ctrl-vc=2 \
--garnet-deadlock-threshold=$DEADLOCKTHRESHOLD \
--inj-vnet=0 \
--tikz $SEND_TO

python getnetworkstats.py $OUTDIR
