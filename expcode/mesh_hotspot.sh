#!/bin/bash

# Define different configurations
injectionRates=($(seq 0.01 0.03 1))
wormholeEnable=(1 1 1 1 1)
VcsPerVnet=(1 1 1 1 1)
AdaptiveRouting=(0 1 1 1 1)
BufferPerCtrlVc=(2 2 2 2 2)
CongestionSensor=(0 0 1 0 1)
RoutingAlgorithm=(1 4 4 5 5)
Topology=("Mesh_XY" "Mesh_XY" "Mesh_XY" "Mesh_longrange" "Mesh_longrange")
command_line="./build/NULL/gem5.opt configs/example/garnet_synth_traffic.py \
                --network=garnet --num-cpus=16 --num-dirs=16 \
                --topology=\$topology --mesh-rows=4 \
                --inj-vnet=0 \
                --synthetic=hotspot \
                --hotspots 5 11 12 --hotspot-factor=100 \
                --injectionrate=\$rate \
                --vcs-per-vnet=\$vcs --buffers-per-ctrl-vc=\$buffer \
                --routing-algorithm=\$routing \
                --sim-cycles=200000 \
                --congestion-sensor=\$sensor \
                --best-effort --budget=12"

# File to store results
srcFile="m5out/stats.txt"
statsFile="output/mesh_hotspot_16.txt"

# Clear the file to store fresh results
#echo "" > $statsFile

for experiment in {0..4}; do
    for rate in "${injectionRates[@]}"; do
        topology=${Topology[$experiment]}
        routing=${RoutingAlgorithm[$experiment]}
        adaptive=${AdaptiveRouting[$experiment]}
        wormhole=${wormholeEnable[$experiment]}
        vcs=${VcsPerVnet[$experiment]}
        buffer=${BufferPerCtrlVc[$experiment]}
        sensor=${CongestionSensor[$experiment]}
        cmd=$command_line
        if [ "$wormhole" -eq 1 ]; then
            cmd="$cmd --wormhole"
        fi
        if [ "$adaptive" -eq 1 ]; then
            cmd="$cmd --adaptive-routing"
        fi
        echo Running experiment with the following parameters: injection rate = $rate, synthetic type = hotspot, topology = $topology, routing algorithm = $routing, adaptive = $adaptive, wormhole = $wormhole, vcs per vnet = $vcs, buffer per ctrl vc = $buffer, matrix = None, sensor = $sensor, experiment = $experiment >> $statsFile
        eval $cmd
        grep "packets_injected::total" $srcFile | sed 's/system.ruby.network.packets_injected::total\s*/packets_injected = /' >> $statsFile
        grep "packets_received::total" $srcFile | sed 's/system.ruby.network.packets_received::total\s*/packets_received = /' >> $statsFile
        grep "average_packet_queueing_latency" $srcFile | sed 's/system.ruby.network.average_packet_queueing_latency\s*/average_packet_queueing_latency = /' >> $statsFile
        grep "average_packet_network_latency" $srcFile | sed 's/system.ruby.network.average_packet_network_latency\s*/average_packet_network_latency = /' >> $statsFile
        grep "average_packet_latency" $srcFile | sed 's/system.ruby.network.average_packet_latency\s*/average_packet_latency = /' >> $statsFile
        grep "average_hops" $srcFile | sed 's/system.ruby.network.average_hops\s*/average_hops = /' >> $statsFile
        clk_period=$(grep "system.clk_domain.clock" $srcFile | awk '{print $2;}')
        simTicks=$(grep "simTicks" $srcFile | awk '{print $2;}')
        received_packets_per_cpu=$(grep "system.ruby.network.received_packets_per_cpu" $srcFile | awk '{print $2}')
        awk -v received_packets_per_cpu="$received_packets_per_cpu" -v simTicks="$simTicks" -v clk_period="$clk_period" 'BEGIN {print "reception_rate = " received_packets_per_cpu / simTicks * clk_period}' >> $statsFile   
        echo "--------------------------------" >> $statsFile
        average_packet_latency=$(grep "average_packet_latency" $srcFile | awk '{print $2}')
        if (( $(echo "$average_packet_latency > 1000" | bc -l) )); then
            echo "Breaking out of loop"
            break
        fi
    done
done
echo "Simulation runs completed."
