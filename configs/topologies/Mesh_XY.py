# Copyright (c) 2010 Advanced Micro Devices, Inc.
#               2016 Georgia Institute of Technology
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
# Authors: Brad Beckmann
#          Tushar Krishna
# Adapted by: David Smelt

import m5
from m5.params import *
from m5.objects import *

from BaseTopology import SimpleTopology
from TikzTopology import TikzTopology

class Mesh_XY(SimpleTopology):
    # Creates a generic Mesh assuming an equal number of cache
    # and directory controllers.
    # XY routing is enforced (using link weights)
    # to guarantee deadlock freedom.
    description='Mesh_XY'

    def __init__(self, controllers):
        self.nodes = controllers
        self.tikz_out = None

    def writeTikz(self, ln):
        # Writes Tikz topology code to file

        if not self.tikz_out is None:
            self.tikz_out.write(ln)

    def makeBiLink(self, src_id, dst_id, weight, src_outport, dst_inport, IntLink):
        # Makes a bidirectional link between self.routers src_id and dst_id

        if not (src_id, dst_id) in self.lst_links and not (dst_id, src_id) in self.lst_links:
            self.lst_links.append((src_id, dst_id))

            self.int_links.append(IntLink(link_id=self.link_count,
                                          src_node=self.routers[src_id],
                                          dst_node=self.routers[dst_id],
                                          src_outport=src_outport,
                                          dst_inport=dst_inport,
                                          latency=self.link_latency,
                                          weight=weight))
            self.int_links.append(IntLink(link_id=self.link_count + 1,
                                          src_node=self.routers[dst_id],
                                          dst_node=self.routers[src_id],
                                          src_outport=dst_inport,
                                          dst_inport=src_outport,
                                          latency=self.link_latency,
                                          weight=weight))

            thick_line = "line width=1mm" if weight == 1 else ""
            self.writeTikz("    ({0}) edge [{1}] node[] {{}} ({2})".format(src_id, thick_line, dst_id))
            self.link_count += 2

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes
        num_routers = options.num_cpus
        nrows = options.mesh_rows

        # Default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        self.link_latency = options.link_latency # used by simple and garnet
        router_latency = options.router_latency # only used by garnet

        # There must be an evenly divisible number of cntrls to routers
        # Also, obviously the number or rows must be <= the number of routers
        cntrls_per_router, remainder = divmod(len(nodes), num_routers)
        assert(nrows > 0 and nrows <= num_routers)
        ncols = int(num_routers / nrows)
        assert(ncols * nrows == num_routers)

        # Optionally generate Tikz topology code in 'output_directory/topo.tex' and
        # convert it to 'output_directory/topology.png'
        if options.tikz:
            self.tikz_out = TikzTopology(m5.options.outdir, nrows, ncols)

        # Create the routers in the mesh
        self.routers = [Router(router_id=i, latency = router_latency) for i in range(num_routers)]
        network.routers = self.routers

        # Link counter to set unique link ids
        self.link_count = 0

        # Add all but the remainder nodes to the list of nodes to be uniformly
        # distributed across the network.
        network_nodes = []
        remainder_nodes = []
        for node_index in xrange(len(nodes)):
            if node_index < (len(nodes) - remainder):
                network_nodes.append(nodes[node_index])
            else:
                remainder_nodes.append(nodes[node_index])

        # Connect each node to the appropriate router.
        # These should be of type L1Cache_Controllers or Directory_Controller
        ext_links = []
        for (i, node) in enumerate(network_nodes):
            cntrl_level, router_id = divmod(i, num_routers)
            assert(cntrl_level < cntrls_per_router)
            ext_links.append(ExtLink(link_id=self.link_count, ext_node=node,
                                     int_node=self.routers[router_id],
                                     latency=self.link_latency))
            self.link_count += 1

        # Connect the remaining nodes to router 0.
        # These should only be DMA nodes
        for (i, node) in enumerate(remainder_nodes):
            assert(node.type == 'DMA_Controller')
            assert(i < remainder)
            ext_links.append(ExtLink(link_id=self.link_count, ext_node=node,
                                     int_node=self.routers[0],
                                     latency=self.link_latency))
            self.link_count += 1

        network.ext_links = ext_links

        if not self.tikz_out is None:
            # Generate Tikz nodes

            for row in xrange(nrows):
                first_col = False

                for col in xrange(ncols):
                    r = col + (row * ncols)

                    if not first_col:
                        first_col = True

                        if row == 0:
                            self.writeTikz("    \\node[main node] (0) [below left=0cm] {0};")
                        else:
                            self.writeTikz("    \\node[main node] ({0}) [above of={{{1}}}] {{{2}}};".format(r,
                                           r - ncols, r))
                    else:
                        self.writeTikz("    \\node[main node] ({0}) [right of={{{1}}}] {{{2}}};".format(r, r - 1, r))

            self.writeTikz("\n    \\path[every node/.style={font=\\sffamily\\footnotesize},"
                           "every edge/.append style={line width=0.3mm}]")

        self.int_links = []
        self.lst_links = []

        # Create the mesh links.
        for row in xrange(nrows):
            for col in xrange(ncols):

                if (col + 1 < ncols):
                    # Horizontal link (weight = 1)

                    src_id = col + (row * ncols)
                    dst_id = (col + 1) + (row * ncols)
                    self.makeBiLink(src_id, dst_id, 1, "East", "West", IntLink)

                if (row + 1 < nrows):
                    # Vertical link (weight = 2)

                    src_id = col + (row * ncols)
                    dst_id = col + ((row + 1) * ncols)
                    self.makeBiLink(src_id, dst_id, 2, "North", "South", IntLink)

        if not self.tikz_out is None:
            self.tikz_out.close()

        network.int_links = self.int_links
