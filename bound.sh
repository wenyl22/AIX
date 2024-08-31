injectionRates=($(seq 0.01 0.03 1))
command_line="./build/NULL/gem5.opt configs/example/garnet_synth_traffic.py \
        --network=garnet --num-cpus=64 --num-dirs=64 \
        --topology=Cube_XYZ --mesh-rows=4 \
        --inj-vnet=0 --synthetic=uniform_random \
        --sim-cycles=200000 --injectionrate=\$rate \
        --routing-algorithm=6"
statsFile="bound_cube.txt"
for rate in "${injectionRates[@]}"; do
    eval $command_line
    echo Running experiment with the following parameters: injection rate = $rate>> $statsFile
    grep "packets_injected::total" m5out/stats.txt | sed 's/system.ruby.network.packets_injected::total\s*/packets_injected = /' >> $statsFile
    grep "packets_received::total" m5out/stats.txt | sed 's/system.ruby.network.packets_received::total\s*/packets_received = /' >> $statsFile
    grep "average_packet_queueing_latency" m5out/stats.txt | sed 's/system.ruby.network.average_packet_queueing_latency\s*/average_packet_queueing_latency = /' >> $statsFile
    grep "average_packet_network_latency" m5out/stats.txt | sed 's/system.ruby.network.average_packet_network_latency\s*/average_packet_network_latency = /' >> $statsFile
    grep "average_packet_latency" m5out/stats.txt | sed 's/system.ruby.network.average_packet_latency\s*/average_packet_latency = /' >> $statsFile
    grep "average_hops" m5out/stats.txt | sed 's/system.ruby.network.average_hops\s*/average_hops = /' >> $statsFile
    clk_period=$(grep "system.clk_domain.clock" m5out/stats.txt | awk '{print $2;}')
    simTicks=$(grep "simTicks" m5out/stats.txt | awk '{print $2;}')
    received_packets_per_cpu=$(grep "system.ruby.network.received_packets_per_cpu" m5out/stats.txt | awk '{print $2}')
    packets_in_network_per_cpu=$(grep "system.ruby.network.packets_in_network_per_cpu" m5out/stats.txt | awk '{print $2}')
    awk -v received_packets_per_cpu="$received_packets_per_cpu" -v simTicks="$simTicks" -v clk_period="$clk_period" 'BEGIN {print "reception_rate = " received_packets_per_cpu / simTicks * clk_period}' >> $statsFile
    awk -v packets_in_network_per_cpu="$packets_in_network_per_cpu" 'BEGIN {print "packets_in_network_per_cpu = " packets_in_network_per_cpu}' >> $statsFile
    echo "--------------------------------" >> $statsFile
done
