# Author: David Smelt
# Adapted from: Mesh_XY.py (c) 2010 Advanced Micro Devices, Inc., 2016 Georgia Institute of Technology

import m5
from m5.params import *
from m5.objects import *

from BaseTopology import SimpleTopology
from TikzTopology import TikzTopology

class FlattenedButterfly(SimpleTopology):
    # Creates a generic FlattenedButterfly topology assuming an equal number of cache
    # and directory controllers.
    description='FlattenedButterfly'

    def __init__(self, controllers):
        self.nodes = controllers
        self.tikz_out = None

    def writeTikz(self, ln):
        # Writes Tikz topology code to file

        if not self.tikz_out is None:
            self.tikz_out.write(ln)

    def makeBiLink(self, src_id, dst_id, weight, src_outport, dst_inport, IntLink, tikz_bend_right):
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
            self.link_count += 2

            # Generate Tikz code for edge
            thick_line = "line width=0.6mm" if weight == 1 else ""
            bend_right = "bend right=30" if tikz_bend_right else ""

            if bend_right != "" and thick_line != "":
                bend_right = bend_right + ","

            self.writeTikz("    ({0}) edge [{1}] node[] {{}} ({2})".format(src_id, bend_right + thick_line, dst_id))

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
                           "every edge/.append style={bend left=30,line width=0.2mm}]")

        self.int_links = []
        self.lst_links = []

        # Create the flattened butterfly links.
        for row in xrange(nrows):
            for col in xrange(ncols):
                src_id = col + (row * ncols)

                for x in xrange(1, ncols):
                    dst_col = (col + x) % ncols
                    dst_id = dst_col + (row * ncols)

                    # Horizontal link (weight = 1)
                    self.makeBiLink(src_id, dst_id, 1, "East", "West", IntLink, (row < nrows / 2))

                for y in xrange(1, nrows):
                    dst_row = (row + y) % nrows
                    dst_id = col + (dst_row * ncols)

                    # Vertical link (weight = 2)
                    self.makeBiLink(src_id, dst_id, 2, "North", "South", IntLink, (col >= ncols / 2))

        if not self.tikz_out is None:
            self.tikz_out.close()

        network.int_links = self.int_links
