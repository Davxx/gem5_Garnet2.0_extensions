# Author: David Smelt
# Adapted from: Mesh_XY.py (c) 2010 Advanced Micro Devices, Inc., 2016 Georgia Institute of Technology

import m5
from m5.params import *
from m5.objects import *

from BaseTopology import SimpleTopology
from TikzTopology import TikzTopology

import numpy as np

class Ring(SimpleTopology):
    # Creates a generic Ring topology assuming an equal number of cache
    # and directory controllers.
    # XY routing is enforced (using link weights)
    # to guarantee deadlock freedom.
    description='Ring'

    def __init__(self, controllers):
        self.nodes = controllers
        self.tikz_out = None

    def writeTikz(self, ln):
        # Writes Tikz topology code to file

        if not self.tikz_out is None:
            self.tikz_out.write(ln)

    def makeBiLink(self, src_id, dst_id, weight, src_outport, dst_inport, IntLink):
        # Makes a bidirectional link between self.routers src_id and dst_id

        # src->dst link
        self.int_links.append(IntLink(link_id=self.link_count,
                                      src_node=self.routers[src_id],
                                      dst_node=self.routers[dst_id],
                                      src_outport=src_outport,
                                      dst_inport=dst_inport,
                                      latency=self.link_latency,
                                      weight=weight,
                                      escapevc_dor=src_id))

        # dst->src link. escapevc_dor is computed in Topology.cc, based on
        # src->dst link DOR values
        self.int_links.append(IntLink(link_id=self.link_count + 1,
                                      src_node=self.routers[dst_id],
                                      dst_node=self.routers[src_id],
                                      src_outport=dst_inport,
                                      dst_inport=src_outport,
                                      latency=self.link_latency,
                                      weight=weight,
                                      escapevc_dor=-1))

        thick_line = "line width=1mm" if weight == 1 else ""
        self.writeTikz("    ({0}) edge [{1}] node[] {{}} ({2})".format(src_id, thick_line, dst_id))
        self.link_count += 2

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes
        self.nrouters = options.num_cpus

        # Number of rows must == 2
        options.mesh_rows = 2
        nrows = 2

        # Default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        self.link_latency = options.link_latency # used by simple and garnet
        router_latency = options.router_latency # only used by garnet

        # There must be an evenly divisible number of cntrls to routers
        # Also, obviously the number or rows must be <= the number of routers
        cntrls_per_router, remainder = divmod(len(nodes), self.nrouters)
        assert(nrows > 0 and nrows <= self.nrouters)
        ncols = int(self.nrouters / nrows)
        assert(ncols * nrows == self.nrouters)

        # There must be an even number of routers
        assert(self.nrouters % 2 == 0)

        # Optionally generate Tikz topology code in 'output_directory/topo.tex' and
        # convert it to 'output_directory/topology.png'
        if options.tikz:
            self.tikz_out = TikzTopology(m5.options.outdir, nrows, ncols)

        # Create the routers on the ring
        self.routers = [Router(router_id=i, latency = router_latency) for i in range(self.nrouters)]
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
            cntrl_level, router_id = divmod(i, self.nrouters)
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


        # Place routers on the ring, counter-clockwise
        ring = np.zeros((nrows, ncols), dtype=int)
        is_first_router = True
        for x in xrange(nrows - 1, -1, -1):
            for y in xrange(ncols):
                r = y + (x * ncols)
                x_index = nrows - 1 - x
                y_index = ncols - 1 - y if x > 0 else y
                ring[x_index][y_index] = r

                if is_first_router:
                    is_first_router = False
                    self.writeTikz("    \\node[main node] ({0}) [above right=0cm] {{{0}}};".format(r, r))
                else:
                    if x == nrows - 1:
                        self.writeTikz("    \\node[main node] ({0}) [left of={{{1}}}] {{{2}}};".format(r, r - 1, r))
                    else:
                        self.writeTikz("    \\node[main node] ({0}) [below of={{{1}}}] {{{2}}};".format(r, ring[x][y], r))

        self.writeTikz("\n    \\path[every node/.style={font=\\sffamily\\footnotesize},"
                       "every edge/.append style={line width=0.3mm}]")

        self.int_links = []

        # Create the ring's links
        flip_horizontal = False
        for x in xrange(nrows - 1, -1, -1):
            for y in xrange(ncols):
                src_id = ring[x][ncols - 1 - y] if flip_horizontal else ring[x][y]
                dst_id = (src_id + 1) % self.nrouters
                dst_npxindex = np.argwhere(ring == dst_id)[0][0]

                if dst_npxindex != x:
                    # Destination router is on a different row ==> Vertical link (weight = 1)
                    if flip_horizontal:
                        # West vertical link
                        self.makeBiLink(src_id, dst_id, 1, "South", "North", IntLink)
                    else:
                        # East vertical link
                        self.makeBiLink(src_id, dst_id, 1, "North", "South", IntLink)
                else:
                    # Horizontal link (weight = 1)

                    if x == 0:
                        # Destination router is west of source router

                        self.makeBiLink(src_id, dst_id, 1, "West", "East", IntLink)
                    else:
                        # Destination router is east of source router

                        self.makeBiLink(src_id, dst_id, 1, "East", "West", IntLink)

            flip_horizontal = True

        if not self.tikz_out is None:
            self.tikz_out.close()

        network.int_links = self.int_links
