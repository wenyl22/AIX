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
import random

from common import FileSystemConfig

from topologies.BaseTopology import SimpleTopology

# Creates a generic Mesh assuming an equal number of cache
# and directory controllers.
# XY routing is enforced (using link weights)
# to guarantee deadlock freedom.


class Cube_longrange(SimpleTopology):
    description = "Cube_longrange"

    def __init__(self, controllers):
        self.nodes = controllers

    # Makes a generic mesh
    # assuming an equal number of cache and directory cntrls
    def initTrafficFreqFromSyntheticType(self, options, num_w, num_h, num_d):
        synthetic = options.synthetic
        num_routers = num_w * num_h * num_d
        traffic_matrix = [[0 for i in range(num_routers)] for j in range(num_routers)]
        if options.single_dest_id != -1:
            for i in range(num_routers):
                traffic_matrix[i][options.single_dest_id] = 1
        elif synthetic == "uniform_random":
            for i in range(num_routers):
                for j in range(num_routers):
                    traffic_matrix[i][j] = 1
        elif synthetic == "transpose":
            for i in range(num_w):
                for j in range(num_h):
                    for k in range(num_d):
                        # # (i, j, k) -> (j, k, i)
                        # src = i + j * num_w + k * num_w * num_h
                        # dst = j + k * num_h + i * num_w * num_h
                        # # (i, j, k) -> (k, i, j)
                        # src = i + j * num_w + k * num_w * num_h
                        # dst = k + i * num_h + j * num_w * num_h

                        # # (i, j, k) -> (j, i, k)
                        src = i + j * num_w + k * num_w * num_h
                        dst = j + i * num_h + k * num_w * num_h
                        traffic_matrix[src][dst] = 1
        elif synthetic == "hotspot":
            for i in range(num_routers):
                for j in range(num_routers):
                    traffic_matrix[i][j] = 1
            for i in options.hotspots:
                for j in range(num_routers):
                    traffic_matrix[j][i] += options.hotspot_factor / 100.0
        else:
            print("Error: Traffic type not supported")
            exit(1)
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
    def caculateBenifit(self, options, Links, To, num_w, num_h, num_d):
        num_routers = num_w * num_h * num_d
        sum_d = 0
        sum_rd = 0
        for i in range(num_routers):
            for j in range(num_routers):
                i_x = i % num_w
                i_y = i // num_w % num_h
                i_z = i // num_w // num_h
                j_x = j % num_w
                j_y = j // num_w % num_h
                j_z = j // num_w // num_h
                to_i_x = To[i] % num_w
                to_i_y = To[i] // num_w % num_h
                to_i_z = To[i] // num_w // num_h
                sum_d += options.traffic_matrix[i][j] * (abs(i_x - j_x) + abs(i_y - j_y) + abs(i_z - j_z))
                if To[i] != -1:
                    sum_rd += options.traffic_matrix[i][j] * min(abs(i_x - j_x) + abs(i_y - j_y), 1 + abs(j_x - to_i_x) + abs(j_y - to_i_y) + abs(j_z - to_i_z))
                else:
                    sum_rd += options.traffic_matrix[i][j] * (abs(i_x - j_x) + abs(i_y - j_y) + abs(i_z - j_z))
        print(sum_d, sum_rd, 1 - sum_rd / sum_d)
    def caculateLongRangeLinks(self, options, num_w, num_h, num_d):       
        num_routers = num_w * num_h * num_d
        Links = []
        To = [-1] * num_routers
        while options.budget > 0:
            max_i = -1
            max_j = -1
            max_d = 0
            for i in range(num_routers):
                for j in range(i + 1, num_routers):
                    i_x = i % num_w
                    i_y = i // num_w % num_h
                    i_z = i // num_w // num_h
                    j_x = j % num_w
                    j_y = j // num_w % num_h
                    j_z = j // num_w // num_h

                    dst = ((i_x - j_x)**2 + (i_y - j_y)**2 + (i_z - j_z)**2)**0.5
                    if To[i] == -1 and To[j] == -1 and options.budget >= dst:
                        cnt = 0
                        for k in range(num_routers):
                            k_x = k % num_w
                            k_y = k // num_w % num_h
                            k_z = k // num_w // num_h
                            cnt += options.traffic_matrix[j][k] * max(0, abs(k_x - j_x) + abs(k_y - j_y) + abs(k_z - j_z) - abs(k_x - i_x) - abs(k_y - i_y) - abs(k_z - i_z) - 1)
                            cnt += options.traffic_matrix[i][k] * max(0, abs(k_x - i_x) + abs(k_y - i_y) + abs(k_z - i_z) - abs(k_x - j_x) - abs(k_y - j_y) - abs(k_z - j_z) - 1)
                        if cnt / dst > max_d:
                            max_d = cnt / dst
                            max_i = i
                            max_j = j
            if max_i == -1:
                break
            Links.append((max_i, max_j))
            To[max_i] = max_j
            To[max_j] = max_i
            options.budget -= ((max_i % num_w - max_j % num_w)**2 + (max_i // num_w % num_h - max_j // num_w % num_h)**2 + (max_i // num_w // num_h - max_j // num_w // num_h)**2)**0.5
        print(Links)
        self.caculateBenifit(options, Links, To, num_w, num_h, num_d)
        return Links
    def randomAddLongRangeLinks(self, options, num_w, num_h, num_d):
        num_routers = num_w * num_h * num_d
        Links = []
        To = [-1] * num_routers
        cnt = 0

        while cnt < 10:
            i = random.randint(0, num_routers - 1)
            j = random.randint(0, num_routers - 1)
            i_x = i % num_w
            i_y = i // num_w % num_h
            i_z = i // num_w // num_h
            j_x = j % num_w
            j_y = j // num_w % num_h
            j_z = j // num_w // num_h
            dst = ((i_x - j_x)**2 + (i_y - j_y)**2 + (i_z - j_z)**2)**0.5
            if dst <= 1:
                continue
            if To[i] == -1 and To[j] == -1 and options.budget >= dst:
                Links.append((i, j))
                To[i] = j
                To[j] = i
                options.budget -= dst
            cnt += 1
        print(Links)
        self.caculateBenifit(options, Links, To, num_w, num_h, num_d)
        return Links
    
    def getWeight(self, i_x, j_x, i_y, j_y, i_z, j_z):
        res = []
        dirn = ''
        if i_x < j_x:
            dirn += '+'
        if i_x > j_x:
            dirn += '-'
        if i_x == j_x:
            dirn += '0'
        if i_y < j_y:
            dirn += '+'
        if i_y > j_y:
            dirn += '-'
        if i_y == j_y:
            dirn += '0'
        if i_z < j_z:
            dirn += '+'
        if i_z > j_z:
            dirn += '-'
        if i_z == j_z:
            dirn += '0'
        P = [[], ["++-", "++0", "+++", "+0-", "+00", "+0+"],
             ["+--", "+-0", "+-+", "00-"],
        ["---", "--0", "--+", "0--", "0-0", "0-+"],
        ["-+-", "-+0", "-++", "0+-", "0+0", "0++", "-0-", "-00", "-0+", "00+"],

        ["+-+", "+0+", "+++", "+-0", "+00", "++0"],
        ["+--", "+0-", "++-", "0-0"],
        ["---", "-0-", "-+-", "0--", "00-", "0+-"],
        ["--+", "-0+", "-++", "0-+", "00+", "0++", "--0", "-00", "-+0", "0+0"]]

        for i in range(1, 9):
            if dirn in P[i]:
                res.append(i)
        
        assert(len(res) == 2)
        return res

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes

        num_routers = options.num_cpus
        # w * h * d = num_routers
        num_w = options.mesh_rows
        num_h = options.mesh_rows
        num_d = options.mesh_rows
        assert(num_w * num_h * num_d == num_routers)
        options.traffic_matrix = self.initTrafficFreqFromSyntheticType(options, num_w, num_h, num_d) 
        if options.best_effort:
            Links = self.caculateLongRangeLinks(options, num_w, num_h, num_d)
        else:
            Links = self.randomAddLongRangeLinks(options, num_w, num_h, num_d)
        longLinkId = [-1] * num_routers
        for (i, j) in Links:
            longLinkId[i] = j
            longLinkId[j] = i

        link_latency = options.link_latency  # used by simple and garnet
        router_latency = options.router_latency  # only used by garnet

        cntrls_per_router, remainder = divmod(len(nodes), num_routers)

        # Create the routers in the mesh
        routers = [
            Router(router_id=i, latency=router_latency,
                longLinkId=longLinkId[i],
                buffers=options.buffers_per_ctrl_vc + (longLinkId[i] != -1
                ) * options.buffers_per_ctrl_vc) 
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

        # P_1 = {++-, ++0, +++, +0-, +00, +0+}
        # P_3 = {+--, +-0, +-+, 00-}
        # P_5 = {---, --0, --+, 0--, 0-0, 0-+}
        # P_7 = {-+-, -+0, -++, 0+-, 0+0, 0++, -0-, -00, -0+, 00+}

        # P_2 = {+-+, +0+, +++, +-0, +00, ++0}
        # P_4 = {+--, +0-, ++-, 0-0}
        # P_6 = {---, -0-, -+-, 0--, 00-, 0+-}
        # P_8 = {--+, -0+, -++, 0-+, 00+, 0++, --0, -00, -+0, 0+0}

        # Long range links
        for k, (i, j) in enumerate(Links):
            i_x = i % num_w
            i_y = i // num_w % num_h
            i_z = i // num_w // num_h
            j_x = j % num_w
            j_y = j // num_w % num_h
            j_z = j // num_w // num_h
            dirn = ""
            rev_dirn = ""
            if i_z < j_z:
                dirn += "Up"
                rev_dirn += "Down"
            elif i_z > j_z:
                dirn += "Down"
                rev_dirn += "Up"
            elif i_z == j_z:
                dirn += "Same"
                rev_dirn += "Same"

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
                    weight=4,
                    per_vc_weight = self.getWeight(i_x, j_x, i_y, j_y, i_z, j_z),
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
                    weight=4,
                    per_vc_weight = self.getWeight(j_x, i_x, j_y, i_y, j_z, i_z),
                )
            )
            link_count += 2

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
                                per_vc_weight = [1, 2],
                                # +00
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
                                per_vc_weight = [7, 8],
                                # -00
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
                                per_vc_weight = [7, 8],
                                # 0+0
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
                                per_vc_weight = [5, 4],
                                # 0-0
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
                                per_vc_weight = [7, 8],
                                # 00+
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
                                per_vc_weight = [3, 6],
                                # 00-
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
