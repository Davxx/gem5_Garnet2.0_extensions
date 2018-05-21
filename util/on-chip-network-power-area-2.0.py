#!/usr/bin/python2
#
# Copyright (c) 2014 Mark D. Hill and David A. Wood
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Modified by David Smelt for Garnet2.0


import string, sys, subprocess, os
from ConfigParser import ConfigParser
from collections import Counter

# Compile DSENT to generate the Python module and then import it.
# This script assumes it is executed from the gem5 root.
print("Attempting compilation")
from subprocess import call

src_dir = 'ext/dsent'
build_dir = 'build/ext/dsent'

if not os.path.exists(build_dir):
    os.makedirs(build_dir)
os.chdir(build_dir)

error = call(['cmake', '../../../%s' % src_dir])
if error:
    print("Failed to run cmake")
    exit(-1)

error = call(['make'])
if error:
    print("Failed to run make")
    exit(-1)

print("Compiled dsent")
os.chdir("../../../")
sys.path.append("build/ext/dsent")
import dsent

# Parse gem5 config.ini file for the configuration parameters related to
# the on-chip network.
def parseConfig(config_file):
    config = ConfigParser()
    if not config.read(config_file):
        print("ERROR: config file '", config_file, "' not found")
        sys.exit(1)

    if not config.has_section("system.ruby.network"):
        print("ERROR: Ruby network not found in ", config_file)
        sys.exit(1)

    if config.get("system.ruby.network", "type") != "GarnetNetwork" :
        print("ERROR: Garnet network not used in ", config_file)
        sys.exit(1)

    number_of_virtual_networks = config.getint("system.ruby.network",
                                               "number_of_virtual_networks")
    vcs_per_vnet = config.getint("system.ruby.network", "vcs_per_vnet")

    buffers_per_data_vc = config.getint("system.ruby.network",
                                        "buffers_per_data_vc")
    buffers_per_control_vc = config.getint("system.ruby.network",
                                           "buffers_per_ctrl_vc")

    ni_flit_size_bits = 8 * config.getint("system.ruby.network",
                                          "ni_flit_size")

    # Get num_cycles for one of four possible config.ini:[system.cpu????] 
    # formats
    num_cycles = 0
    if config.has_section("system.cpu0"):
        num_cycles = config.getint("system.cpu0", "sim_cycles")
    elif config.has_section("system.cpu00"):
        num_cycles = config.getint("system.cpu00", "sim_cycles")
    elif config.has_section("system.cpu000"):
        num_cycles = config.getint("system.cpu000", "sim_cycles")
    elif config.has_section("system.cpu0000"):
        num_cycles = config.getint("system.cpu0000", "sim_cycles")
    
    assert(num_cycles > 0)

    routers = config.get("system.ruby.network", "routers").split()
    int_links = config.get("system.ruby.network", "int_links").split()
    ext_links = config.get("system.ruby.network", "ext_links").split()

    return (config, number_of_virtual_networks, vcs_per_vnet,
            buffers_per_data_vc, buffers_per_control_vc, ni_flit_size_bits,
            num_cycles, routers, int_links, ext_links)

## Get clock for the given object
def getClock(obj, config):
    if config.get(obj, "type") == "SrcClockDomain":
        return config.getint(obj, "clock")

    if config.get(obj, "type") == "DerivedClockDomain":
        source = config.get(obj, "clk_domain")
        divider = config.getint(obj, "clk_divider")
        return getClock(source, config)  / divider

    source = config.get(obj, "clk_domain")
    return getClock(source, config)

## Return the key index of known result strings to order known result strings
## for more intuitive printing
def getResultKey(s):
    key_order = ["Buffer/Dynamic", "Buffer/Leakage", "Crossbar/Dynamic",
                 "Crossbar/Leakage", "Switch allocator/Dynamic",
                 "Switch allocator/Leakage", "Clock/Dynamic",
                 "Clock/Leakage", "Total/Dynamic", "Total/Leakage",
                 "Area/Buffer", "Area/Crossbar", "Area/Switch allocator",
                 "Area/Other", "Area/Total"]
    for (i, key) in enumerate(key_order):
        if key in s:
            return i
    return -1

