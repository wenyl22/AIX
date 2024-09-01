syntheticTypes=("uniform_random" "transpose")

command_line="./build/NULL/gem5.opt configs/example/garnet_synth_traffic.py \
        --network=garnet --num-cpus=64 --num-dirs=64 \
        --topology=Cube_longrange --mesh-rows=4 \
        --inj-vnet=0 --synthetic=\$synthetic \
        --sim-cycles=20 --injectionrate=0.00 \
        --routing-algorithm=1 --hotspots 5 11 12 --hotspot-factor=100"

statsFile="output/cube_expected_hopcount.txt"
for synthetic in "${syntheticTypes[@]}"; do
    for experiment in {1..2}; do
        cmd=$command_line
        if [ "$experiment" -eq 0 ]; then
            cmd="$cmd --budget=0"
        else
            cmd="$cmd --budget=24"
        fi
        if [ "$experiment" -eq 2 ]; then
            cmd="$cmd --best-effort"
        fi
        eval $cmd >> $statsFile
    done
done
