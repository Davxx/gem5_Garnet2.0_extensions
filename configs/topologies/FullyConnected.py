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

from math import sqrt
import m5
from m5.params import *
from m5.objects import *

from BaseTopology import SimpleTopology
from TikzTopology import TikzTopology
from TopologyToDSENT import TopologyToDSENT

class FullyConnected(SimpleTopology):
    # Creates a generic Mesh assuming an equal number of cache
    # and directory controllers.
    # XY routing is enforced (using link weights)
    # to guarantee deadlock freedom.
    description='FullyConnected'

    def __init__(self, controllers):
        self.nodes = controllers
        self.tikz_out = None

    def writeTikz(self, ln):
        # Writes Tikz topology code to file

        if not self.tikz_out is None:
            self.tikz_out.write(ln)

    def makeBiLink(self, src_id, dst_id, nrows, ncols, IntLink):
        # Makes a bidirectional link between routers src_id and dst_id

        if not (src_id, dst_id) in self.lst_links and not (dst_id, src_id) in self.lst_links:
            self.lst_links.append((src_id, dst_id))
            
            # Calculate distance in proportion to a straight link
            (src_x, src_y) = divmod(src_id, ncols)
            (dst_x, dst_y) = divmod(dst_id, ncols)
            x_diff = float(abs(src_x - dst_x))
            y_diff = float(abs(src_y - dst_y))
            distance = sqrt(x_diff ** 2 + y_diff ** 2)

            self.int_links.append(IntLink(link_id=self.link_count,
                                          src_node=self.routers[src_id],
                                          dst_node=self.routers[dst_id],
                                          latency=self.link_latency,
                                          weight=1))
            self.int_links.append(IntLink(link_id=self.link_count + 1,
                                          src_node=self.routers[dst_id],
                                          dst_node=self.routers[src_id],
                                          latency=self.link_latency,
                                          weight=1))

            self.writeTikz("    ({0}) edge [line width=0.2mm] node[] {{}} ({1})".format(src_id, dst_id))
            self.link_count += 2

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes
        concentration_factor = options.concentration_factor
        ncpus = options.num_cpus
        nrouters = ncpus / concentration_factor
        nrows = options.mesh_rows

        # First determine which nodes are cache cntrls vs. dirs vs. dma
        cache_nodes = []
        dir_nodes = []
        dma_nodes = []
        for node in nodes:
            if node.type == 'L1Cache_Controller' or node.type == 'L2Cache_Controller':
                cache_nodes.append(node)
            elif node.type == 'Directory_Controller':
                dir_nodes.append(node)
            elif node.type == 'DMA_Controller':
                dma_nodes.append(node)

        # Obviously the number of rows must be <= the number of routers
        # and evenly divisible.  Also the number of caches must be a
        # multiple of the number of routers and the number of directories
        # must be <= the number of cache nodes
        assert(nrows > 0 and nrows <= nrouters)
        ncols = int(nrouters / nrows)

        assert(ncols * nrows == nrouters)
        assert(nrouters * concentration_factor == ncpus)

        caches_per_router, remainder = divmod(len(cache_nodes), nrouters)
        assert(remainder == 0)

        ndirs = options.num_dirs
        assert(len(dir_nodes) <= len(cache_nodes))

        # Default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        self.link_latency = options.link_latency # used by simple and garnet
        router_latency = options.router_latency # only used by garnet

        # Optionally generate Tikz topology code in 'output_directory/topo.tex' and
        # convert it to 'output_directory/topology.png'
        if options.tikz:
            self.tikz_out = TikzTopology(m5.options.outdir, nrows, ncols)

        # Create the routers in the mesh
        self.routers = [Router(router_id=i, latency=router_latency) for i in range(nrouters)]
        network.routers = self.routers

        # Link counter to set unique link ids
        self.link_count = 0

        # Connect each cache node to the appropriate router
        ext_links = []
        router_id = 0
        for (i, node) in enumerate(cache_nodes):
            if i != 0 and i % caches_per_router == 0:
                router_id += 1
            ext_links.append(ExtLink(link_id=self.link_count, ext_node=node,
                                     int_node=self.routers[router_id],
                                     latency=self.link_latency))
            self.link_count += 1

       # Connect each directory node to the appropriate router
        router_id = 0
        for (i, node) in enumerate(dir_nodes):
            ext_links.append(ExtLink(link_id=self.link_count, ext_node=node,
                                     int_node=self.routers[router_id],
                                     latency=self.link_latency))
            self.link_count += 1
            router_id += nrouters / ndirs

        # Connect the DMA nodes to router 0
        for (i, node) in enumerate(dma_nodes):
            assert(node.type == 'DMA_Controller')
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

        # Fully connect the mesh
        for i in xrange(len(self.routers)):
            for j in xrange(len(self.routers)):
                if (i != j):
                    self.makeBiLink(i, j, nrows, ncols, IntLink)

        if not self.tikz_out is None:
            self.tikz_out.close()

        network.int_links = self.int_links
        
        # Generate router.cfg and electrical-link.cfg for DSENT
        dsent = TopologyToDSENT(m5.options.outdir, options.link_width_bits, 
                                options.vcs_per_vnet, options.buffers_per_ctrl_vc,
                                options.buffers_per_data_vc)
