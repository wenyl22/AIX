from m5.params import *
from m5.objects import *

from common import FileSystemConfig

from topologies.BaseTopology import SimpleTopology

class Ring(SimpleTopology):
    description = "Ring"

    def __init__(self, controllers):
        self.nodes = controllers

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes

        num_routers = options.num_cpus
        # num_rows = options.mesh_rows
        # assert num_rows > 0 and num_rows <= num_routers

        # default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        link_latency = options.link_latency  # used by simple and garnet
        router_latency = options.router_latency  # only used by garnet

        # There must be an evenly divisible number of cntrls to routers
        # Also, obviously the number or rows must be <= the number of routers
        cntrls_per_router, remainder = divmod(len(nodes), num_routers)
        # num_columns = int(num_routers / num_rows)
        # assert num_columns * num_rows == num_routers

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

        # Connect the remainding nodes to router 0.  These should only be
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
        for id in range(num_routers):
            if id + 1 < num_routers:
                east_out = id
                west_in = id + 1
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
            else:
                east_out = id
                west_in = 0
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
        for id in range(num_routers):
            if id + 1 < num_routers:
                east_in = id
                west_out = id + 1
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
            else:
                east_in = id
                west_out = 0
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

        network.int_links = int_links

    # Register nodes with filesystem
    def registerTopology(self, options):
        for i in range(options.num_cpus):
            FileSystemConfig.register_node(
                [i], MemorySize(options.mem_size) // options.num_cpus, i
            )
