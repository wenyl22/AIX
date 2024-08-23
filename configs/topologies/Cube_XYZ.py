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

from m5.params import *
from m5.objects import *

from common import FileSystemConfig

from topologies.BaseTopology import SimpleTopology

# Creates a generic Mesh assuming an equal number of cache
# and directory controllers.
# XY routing is enforced (using link weights)
# to guarantee deadlock freedom.


class Cube_XYZ(SimpleTopology):
    description = "Cube_XYZ"

    def __init__(self, controllers):
        self.nodes = controllers

    # Makes a generic mesh
    # assuming an equal number of cache and directory cntrls

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes

        num_routers = options.num_cpus
        # w * h * d = num_routers
        num_w = options.mesh_rows
        num_h = options.mesh_rows
        num_d = options.mesh_rows
        assert(num_w * num_h * num_d == num_routers)

        link_latency = options.link_latency  # used by simple and garnet
        router_latency = options.router_latency  # only used by garnet

        cntrls_per_router, remainder = divmod(len(nodes), num_routers)

        # Create the routers in the mesh
        routers = [
            Router(router_id=i, latency=router_latency)
            for i in range(num_routers)
        ]
        network.routers = routers

        # link counter to set unique link ids
        link_count = 0

        # Add all but the remainder nodes to the list of nodes to be uniformly
        # distributed across the network.
        network_nodes = []
        remainder_nodes = []
        for node_index in range(len(nodes)):
            if node_index < (len(nodes) - remainder):
                network_nodes.append(nodes[node_index])
            else:
                remainder_nodes.append(nodes[node_index])

        # Connect each node to the appropriate router
        ext_links = []
        for (i, n) in enumerate(network_nodes):
            cntrl_level, router_id = divmod(i, num_routers)
            assert cntrl_level < cntrls_per_router
            ext_links.append(
                ExtLink(
                    link_id=link_count,
                    ext_node=n,
                    int_node=routers[router_id],
                    latency=link_latency,
                )
            )
            link_count += 1

        # Connect the remainding nodes to router 0. These should only be
        # DMA nodes.
        for (i, node) in enumerate(remainder_nodes):
            assert node.type == "DMA_Controller"
            assert i < remainder
            ext_links.append(
                ExtLink(
                    link_id=link_count,
                    ext_node=node,
                    int_node=routers[0],
                    latency=link_latency,
                )
            )
            link_count += 1

        network.ext_links = ext_links

        # Create the mesh links.
        int_links = []

        # East output to West input links (weight = 1)
        for d in range(num_d):
            for h in range(num_h):
                for w in range(num_w):
                    if w + 1 < num_w:
                        east_out = w + (h * num_w) + (d * num_w * num_h)
                        west_in = (w + 1) + (h * num_w) + (d * num_w * num_h)
                        int_links.append(
                            IntLink(
                                link_id=link_count,
                                src_node=routers[east_out],
                                dst_node=routers[west_in],
                                src_outport="East",
                                dst_inport="West",
                                latency=link_latency,
                                weight=1,
                            )
                        )
                        link_count += 1
        # West output to East input links (weight = 1)
        for d in range(num_d):
            for h in range(num_h):
                for w in range(num_w):
                    if w + 1 < num_w:
                        west_out = (w + 1) + (h * num_w) + (d * num_w * num_h)
                        east_in = w + (h * num_w) + (d * num_w * num_h)
                        int_links.append(
                            IntLink(
                                link_id=link_count,
                                src_node=routers[west_out],
                                dst_node=routers[east_in],
                                src_outport="West",
                                dst_inport="East",
                                latency=link_latency,
                                weight=1,
                            )
                        )
                        link_count += 1

        # North output to South input links (weight = 2)
        for d in range(num_d):
            for h in range(num_h):
                for w in range(num_w):
                    if h + 1 < num_h:
                        north_out = w + (h * num_w) + (d * num_w * num_h)
                        south_in = w + ((h + 1) * num_w) + (d * num_w * num_h)
                        int_links.append(
                            IntLink(
                                link_id=link_count,
                                src_node=routers[north_out],
                                dst_node=routers[south_in],
                                src_outport="North",
                                dst_inport="South",
                                latency=link_latency,
                                weight=2,
                            )
                        )
                        link_count += 1

        # South output to North input links (weight = 2)
        for d in range(num_d):
            for h in range(num_h):
                for w in range(num_w):
                    if h + 1 < num_h:
                        south_out = w + ((h + 1) * num_w) + (d * num_w * num_h)
                        north_in = w + (h * num_w) + (d * num_w * num_h)
                        int_links.append(
                            IntLink(
                                link_id=link_count,
                                src_node=routers[south_out],
                                dst_node=routers[north_in],
                                src_outport="South",
                                dst_inport="North",
                                latency=link_latency,
                                weight=2,
                            )
                        )
                        link_count += 1
        # Up output to Down input links (weight = 3)
        for d in range(num_d):
            for h in range(num_h):
                for w in range(num_w):
                    if d + 1 < num_d:
                        up_out = w + (h * num_w) + (d * num_w * num_h)
                        down_in = w + (h * num_w) + ((d + 1) * num_w * num_h)
                        int_links.append(
                            IntLink(
                                link_id=link_count,
                                src_node=routers[up_out],
                                dst_node=routers[down_in],
                                src_outport="Up",
                                dst_inport="Down",
                                latency=link_latency,
                                weight=3,
                            )
                        )
                        link_count += 1 
        # Down output to Up input links (weight = 3)
        for d in range(num_d):
            for h in range(num_h):
                for w in range(num_w):
                    if d + 1 < num_d:
                        down_out = w + (h * num_w) + ((d + 1) * num_w * num_h)
                        up_in = w + (h * num_w) + (d * num_w * num_h)
                        int_links.append(
                            IntLink(
                                link_id=link_count,
                                src_node=routers[down_out],
                                dst_node=routers[up_in],
                                src_outport="Down",
                                dst_inport="Up",
                                latency=link_latency,
                                weight=3,
                            )
                        )
                        link_count += 1

        network.int_links = int_links

    # Register nodes with filesystem
    def registerTopology(self, options):
        for i in range(options.num_cpus):
            FileSystemConfig.register_node(
                [i], MemorySize(options.mem_size) // options.num_cpus, i
            )
