# Author: David Smelt
# Adapted from: Mesh_XY.py (c) 2010 Advanced Micro Devices, Inc., 2016 Georgia Institute of Technology

from m5.params import *
from m5.objects import *

from BaseTopology import SimpleTopology
from TikzTopology import TikzTopology

import numpy as np

class HierarchicalRing(SimpleTopology):
    # Creates a generic HierarchicalRing topology assuming an equal number of cache
    # and directory controllers.
    description='HierarchicalRing'

    def __init__(self, controllers):
        self.nodes = controllers
        self.tikz_out = None

    def writeTikz(self, ln):
        # Writes Tikz topology code to file

        if not self.tikz_out is None:
            self.tikz_out.write(ln)

    def makeBiLink(self, src_id, dst_id, weight, src_outport, dst_inport, IntLink, is_central_ring):
        # Makes a bidirectional link between routers src_id and dst_id

        new_weight = weight
        num_routers = self.nrows * self.ncols
        if (not is_central_ring and src_outport == "North") or is_central_ring:
            if dst_id < num_routers - self.ncols and src_id >= self.ncols and\
                dst_id % self.ncols != 0 and (dst_id + 1) % self.ncols != 0:
                # Link is part of central ring ==> gets stronger weight = 1
                new_weight = 1
        
        if (new_weight == 1 and not (src_id, dst_id) in self.central_ring_links and\
            not (dst_id, src_id) in self.central_ring_links) or new_weight == 2:

            self.int_links.append(IntLink(link_id=self.link_count,
                                          src_node=self.routers[src_id],
                                          dst_node=self.routers[dst_id],
                                          src_outport=src_outport,
                                          dst_inport=dst_inport,
                                          latency=self.link_latency,
                                          weight=new_weight))
            self.int_links.append(IntLink(link_id=self.link_count + 1,
                                          src_node=self.routers[dst_id],
                                          dst_node=self.routers[src_id],
                                          src_outport=dst_inport,
                                          dst_inport=src_outport,
                                          latency=self.link_latency,
                                          weight=new_weight))

            if new_weight == 1:
                self.central_ring_links.append((src_id, dst_id))

            thick_line = "line width=1mm" if new_weight == 1 else ""
            self.writeTikz("    ({0}) edge [{1}] node[] {{}} ({2})".format(src_id, thick_line, dst_id))
            self.link_count += 2

    def connectRing(self, ring, weight, IntLink, is_central_ring=False):
        # Connects routers in the ring bidirectionally

        x_range = ring.shape[0]
        y_range = ring.shape[1]

        for x in xrange(x_range):
            for y in xrange(y_range):
                if (not is_central_ring and y < y_range - 1) or\
                   (is_central_ring and y < y_range - 1 and (x == 0 or x == x_range - 1)):
                    # Horizontal link

                    src_id = ring[x][y]
                    dst_id = ring[x][y + 1]
                    self.makeBiLink(src_id, dst_id, weight, "East", "West", IntLink, is_central_ring)

                if (not is_central_ring and x == 1 and (y == 0 or y == y_range - 1)) or\
                   (is_central_ring and x >= 1 and x <= x_range - 1):
                    # Vertical link

                    src_id = ring[x][y]
                    dst_id = ring[x - 1][y]
                    self.makeBiLink(src_id, dst_id, weight, "North", "South", IntLink, is_central_ring)

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes
        num_routers = options.num_cpus
        self.nrows = options.mesh_rows

        # Default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        self.link_latency = options.link_latency # used by simple and garnet
        router_latency = options.router_latency # only used by garnet

        # There must be an evenly divisible number of cntrls to routers
        # Also, obviously the number or rows must be <= the number of routers
        cntrls_per_router, remainder = divmod(len(nodes), num_routers)
        assert(self.nrows > 0 and self.nrows <= num_routers)
        self.ncols = int(num_routers / self.nrows)
        assert(self.ncols * self.nrows == num_routers)
        
        # There must be an even number of rows and columns
        assert(self.nrows % 2 == 0 and self.ncols % 2 == 0)

        # Optionally generate Tikz topology code in 'output_directory/topo.tex' and
        # convert it to 'output_directory/topology.png'
        if options.tikz:
            self.tikz_out = TikzTopology(self.nrows, self.ncols)

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

            for row in xrange(self.nrows):
                first_col = False

                for col in xrange(self.ncols):
                    r = col + (row * self.ncols)

                    if not first_col:
                        first_col = True

                        if row == 0:
                            self.writeTikz("    \\node[main node] (0) [below left=0cm] {0};")
                        else:
                            self.writeTikz("    \\node[main node] ({0}) [above of={{{1}}}] {{{2}}};".format(r,
                                           r - self.ncols, r))
                    else:
                        self.writeTikz("    \\node[main node] ({0}) [right of={{{1}}}] {{{2}}};".format(r, r - 1, r))

            self.writeTikz("\n    \\path[every node/.style={font=\\sffamily\\footnotesize},"
                           "every edge/.append style={line width=0.3mm}]")

        self.int_links = []
        self.central_ring_links = []
        rings_left = []

        # Gather routers for left half of sub-rings
        midpoint = self.ncols / 2
        for x in xrange(0, self.nrows, 2):
            ring = np.zeros((2, midpoint), dtype=int)

            offset = 0
            for i in xrange(self.ncols):
                if i >= midpoint:
                    offset = 1

                router_index = i - offset * midpoint
                ring[1 - offset][router_index] = router_index + ((x + offset) * self.ncols)

            rings_left.append(ring)

        # Gather routers for right half of sub-rings
        rings_right = rings_left[:]
        for i in xrange(len(rings_right)):
            rings_right[i] = rings_right[i] + midpoint

        # Create sub-ring links (weight = 2)
        rings = rings_left + rings_right

        for ring in rings:
            self.connectRing(ring, 2, IntLink)

        # Gather routers situated on central ring
        central_ring_height = self.nrows - 2
        central_ring = np.zeros((central_ring_height, 2), dtype=int)
        for i in xrange(central_ring_height):
            id1 = (i + 1) * self.ncols + midpoint - 1
            id2 = id1 + 1
            central_ring[central_ring_height - 1 - i][0] = id1
            central_ring[central_ring_height - 1 - i][1] = id2

        # Create central ring links (weight = 1)
        self.connectRing(central_ring, 1, IntLink, True)

        if not self.tikz_out is None:
            self.tikz_out.close()
        
        network.int_links = self.int_links
