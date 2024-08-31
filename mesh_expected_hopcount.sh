syntheticTypes=("uniform_random" "transpose" "hotspot" "real_traffic")
trafficMatrices=("real_traffic/mesh_4x4/Fpppp_mesh_4x4_traffic.txt" "real_traffic/mesh_4x4/H264-720p_dec_mesh_4x4_traffic.txt" "real_traffic/mesh_4x4/H264-1080p_dec_mesh_4x4_traffic.txt" "real_traffic/mesh_4x4/Robot_mesh_4x4_traffic.txt" "real_traffic/mesh_4x4/RS-32_28_8_dec_mesh_4x4_traffic.txt" "real_traffic/mesh_4x4/RS-32_28_8_enc_mesh_4x4_traffic.txt" "real_traffic/mesh_4x4/Sparse_mesh_4x4_traffic.txt")

command_line="./build/NULL/gem5.opt configs/example/garnet_synth_traffic.py \
        --network=garnet --num-cpus=16 --num-dirs=16 \
        --topology=Mesh_longrange --mesh-rows=4 \
        --inj-vnet=0 --synthetic=\$synthetic \
        --sim-cycles=20 --injectionrate=0.00 \
        --routing-algorithm=1 --hotspots 5 11 12 --hotspot-factor=100"

statsFile="mesh_expected_hopcount.txt"
for synthetic in "${syntheticTypes[@]}"; do
    if [ "$synthetic" == "real_traffic" ]; then
        for matrix in "${trafficMatrices[@]}"; do
            for experiment in {1..2}; do
                cmd=$command_line
                if [ "$experiment" -eq 0 ]; then
                    cmd="$cmd --budget=0"
                else
                    cmd="$cmd --budget=12"
                fi
                if [ "$experiment" -eq 2 ]; then
                    cmd="$cmd --best-effort"
                fi
                cmd="$cmd --traffic-matrix=$matrix"
                eval $cmd >> $statsFile
            done
        done
        continue
    fi
    for experiment in {1..2}; do
        cmd=$command_line
        if [ "$experiment" -eq 0 ]; then
            cmd="$cmd --budget=0"
        else
            cmd="$cmd --budget=12"
        fi
        if [ "$experiment" -eq 2 ]; then
            cmd="$cmd --best-effort"
        fi
        eval $cmd >> $statsFile
    done
done
