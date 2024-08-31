#!/bin/bash

# Define different configurations
injectionRates=($(seq 0.01 0.03 1))
trafficMatrices=("real_traffic/mesh_4x4/Sparse_mesh_4x4_traffic.txt")
# "real_traffic/mesh_4x4/Fpppp_mesh_4x4_traffic.txt" "real_traffic/mesh_4x4/RS-32_28_8_enc_mesh_4x4_traffic.txt" "real_traffic/mesh_4x4/H264-720p_dec_mesh_4x4_traffic.txt" 
# "real_traffic/mesh_4x4/H264-1080p_dec_mesh_4x4_traffic.txt" "real_traffic/mesh_4x4/Robot_mesh_4x4_traffic.txt" "real_traffic/mesh_4x4/RS-32_28_8_dec_mesh_4x4_traffic.txt" 

wormholeEnable=(1 1 1 1 1)
VcsPerVnet=(2 2 2 2 2)
AdaptiveRouting=(0 1 1 1 1)
BufferPerCtrlVc=(2 2 2 2 2)
RoutingAlgorithm=(1 8 8 5 5)
CongestionSensor=(0 0 1 0 1)
EscapeVCEnable=(0 1 1 0 0)
EscapeRoutingAlgorithm=(-1 1 1 -1 -1)
Topology=("Mesh_XY" "Mesh_longrange" "Mesh_longrange" "Mesh_longrange" "Mesh_longrange")
command_line="./build/NULL/gem5.opt configs/example/garnet_synth_traffic.py \
                --network=garnet --num-cpus=16 --num-dirs=16 \
                --topology=\$topology --mesh-rows=4 \
                --inj-vnet=0 --synthetic=real_traffic \
                --traffic-matrix=\$matrix \
                --injectionrate=\$rate \
                --routing-algorithm=\$routing --escape-routing=\$escape_routing \
                --vcs-per-vnet=\$vcs --buffers-per-ctrl-vc=\$buffer \
                --congestion-sensor=\$sensor \
                --sim-cycles=200000 --best-effort --budget=12"
# File to store results
statsFile="mesh_real_evc_16.txt"

# Clear the file to store fresh results
#echo "" > $statsFile

for matrix in "${trafficMatrices[@]}"; do
    for experiment in {0..4}; do
        for rate in "${injectionRates[@]}"; do
            topology=${Topology[$experiment]}
            routing=${RoutingAlgorithm[$experiment]}
            adaptive=${AdaptiveRouting[$experiment]}
            wormhole=${wormholeEnable[$experiment]}
            vcs=${VcsPerVnet[$experiment]}
            buffer=${BufferPerCtrlVc[$experiment]}
            sensor=${CongestionSensor[$experiment]}
            escape_routing=${EscapeRoutingAlgorithm[$experiment]}
            cmd=$command_line
            if [ "$wormhole" -eq 1 ]; then
                cmd="$cmd --wormhole"
            fi
            if [ "$adaptive" -eq 1 ]; then
                cmd="$cmd --adaptive-routing"
            fi
            echo Running experiment with the following parameters: injection rate = $rate, synthetic type = real_traffic, topology = $topology, routing algorithm = $routing, adaptive = $adaptive, wormhole = $wormhole, vcs per vnet = $vcs, buffer per ctrl vc = $buffer, sensor = $sensor, escape-routing = $escape_routing, maxtrix = $matrix, experiment = $experiment >> $statsFile
            eval $cmd
            grep "packets_injected::total" m5out/stats.txt | sed 's/system.ruby.network.packets_injected::total\s*/packets_injected = /' >> $statsFile
            grep "packets_received::total" m5out/stats.txt | sed 's/system.ruby.network.packets_received::total\s*/packets_received = /' >> $statsFile
            grep "average_packet_queueing_latency" m5out/stats.txt | sed 's/system.ruby.network.average_packet_queueing_latency\s*/average_packet_queueing_latency = /' >> $statsFile
            grep "average_packet_network_latency" m5out/stats.txt | sed 's/system.ruby.network.average_packet_network_latency\s*/average_packet_network_latency = /' >> $statsFile
            grep "average_packet_latency" m5out/stats.txt | sed 's/system.ruby.network.average_packet_latency\s*/average_packet_latency = /' >> $statsFile
            grep "average_hops" m5out/stats.txt | sed 's/system.ruby.network.average_hops\s*/average_hops = /' >> $statsFile
            clk_period=$(grep "system.clk_domain.clock" m5out/stats.txt | awk '{print $2;}')
            simTicks=$(grep "simTicks" m5out/stats.txt | awk '{print $2;}')
            received_packets_per_cpu=$(grep "system.ruby.network.received_packets_per_cpu" m5out/stats.txt | awk '{print $2}')
            awk -v received_packets_per_cpu="$received_packets_per_cpu" -v simTicks="$simTicks" -v clk_period="$clk_period" 'BEGIN {print "reception_rate = " received_packets_per_cpu / simTicks * clk_period}' >> $statsFile   
            echo "--------------------------------" >> $statsFile
            average_packet_latency=$(grep "average_packet_latency" m5out/stats.txt | awk '{print $2}')
            if (( $(echo "$average_packet_latency > 1000" | bc -l) )); then
                echo "Breaking out of loop"
                break
            fi

        done
    done
done
echo "Simulation runs completed."
