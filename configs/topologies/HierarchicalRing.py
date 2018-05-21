# Author: David Smelt
# Adapted from: Mesh_XY.py (c) 2010 Advanced Micro Devices, Inc., 2016 Georgia Institute of Technology

import m5
from m5.params import *
from m5.objects import *

from BaseTopology import SimpleTopology
from TikzTopology import TikzTopology
from TopologyToDSENT import TopologyToDSENT

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

        part_of_central_ring = False
        new_weight = weight
        self.nrouters = self.nrows * self.ncols
        if (not is_central_ring and src_outport == "North") or is_central_ring:
            if dst_id < self.nrouters - self.ncols and src_id >= self.ncols and\
                dst_id % self.ncols != 0 and (dst_id + 1) % self.ncols != 0:
                # Link is part of central ring ==> gets stronger weight = 1
                part_of_central_ring = True
                new_weight = 1
        
        if (part_of_central_ring and not (src_id, dst_id) in self.central_ring_links and\
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

            if part_of_central_ring:
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
        concentration_factor = options.concentration_factor
        ncpus = options.num_cpus
        self.nrouters = ncpus / concentration_factor
        self.nrows = options.mesh_rows

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
        assert(self.nrows > 0 and self.nrows <= self.nrouters)
        self.ncols = int(self.nrouters / self.nrows)

        assert(self.ncols * self.nrows == self.nrouters)
        assert(self.nrouters * concentration_factor == ncpus)

        caches_per_router, remainder = divmod(len(cache_nodes), self.nrouters)
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
            self.tikz_out = TikzTopology(m5.options.outdir, self.nrows, self.ncols)

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
        
        assert(len(rings_left) >= 2 and len(rings_right) >= 2)

        # Gather routers situated on central ring
        central_ring_height = self.nrows - 2
        central_ring = np.zeros((central_ring_height, 2), dtype=int)
        for i in xrange(central_ring_height):
            id1 = (i + 1) * self.ncols + midpoint - 1
            id2 = id1 + 1
            central_ring[central_ring_height - 1 - i][0] = id1
            central_ring[central_ring_height - 1 - i][1] = id2

        assert(central_ring.size >= 4)

        """
        # Start of orphaned Escape VC DOR code #

        # Create escape VC DOR table
        dor = [-1] * self.nrouters
        dor_base = 0
        for ring_num, ring in enumerate(rings_left):
            top = 1 if ring_num == len(rings_left) - 1 else 0

            i = dor_base + len(ring[top]) - 1
            for r in ring[top]:
                dor[r] = i
                i -= 1

            j = dor_base + len(ring[1 - top])
            for r in ring[1 - top]:
                dor[r] = j
                j += 1
            
            dor_base += rings_left[0].size

        dor_base = rings_right[0].size * len(rings_right) * 2

        for ring_num, ring in enumerate(rings_right):
            dor_base -= rings_left[0].size
            top = 0 if ring_num == len(rings_left) - 1 else 1

            i = dor_base + 2 * len(ring[top]) - 1
            for r in ring[top]:
                dor[r] = i
                i -= 1

            j = dor_base
            for r in ring[1 - top]:
                dor[r] = j
                j += 1


        self.routers = [Router(router_id=i, latency=router_latency, escapevc_dor=dor[i]) \
                        for i in range(self.nrouters)]
        # End of orphaned Escape VC DOR code #
        """

        # Create the routers in the mesh
        self.routers = [Router(router_id=i, latency=router_latency) for i in range(self.nrouters)]
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
            router_id += self.nrouters / ndirs

        # Connect the DMA nodes to router 0
        for (i, node) in enumerate(dma_nodes):
            assert(node.type == 'DMA_Controller')
            ext_links.append(ExtLink(link_id=self.link_count, ext_node=node,
                                     int_node=self.routers[0],
                                     latency=link_latency))
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

        # Create sub-ring links (weight = 2)
        rings = rings_left + rings_right

        for ring in rings:
            self.connectRing(ring, 2, IntLink)


        # Create central ring links (weight = 1)
        self.connectRing(central_ring, 1, IntLink, True)

        if not self.tikz_out is None:
            self.tikz_out.close()
        
        network.int_links = self.int_links
        
        # Generate router.cfg and electrical-link.cfg for DSENT
        dsent = TopologyToDSENT(m5.options.outdir, options.link_width_bits, 
                                options.vcs_per_vnet, options.buffers_per_ctrl_vc,
                                options.buffers_per_data_vc)