## Compute the power consumed by the given int_links
def computeIntLinkPower(int_links, stats_file, config, num_links=1e9):
    power = None
    for (i, link) in enumerate(int_links):
        if i + 1 > num_links:
            break

        frequency = getClock(link + ".network_link", config)
        injrate = 1

        if num_links == 1:
            print("\nSingle link power:")
        else:
            print("\n%s.network_link power: " % link)
        
        power = dsent.computeLinkPower(frequency, injrate)

    # Return latest result
    return power

## Compute the power consumed by the given ext_links
def computeExtLinkPower(ext_links, stats_file, config, num_links=1e9):
    power = None
    i = 1
    for link in ext_links:
        if i > num_links:
            break

        frequency = getClock(link + ".network_links0", config)

        if num_links == 1:
            print("\nSingle link power:")
        else:
            print("\n%s.network_links0 power: " % link)

        power = dsent.computeLinkPower(frequency)
        i += 1

        if i > num_links:
            break

        frequency = getClock(link + ".network_links1", config)
        print("\n%s.network_links1 power: " % link)

        power = dsent.computeLinkPower(frequency)
        i += 1

    # Return latest result
    return power

## Compute total link power consumption, assuming that each link has a power
## model equal to single_link_power
def computeTotalLinkPower(num_cycles, int_links, ext_links, stats_file, config):

    # Compute the power consumed by a single link, since all links
    # currently have the same power model
    dsent_out = computeIntLinkPower(int_links, stats_file, config, num_links=1)
    single_link_power = dict(dsent_out)


    num_int_links = len(int_links)
    num_ext_links = len(ext_links)
    total_num_links = num_int_links + num_ext_links
    single_dynamic = 0.0
    single_leakage = 0.0

    # Get power consumption for a single link
    for k, v in single_link_power.iteritems():
        if "Dynamic" in k:
            single_dynamic = v
        elif "Leakage" in k:
            single_leakage = v
    print single_dynamic
    print single_leakage
    print num_cycles
    print("\nTotal number of links: %d" % total_num_links)
    print("Total link power for %d bidirectional int_links and %d bidirectional ext_links:"
          % (len(int_links) / 2, len(ext_links) / 2))

    flits_injected = getStatsForString(stats_file, "system.ruby.network.flits_injected::total")
    ext_in_link_utilization = getStatsForString(stats_file, "system.ruby.network.ext_in_link_utilization")
    ext_out_link_utilization = getStatsForString(stats_file, "system.ruby.network.ext_out_link_utilization")
    int_link_utilization = getStatsForString(stats_file, "system.ruby.network.int_link_utilization")
    ext_link_utilization = ext_in_link_utilization + ext_out_link_utilization

    flits_per_cycle = flits_injected / float(num_cycles)
    print flits_injected, flits_per_cycle

