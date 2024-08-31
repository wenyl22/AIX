/*
 * Copyright (c) 2008 Princeton University
 * Copyright (c) 2016 Georgia Institute of Technology
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */


#include "mem/ruby/network/garnet/RoutingUnit.hh"

#include "base/cast.hh"
#include "base/compiler.hh"
#include "debug/RubyNetwork.hh"
#include "mem/ruby/network/garnet/InputUnit.hh"
#include "mem/ruby/network/garnet/Router.hh"
#include "mem/ruby/slicc_interface/Message.hh"

namespace gem5
{

namespace ruby
{

namespace garnet
{

RoutingUnit::RoutingUnit(Router *router)
{
    max_weight = -1;
    m_router = router;
    m_routing_table.clear();
    m_ordered_routing_table.clear();
    m_weight_table.clear();
    m_in_per_vc_weight_table.clear();
    m_out_per_vc_weight_table.clear();
}

void
RoutingUnit::addRoute(std::vector<NetDest>& routing_table_entry)
{
    if (routing_table_entry.size() > m_routing_table.size()) {
        m_routing_table.resize(routing_table_entry.size());
    }
    for (int v = 0; v < routing_table_entry.size(); v++) {
        m_routing_table[v].push_back(routing_table_entry[v]);
    }
}

void
RoutingUnit::addOrderedRoute(std::vector <std::vector<NetDest>> & routing_table_entry)
{
    if (routing_table_entry.size() > m_ordered_routing_table.size()) {
        m_ordered_routing_table.resize(routing_table_entry.size());
    }
    for (int v = 0; v < routing_table_entry.size(); v++) {
        m_ordered_routing_table[v].push_back(routing_table_entry[v]);
    }
}

void
RoutingUnit::addWeight(int link_weight)
{
    m_weight_table.push_back(link_weight);
}
void
RoutingUnit::addInWeight(std::vector <int>& link_weight)
{
    int vcs = m_router -> get_vc_per_vnet();
    std::vector <int> extended_weight;
    if (!link_weight.size()) {
        for (int i = 0; i < vcs; i++) {
            extended_weight.push_back(-1);
        }
    }
    else   
        for (int i = 0; i < vcs; i++) {
            max_weight = std::max(max_weight, link_weight[i % link_weight.size()]);
            extended_weight.push_back(link_weight[i % link_weight.size()]);
        }
    m_in_per_vc_weight_table.push_back(extended_weight);
}


void
RoutingUnit::addOutWeight(std::vector <int>& link_weight)
{
    int vcs = m_router -> get_vc_per_vnet();
    std::vector <int> extended_weight;
    if (!link_weight.size()) {
        for (int i = 0; i < vcs; i++) {
            extended_weight.push_back(-1);
        }
    }
    else   
        for (int i = 0; i < vcs; i++) {
            max_weight = std::max(max_weight, link_weight[i % link_weight.size()]);
            extended_weight.push_back(link_weight[i % link_weight.size()]);
        }
    m_out_per_vc_weight_table.push_back(extended_weight);
}

bool
RoutingUnit::supportsVnet(int vnet, std::vector<int> sVnets)
{
    // If all vnets are supported, return true
    if (sVnets.size() == 0) {
        return true;
    }

    // Find the vnet in the vector, return true
    if (std::find(sVnets.begin(), sVnets.end(), vnet) != sVnets.end()) {
        return true;
    }

    // Not supported vnet
    return false;
}

/*
 * This is the default routing algorithm in garnet.
 * The routing table is populated during topology creation.
 * Routes can be biased via weight assignments in the topology file.
 * Correct weight assignments are critical to provide deadlock avoidance.
 */
int
RoutingUnit::lookupRoutingTable(int vnet, NetDest msg_destination)
{
    // First find all possible output link candidates
    // For ordered vnet, just choose the first
    // (to make sure different packets don't choose different routes)
    // For unordered vnet, randomly choose any of the links
    // To have a strict ordering between links, they should be given
    // different weights in the topology file

    int output_link = -1;
    int min_weight = INFINITE_;
    std::vector<int> output_link_candidates;
    int num_candidates = 0;

    // Identify the minimum weight among the candidate output links
    for (int link = 0; link < m_routing_table[vnet].size(); link++) {
        if (msg_destination.intersectionIsNotEmpty(
            m_routing_table[vnet][link])) {

        if (m_weight_table[link] <= min_weight)
            min_weight = m_weight_table[link];
        }
    }

    // Collect all candidate output links with this minimum weight
    for (int link = 0; link < m_routing_table[vnet].size(); link++) {
        if (msg_destination.intersectionIsNotEmpty(
            m_routing_table[vnet][link])) {

            if (m_weight_table[link] == min_weight) {
                num_candidates++;
                output_link_candidates.push_back(link);
            }
        }
    }

    if (output_link_candidates.size() == 0) {
        fatal("Fatal Error:: No Route exists from this Router.");
        exit(0);
    }

    // Randomly select any candidate output link
    int candidate = 0;
    if (!(m_router->get_net_ptr())->isVNetOrdered(vnet))
        candidate = rand() % num_candidates;

    output_link = output_link_candidates.at(candidate);
    return output_link;
}


void
RoutingUnit::addInDirection(PortDirection inport_dirn, int inport_idx)
{
    m_inports_dirn2idx[inport_dirn] = inport_idx;
    m_inports_idx2dirn[inport_idx]  = inport_dirn;
}

void
RoutingUnit::addOutDirection(PortDirection outport_dirn, int outport_idx)
{
    m_outports_dirn2idx[outport_dirn] = outport_idx;
    m_outports_idx2dirn[outport_idx]  = outport_dirn;
}

// outportCompute() is called by the InputUnit
// It calls the routing table by default.
// A template for adaptive topology-specific routing algorithm
// implementations using port directions rather than a static routing
// table is provided here.

int
RoutingUnit::outportCompute(RouteInfo route, int inport,
                            PortDirection inport_dirn)
{
    int outport = -1;

    if (route.dest_router == m_router->get_id()) {

        // Multiple NIs may be connected to this router,
        // all with output port direction = "Local"
        // Get exact outport id from table
        outport = lookupRoutingTable(route.vnet, route.net_dest);
        return outport;
    }

    // Routing Algorithm set in GarnetNetwork.py
    // Can be over-ridden from command line using --routing-algorithm = 1
    RoutingAlgorithm routing_algorithm =
        (RoutingAlgorithm) m_router->get_net_ptr()->getRoutingAlgorithm();

    switch (routing_algorithm) {
        case TABLE_:  outport =
            lookupRoutingTable(route.vnet, route.net_dest); break;
        case XY_:     outport =
            outportComputeXY(route, inport, inport_dirn); break;
        // any custom algorithm
        case CUSTOM_: outport =
            outportComputeCustom(route, inport, inport_dirn); break;
        case LFT_:    outport =
            outportComputeLFT(route, inport); break;
        case XYZ_:    outport =
            outportComputeXYZ(route, inport, inport_dirn); break;
        default: panic("Unknown non-adaptive routing algorithm\n");
    }

    assert(outport != -1);
    return outport;
}

// XY routing implemented using port directions
// Only for reference purpose in a Mesh
// By default Garnet uses the routing table
int
RoutingUnit::outportComputeXY(RouteInfo route,
                              int inport,
                              PortDirection inport_dirn)
{
    PortDirection outport_dirn = "Unknown";

    [[maybe_unused]] int num_rows = m_router->get_net_ptr()->getNumRows();
    int num_cols = m_router->get_net_ptr()->getNumCols();
    assert(num_rows > 0 && num_cols > 0);

    int my_id = m_router->get_id();
    int my_x = my_id % num_cols;
    int my_y = my_id / num_cols;

    int dest_id = route.dest_router;
    int dest_x = dest_id % num_cols;
    int dest_y = dest_id / num_cols;

    int x_hops = abs(dest_x - my_x);
    int y_hops = abs(dest_y - my_y);

    bool x_dirn = (dest_x >= my_x);
    bool y_dirn = (dest_y >= my_y);

    // already checked that in outportCompute() function
    assert(!(x_hops == 0 && y_hops == 0));

    if (x_hops > 0) {
        if (x_dirn) {
            assert(inport_dirn == "Local" || inport_dirn == "West");
            outport_dirn = "East";
        } else {
            assert(inport_dirn == "Local" || inport_dirn == "East");
            outport_dirn = "West";
        }
    } else if (y_hops > 0) {
        if (y_dirn) {
            // "Local" or "South" or "West" or "East"
            assert(inport_dirn != "North");
            outport_dirn = "North";
        } else {
            // "Local" or "North" or "West" or "East"
            assert(inport_dirn != "South");
            outport_dirn = "South";
        }
    } else {
        // x_hops == 0 and y_hops == 0
        // this is not possible
        // already checked that in outportCompute() function
        panic("x_hops == y_hops == 0");
    }

    return m_outports_dirn2idx[outport_dirn];
}

// LFT routing
int
RoutingUnit::outportComputeLFT(RouteInfo route, int inport)
{
    return m_outports_dirn2idx["West"];
}

// XYZ routing
int
RoutingUnit::outportComputeXYZ(RouteInfo route,
                               int inport,
                               PortDirection inport_dirn)
{
    PortDirection outport_dirn = "Unknown";

    [[maybe_unused]] int num_w = m_router->get_net_ptr()->getNumRows();
    int num_h = num_w, num_d = num_w;
    int my_id = m_router->get_id();
    int my_x = my_id % num_w, my_y = (my_id / num_w) % num_h, my_z = my_id / (num_w * num_h);
    int dest_id = route.dest_router;
    int dest_x = dest_id % num_w, dest_y = (dest_id / num_w) % num_h, dest_z = dest_id / (num_w * num_h);
    int x_hops = abs(dest_x - my_x), y_hops = abs(dest_y - my_y), z_hops = abs(dest_z - my_z);
    bool x_dirn = (dest_x >= my_x), y_dirn = (dest_y >= my_y), z_dirn = (dest_z >= my_z);
    if (x_hops > 0) {
        if (x_dirn) {
            assert(inport_dirn == "Local" || inport_dirn == "West");
            outport_dirn = "East";
        } else {
            assert(inport_dirn == "Local" || inport_dirn == "East");
            outport_dirn = "West";
        }
    } else if (y_hops > 0) {
        if (y_dirn) {
            assert(inport_dirn != "North");
            outport_dirn = "North";
        } else {
            assert(inport_dirn != "South");
            outport_dirn = "South";
        }
    } else if (z_hops > 0) {
        if (z_dirn) {
            outport_dirn = "Up";
        } else {
            outport_dirn = "Down";
        }
    } else {
        panic("x_hops == y_hops == z_hops == 0");
    }
    return m_outports_dirn2idx[outport_dirn];
 }

std::vector < std::pair<int, int> >
RoutingUnit::outportsCompute(RouteInfo route,
                             int inport,
                             PortDirection inport_dirn, int invc)
{
    int outport = -1;
    if (route.dest_router == m_router->get_id()) {
        outport = lookupRoutingTable(route.vnet, route.net_dest);
        std::vector < std::pair<int, int> > outports;
        int vnet = route.vnet;
        for (int i = 0; i < m_router->get_vc_per_vnet(); ++i) {
            outports.push_back(std::make_pair(outport, i + vnet * m_router->get_vc_per_vnet()));
        }
        return outports;
    }
    RoutingAlgorithm routing_algorithm =
        (RoutingAlgorithm) m_router->get_net_ptr()->getRoutingAlgorithm();
    std::vector < std::pair<int, int> > outports;
    switch (routing_algorithm) {
        case SOUTHLAST_:  outports =
            outportsComputeSouthLast(route, inport, inport_dirn, invc); break;
        case SLLONGRANGE_:  outports =
            outportsComputeLongRange(route, inport, inport_dirn, invc); break;
        case ROUTING_HIRY_:  outports = 
            outportsComputeHiRy(route, inport, invc); break;
        default: panic("Unknown adaptive routing algorithm\n");
    }
    return outports;
}

// South-Last routing
std::vector < std::pair<int, int> >
RoutingUnit::outportsComputeSouthLast(RouteInfo route,
                                     int inport,
                                     PortDirection inport_dirn, int invc)
{
    PortDirection outport_dirn = "Unknown";

    [[maybe_unused]] int num_rows = m_router->get_net_ptr()->getNumRows();
    int num_cols = m_router->get_net_ptr()->getNumCols();
    assert(num_rows > 0 && num_cols > 0);

    int my_id = m_router->get_id();
    int my_x = my_id % num_cols;
    int my_y = my_id / num_cols;

    int dest_id = route.dest_router;
    int dest_x = dest_id % num_cols;
    int dest_y = dest_id / num_cols;

    int x_hops = abs(dest_x - my_x);
    int y_hops = abs(dest_y - my_y);

    bool x_dirn = (dest_x >= my_x);
    bool y_dirn = (dest_y >= my_y);
    std::vector < int > outports;
    int vnet = route.vnet;
    // for (int i = 0; i < m_outports_dirn2idx.size();++i)
    //     assert(m_outports_dirn2idx[m_outports_idx2dirn[i]] == i);
    if (inport_dirn == "North") {        
        outports.push_back(m_outports_dirn2idx["South"]);
    } else {
        if (x_hops > 0) {
            if (x_dirn) {
                outports.push_back(m_outports_dirn2idx["East"]);
            } else {
                outports.push_back(m_outports_dirn2idx["West"]);
            }
        }
        if (y_hops > 0) {
            if (y_dirn) {
                outports.push_back(m_outports_dirn2idx["North"]);
            } else if(x_hops == 0) {
                outports.push_back(m_outports_dirn2idx["South"]);
            }
        }
    }
    std::vector< std::pair<int, int> > outports_pair;
    for (int i = 0; i < outports.size(); ++i) {
        for (int j = 0; j < m_router->get_vc_per_vnet(); ++j) {
            outports_pair.push_back(std::make_pair(outports[i], j + vnet * m_router->get_vc_per_vnet()));
        }
    }
    assert(outports_pair.size());
    return outports_pair;
}

bool 
RoutingUnit::sendAllowedLongRange(PortDirection inport_dirn, 
                                    PortDirection outport_dirn) {
    bool ret = true;
    if (inport_dirn == "NorthWest" || inport_dirn == "NorthEast") {
        ret &= (outport_dirn == "South");
    }
    if (inport_dirn == "SameSouth" || inport_dirn == "South") {
        ret &= (outport_dirn == "South" ||
                outport_dirn == "SouthWest" ||
                outport_dirn == "SouthEast" ||
                outport_dirn == "SameSouth");
    }
    return ret;
}
std::vector < std::pair<int, int> >
RoutingUnit::outportsComputeLongRange(RouteInfo route,
                                     int inport,
                                     PortDirection inport_dirn, int invc)
{
    // Long-Range Turn Model routing is a simple routing algorithm
    // that routes all packets to the South port
    // except for the packets that are coming from the North port
    // which are routed to the East port.
    // This routing algorithm is used in the Mesh topology.
    PortDirection outport_dirn = "Unknown";

    [[maybe_unused]] int num_rows = m_router->get_net_ptr()->getNumRows();
    int num_cols = m_router->get_net_ptr()->getNumCols();
    assert(num_rows > 0 && num_cols > 0);

    int my_id = m_router->get_id();
    int my_x = my_id % num_cols;
    int my_y = my_id / num_cols;

    int dest_id = route.dest_router;
    int dest_x = dest_id % num_cols;
    int dest_y = dest_id / num_cols;

    int x_hops = abs(dest_x - my_x);
    int y_hops = abs(dest_y - my_y);

    bool x_dirn = (dest_x >= my_x);
    bool y_dirn = (dest_y >= my_y);
    std::vector < int > outports;
    int k_x = -1, k_y = -1, flag = 0, vnet = route.vnet;
    if (m_router->longLinkId != -1) {
        k_x = m_router->longLinkId % num_cols, k_y = m_router->longLinkId / num_cols;
        if (abs(dest_x - k_x) + abs(dest_y - k_y) + 1 < x_hops + y_hops) 
            flag = 1;
    }
    for (auto it = m_outports_dirn2idx.begin(); it != m_outports_dirn2idx.end(); ++it) {
        PortDirection dirn = it->first;
        bool ok = sendAllowedLongRange(inport_dirn, dirn);
        if (dirn == "East")
            ok &= (x_hops > 0 && x_dirn);
        if (dirn == "West")
            ok &= (x_hops > 0 && !x_dirn);
        if (dirn == "North")
            ok &= (y_hops > 0 && y_dirn);
        if (dirn == "South")
            ok &= (y_hops > 0 && !y_dirn);
        if (dirn.length() > 5)
            ok &= flag;
        if (dirn == "SouthWest" || dirn == "SouthEast" 
            || dirn == "SameSouth" || dirn == "South") {
            // can only go south after going sw/se
            ok &= (x_hops == 0 && !y_dirn);
        }
        if (ok) {
            outports.push_back(it->second);
        }
    }
    std::vector< std::pair<int, int> > outports_pair;
    for (int i = 0; i < outports.size(); ++i) {
        for (int j = 0; j < m_router->get_vc_per_vnet(); ++j) {
            outports_pair.push_back(std::make_pair(outports[i], j + vnet * m_router->get_vc_per_vnet()));
        }
    }
    assert(outports_pair.size());
    return outports_pair;
}

std::vector < std::pair<int, int> >
RoutingUnit::outportsComputeHiRy(RouteInfo route, int inport, int invc) {
    std::vector <std::pair <int, int> > candidates;
    int cur_weight = m_in_per_vc_weight_table[inport][invc];
/*    std::cerr << "In: " << invc << std::endl;
    std::cerr << "cur_weight: " << cur_weight << std::endl << "src: " << m_router->get_id() << std::endl << "dest: ";
    for (auto u : route.net_dest.getAllDest())
        std::cerr << u << ' ';
    std::cerr << std::endl;*/
    int num_ports = m_router -> get_num_outports(), num_vc = m_router->get_vc_per_vnet();
    for (int outport = 0; outport < num_ports; outport++) {
        for (int outvc = 0; outvc < num_vc; outvc++) {
            if (m_out_per_vc_weight_table[outport][outvc] >= cur_weight 
            && m_out_per_vc_weight_table[outport][outvc] != -1
            && m_out_per_vc_weight_table[outport][outvc] != INFINITE_LATENCY
            && route.net_dest.intersectionIsNotEmpty(
                m_ordered_routing_table[route.vnet][outport][m_out_per_vc_weight_table[outport][outvc]])
                )
                candidates.push_back(std::make_pair(outport, outvc));
        }
    }
/*    for (auto u : candidates)
        std::cerr << u.first << ' ' << u.second << std::endl;*/
    return candidates;
}

// Template for implementing custom routing algorithm
// using port directions. (Example adaptive)
int
RoutingUnit::outportComputeCustom(RouteInfo route,
                                 int inport,
                                 PortDirection inport_dirn)
{
    panic("%s placeholder executed", __FUNCTION__);
}

} // namespace garnet
} // namespace ruby
} // namespace gem5
