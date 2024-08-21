from m5.params import *
from m5.objects import *

from common import FileSystemConfig

from topologies.BaseTopology import SimpleTopology


class Mesh_longrange(SimpleTopology):
    description = "Mesh_longrange"

    def __init__(self, controllers):
        self.nodes = controllers
    def initTrafficFreqFromSyntheticType(self, options, num_rows, num_columns):
        synthetic = options.synthetic
        num_routers = num_rows * num_columns
        traffic_matrix = [[0 for i in range(num_routers)] for j in range(num_routers)]
        if options.single_dest_id != -1:
            for i in range(num_routers):
                traffic_matrix[i][options.single_dest_id] = 1
        elif synthetic == "uniform_random":
            for i in range(num_routers):
                for j in range(num_routers):
                    if i != j:
                        traffic_matrix[i][j] = 1
        elif synthetic == "tornado":
            for i in range(num_rows):
                for j in range(num_columns):
                    k = (i + num_rows // 2) % num_rows
                    traffic_matrix[i + j * num_columns][k + j * num_columns] = 1
        elif synthetic == "bit_complement":
            for i in range(num_rows):
                for j in range(num_columns):
                    k = num_rows - 1 - i
                    l = num_columns - 1 - j
                    traffic_matrix[i + j * num_columns][k + l * num_columns] = 1
        elif synthetic == "bit_reverse":
            for i in range(num_rows):
                for j in range(num_columns):
                    k = (i ^ (num_rows - 1))
                    l = (j ^ (num_columns - 1))
                    traffic_matrix[i + j * num_columns][k + l * num_columns] = 1
        elif synthetic == "bit_rotation":
            for i in range(num_routers):
                traffic_matrix[i][(i/2) + (i%2) * (num_routers/2)] = 1
        elif synthetic == "neighbor":
            for i in range(num_rows):
                for j in range(num_columns):
                    k = (i + 1) % num_rows
                    traffic_matrix[i + j * num_columns][k + j * num_columns] = 1
        elif synthetic == "shuffle":
            for i in range(num_routers):
                if i * 2 < num_routers:
                    traffic_matrix[i][i * 2] = 1
                else:
                    traffic_matrix[i][i * 2 - num_routers + 1] = 1
        elif synthetic == "transpose":
            for i in range(num_rows):
                for j in range(num_columns):
                    traffic_matrix[i + j * num_columns][j + i * num_columns] = 1
        if options.single_sender_id != -1:
            for i in range(num_routers):
                if i != options.single_sender_id:
                    for j in range(num_routers):
                        traffic_matrix[i][j] = 0
        sum_traffic = 0
        for i in range(num_routers):
            for j in range(num_routers):
                sum_traffic += traffic_matrix[i][j]
        for i in range(num_routers):
            for j in range(num_routers):
                traffic_matrix[i][j] /= sum_traffic
        return traffic_matrix
    def caculateLongRangeLinks(self, options, num_rows, num_columns):
        num_routers = num_rows * num_columns
        Links = []
        To = [-1] * num_routers
        while options.budget > 0:
            max_i = -1
            max_j = -1
            max_d = 0
            for i in range(num_routers):
                for j in range(i + 1, num_routers):
                    i_x = i % num_columns
                    i_y = i // num_columns
                    j_x = j % num_columns
                    j_y = j // num_columns
                    dst = ((i_x - j_x)**2 + (i_y - j_y)**2)**0.5
                    if To[i] == -1 and To[j] == -1 and options.budget >= dst:
                        cnt = 0
                        for k in range(num_routers):
                            k_x = k % num_columns
                            k_y = k // num_columns
                            cnt += options.traffic_matrix[j][k] * max(0, abs(k_x - j_x) + abs(k_y - j_y) - abs(k_x - i_x) - abs(k_y - i_y) - 1)
                            cnt += options.traffic_matrix[i][k] * max(0, abs(k_x - i_x) + abs(k_y - i_y) - abs(k_x - j_x) - abs(k_y - j_y) - 1)
                        if cnt / dst > max_d:
                            max_d = cnt / dst
                            max_i = i
                            max_j = j
            if max_i == -1:
                break
            print(max_i, max_j, max_d)
            Links.append((max_i, max_j))
            To[max_i] = max_j
            To[max_j] = max_i
            options.budget -= ((max_i % num_columns - max_j % num_columns)**2 + abs(max_i // num_columns - max_j // num_columns)**2)**0.5
        # caculate reduce in average distance
        # To = [-1] * num_routers
        # for i in range(0, 16, 4):
        #     To[i] = i + 3
        #     To[i + 3] = i
        sum_d = 0
        sum_rd = 0
        for i in range(num_routers):
            for j in range(num_routers):
                i_x = i % num_columns
                i_y = i // num_columns
                j_x = j % num_columns
                j_y = j // num_columns
                sum_d += options.traffic_matrix[i][j] * (abs(i_x - j_x) + abs(i_y - j_y))
                if To[i] != -1:
                    sum_rd += options.traffic_matrix[i][j] * min(abs(i_x - j_x) + abs(i_y - j_y), 1 + abs(j_x - To[i] % num_columns) + abs(j_y - To[i] // num_columns))
                else:
                    sum_rd += options.traffic_matrix[i][j] * (abs(i_x - j_x) + abs(i_y - j_y))
        print(Links)
        print(sum_d, sum_rd, 1 - sum_rd/sum_d)
        return Links

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes
        num_routers = options.num_cpus
        num_rows = options.mesh_rows        
        
        # default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        link_latency = options.link_latency  # used by simple and garnet
        router_latency = options.router_latency  # only used by garnet

        # There must be an evenly divisible number of cntrls to routers
        # Also, obviously the number or rows must be <= the number of routers
        cntrls_per_router, remainder = divmod(len(nodes), num_routers)
        assert num_rows > 0 and num_rows <= num_routers
        num_columns = int(num_routers / num_rows)
        assert num_columns * num_rows == num_routers

        if options.traffic_matrix == None:
            options.traffic_matrix = self.initTrafficFreqFromSyntheticType(options, num_rows, num_columns)
        else: # read from file
            options.traffic_matrix = [[float(j) for j in i.split()] for i in open(options.traffic_matrix).read().split('\n') if i != '']
        Links = self.caculateLongRangeLinks(options, num_rows, num_columns)
        # Create the routers in the mesh
        longLinkId = [-1] * num_routers
        for (i, j) in Links:
            longLinkId[i] = j
            longLinkId[j] = i
        routers = [
            Router(router_id=i, latency=router_latency, longLinkId=longLinkId[i])
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
        for row in range(num_rows):
            for col in range(num_columns):
                if col + 1 < num_columns:
                    east_out = col + (row * num_columns)
                    west_in = (col + 1) + (row * num_columns)
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
        for row in range(num_rows):
            for col in range(num_columns):
                if col + 1 < num_columns:
                    east_in = col + (row * num_columns)
                    west_out = (col + 1) + (row * num_columns)
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
        for col in range(num_columns):
            for row in range(num_rows):
                if row + 1 < num_rows:
                    north_out = col + (row * num_columns)
                    south_in = col + ((row + 1) * num_columns)
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
        for col in range(num_columns):
            for row in range(num_rows):
                if row + 1 < num_rows:
                    north_in = col + (row * num_columns)
                    south_out = col + ((row + 1) * num_columns)
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
        for (i, j) in Links:
            i_x = i % num_columns
            i_y = i // num_columns
            j_x = j % num_columns
            j_y = j // num_columns
            dirn = ""
            rev_dirn = ""
            if i_y < j_y:
                dirn += "North"
                rev_dirn += "South"
            elif i_y > j_y:
                dirn += "South"
                rev_dirn += "North"
            elif i_y == j_y:
                dirn += "Same"
                rev_dirn += "Same"

            if i_x < j_x:
                dirn += "East"
                rev_dirn += "West"
            elif i_x > j_x:
                dirn += "West"
                rev_dirn += "East"
            elif i_x == j_x:
                dirn += "Same"
                rev_dirn += "Same"

            int_links.append(
                IntLink(
                    link_id=link_count,
                    src_node=routers[i],
                    dst_node=routers[j],
                    src_outport=dirn,
                    dst_inport=rev_dirn,
                    latency=link_latency,
                    weight=3,
                )
            )

            int_links.append(
                IntLink(
                    link_id=link_count + 1,
                    src_node=routers[j],
                    dst_node=routers[i],
                    src_outport=rev_dirn,
                    dst_inport=dirn,
                    latency=link_latency,
                    weight=3,
                )
            )
            link_count += 2

        network.int_links = int_links

    # Register nodes with filesystem
    def registerTopology(self, options):
        for i in range(options.num_cpus):
            FileSystemConfig.register_node(
                [i], MemorySize(options.mem_size) // options.num_cpus, i
            )