## Compute the power and area used for all routers
def computeRouterPowerAndArea(routers, stats_file, config, int_links, ext_links,
                              number_of_virtual_networks, vcs_per_vnet,
                              buffers_per_data_vc, buffers_per_control_vc,
                              ni_flit_size_bits, num_cycles):
    results = []
    num_keys = 15
    sum_strings = [""] * num_keys
    avg_strings = [""] * num_keys

    for router in routers:
        frequency = getClock(router, config)

        # Count number of ports for this router
        nports = 0
        for int_link in int_links:
            if config.get(int_link, "src_node") == router or \
               config.get(int_link, "dst_node") == router:
               nports += 1

        for ext_link in ext_links:
            if config.get(ext_link, "int_node") == router:
               nports += 1

        # All ports are bidirectional
        nports /= 2

        # Calculate injection rate (number of flits per cycle per port) for
        # this router, based on stats
        flits_injected = getStatsForString(stats_file, "system.ruby.network.flits_injected::total")
        flits_per_cycle = flits_injected / float(num_cycles)
        buf_injrate = 1.5
        xbar_injrate = 1.5
        sa_injrate = 1.5

        # Print results, overwriting relevant parameters, for this router
        print("\n%s:" % router)
        dsent_out = dsent.computeRouterPowerAndArea(
                         frequency, nports, nports, 
                         buf_injrate, xbar_injrate, sa_injrate,
                         number_of_virtual_networks, vcs_per_vnet,
                         buffers_per_control_vc, buffers_per_data_vc,
                         ni_flit_size_bits)
        results.append(dict(dsent_out))

    # Calculate sum for all routers
    result_sum = Counter()
    for d in results:
        result_sum.update(d)
    result_sum = dict(result_sum)
    
    # Calculate average for all routers
    result_average = {}
    for k, v in result_sum.iteritems():
        result_average[k] = v / float(len(routers))

    # Generate output strings in the correct order
    for k, v in result_sum.iteritems():
        sum_strings[getResultKey(k)] = str(k) + str(v)
    for k, v in result_average.iteritems():
        avg_strings[getResultKey(k)] = str(k) + str(v)

    # Print sum and average
    print("\nAverages for all %d routers:" % len(routers))
    print("\n".join(avg_strings))
    print("\nSum totals for all %d routers:" % len(routers))
    print("\n".join(sum_strings))

## Parse stats.txt for the specified key and return the associated value as float
def getStatsForString(stats_file, key):
    with open(stats_file, "rt") as f:
        for line in f:
            if key in line:
                split = line.split()
                return float(split[-1])
    return 0

## Parse gem5 stats.txt file
def parseStats(stats_file, config, router_config_file, link_config_file,
               routers, int_links, ext_links, number_of_virtual_networks,
               vcs_per_vnet, buffers_per_data_vc, buffers_per_control_vc,
               ni_flit_size_bits, num_cycles):

    # Initialize DSENT with router base configuration file
    dsent.initialize(router_config_file)

    # Compute the power consumed by the routers
    computeRouterPowerAndArea(routers, stats_file, config, int_links,
                              ext_links, number_of_virtual_networks,
                              vcs_per_vnet, buffers_per_data_vc,
                              buffers_per_control_vc, ni_flit_size_bits,
                              num_cycles)

    # Finalize DSENT
    dsent.finalize()

    # Initialize DSENT with link base configuration file
    dsent.initialize(link_config_file)

    # Compute total link power consumption
    computeTotalLinkPower(num_cycles, int_links, ext_links, stats_file, config)

    # Finalize DSENT
    dsent.finalize()


# This script parses the config.ini and the stats.txt from a run and
# generates the power and the area of the on-chip network using DSENT
def main():
    if len(sys.argv) < 2:
        print("Usage: %s <simulation directory> " \
              "<router config file> <link config file>" % sys.argv[0])
        print("If unspecified, <router config file> will default to " \
              "<simulation directory>/router.cfg and")
        print("<link config file> will default to " \
              "<simulation directory>/electrical-link.cfg")
        exit(2)

    print("WARNING: configuration files for DSENT and McPAT are separate. " \
          "Changes made to one are not reflected in the other.")

    cfg_str = os.path.join(sys.argv[1], "config.ini")
    stats_str = os.path.join(sys.argv[1], "stats.txt")

    (config, number_of_virtual_networks, vcs_per_vnet, buffers_per_data_vc,
     buffers_per_control_vc, ni_flit_size_bits, num_cycles, routers, int_links,
     ext_links) = parseConfig(cfg_str)

    router_cfg = os.path.join(sys.argv[1], "router.cfg")
    link_cfg = os.path.join(sys.argv[1], "electrical-link.cfg")

    if len(sys.argv) > 2:
        router_cfg = sys.argv[2]
    if len(sys.argv) > 3:
        link_cfg = sys.argv[3]

    parseStats(stats_str, config, router_cfg, link_cfg, routers, int_links, ext_links,
               number_of_virtual_networks, vcs_per_vnet, buffers_per_data_vc,
               buffers_per_control_vc, ni_flit_size_bits, num_cycles)

if __name__ == "__main__":
    main()
