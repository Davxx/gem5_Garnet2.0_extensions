SCRIPTS_DIR:=$(dir $(realpath $(lastword $(MAKEFILE_LIST))))
TOOLS_DIR:=$(dir $(SCRIPTS_DIR:%/=%))
export BENCHMARKS_ROOT:=/home/dav/gem5/sniper_splash2
export SNIPER_ROOT:=/home/dav/gem5/
export GRAPHITE_ROOT:=/home/dav/gem5/
