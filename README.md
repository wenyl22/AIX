Simulation results mentioned in the report are stored in the `output` folder, and the corresponding plots are stored in the `plots` folder.

## Reproduce all results in the report

**TLDR**: To reproduce the results from simulation, run the following command:
```bash
# clean the output txt files
# Run with care!!!!!
source clear.sh 
source run_all.sh
source plot_all.sh
```

In order to save your time, we also provide the statistics of the simulation results in txt format. You can directly run the following command to generate the plots:
```bash
source plot_all.sh
```

The simulation results will be saved to the `output` folder. The plots will be saved in the `plots` folder.

## Reproduce each result in the report
*   The curves showing the connection of $\mu$ expected hopcount and critical traffic load $\lambda_c$
```bash
source expcode/bound_mesh.sh
source expcode/bound_cube.sh
python expcode/plot_bound.py --name bound_cube
python expcode/plot_bound.py --name bound_mesh
```

*   The improvement in expected hopcount on different topologies
```bash
source expcode/mesh_expected_hopcount.sh
source expcode/cube_expected_hopcount.sh
python expcode/plot_expected_hopcount.py --name mesh_expected_hopcount
python expcode/plot_expected_hopcount.py --name cube_expected_hopcount
```

**Note the improvement of Mesh/Cube + Random Express Links over Mesh/Cube is not deterministic.**

*   Topology Centric Experiments:

    *   2D Topo + Synthetic Traffic(Uniform + Transpose)
    ```bash
    source expcode/mesh_synth.sh
    python expcode/plot.py --name mesh_synth_16
    ```
    *   2D Topo + Hotspot Traffic
    ```bash
    source expcode/mesh_hotspot.sh
    python expcode/plot.py --name mesh_hotspot_16
    ```

    *   2D Topo + Real Traffic
    ```bash
    source expcode/mesh_real.sh
    python expcode/plot_real.py --name mesh_real_16
    ```

    *   3D Topo + Synthetic Traffic(Uniform + Transpose)
    ```bash
    source expcode/cube_synth.sh
    python expcode/plot.py --name cube_synth_64
    ```
*   Routing and Flow Control Centric Experiments:

    *   2D GTM vs Escape VC on Synthetic Traffic
    ```bash
    source expcode/mesh_synth_evc.sh
    python expcode/plot.py --name mesh_synth_evc_16
    ```
    *   2D GTM vs Escape VC on HotSpot Traffic
    ```bash
    source expcode/mesh_hotspot_evc.sh
    python expcode/plot.py --name mesh_hotspot_evc_16
    ```
    *   2D GTM vs Escape VC on Real Traffic
    ```bash
    source expcode/mesh_real_evc.sh
    python expcode/plot.py --name mesh_real_evc_16
    ```

    *   3D GTM vs Escape VC on Synthetic Traffic
    ```bash
    source expcode/cube_synth_evc.sh
    python expcode/plot.py --name cube_synth_evc_64
    ```
## Options when simulating a NoC:

### Topology
```bash
--topology=Mesh_XY --mesh-rows=$rows --num-cpus=$num_cpus
# num_cpus % rows == 0
--topology=Mesh_longrange --mesh-rows=$rows --num-cpus=$num_cpus --budget=$budget --best-effort
# num_cpus % rows == 0, without best-effort, the long-range links are randomly added within the given budget
--topology=Cube_XYZ --mesh-rows=$rows --num-cpus=$num_cpus
# row = col = depth = (num_cpus)^(1/3), only supports regular cube
--topology=Cube_longrange --mesh-rows=$rows --num-cpus=$num_cpus --budget=$budget --best-effort
# row = col = depth = (num_cpus)^(1/3), without best-effort, the long-range links are randomly added within the given budget
```

### Traffic
```bash
--synthetic=uniform_random/transpose
# applicable for mesh and cube
--synthetic=hotspot --hotspot=$router_id_list --hotspot-factor=$hotspot_factor 
# applicable for mesh and cube
--synthetic=real_traffic --traffic-matrix=$traffic_matrix_file
# must match the corresponding topology, for this lab we only find the benchmark suite for mesh in specific shapes, e.g., 16x16, 8x8, 4x4
```

### Routing
Routing algorithms and their ids match as follows:
* 1: XY_ (for Mesh_XY)
* 4: SOUTHLAST_ (Adaptive, for Mesh_XY)
* 5: SLLONGRANGE_ (Adaptive, for Mesh_longrange)
* 6: XYZ_ (for Cube_XYZ)
* 7: HiRY_(for Cube_longrange)
* 8: ANY_ (Adaptive, use along with a deadlock-free routing algorithm, to implement escape VC)
(Adaptive routing is only supported within wormhole flow control)

```bash
--routing-algorithm=1/3/6
# Deterministic routing
--routing-algorithm=4/5 --adaptive-routing
# Turn model routing
--routing-algorithm=8 --adaptive-routing --escape-routing=1/4/5/6
# Adaptive routing with escape VC, escape-routing is the deadlock-free routing algorithm used for escape VC
--congestion-sensor=$sensor
# Adaptive mechanism, switch outport if the current outport's credit is less than the other outports' credits by $sensor
```

### Flow control
In lab4, we abandon the virtual-cut-through flow control in the original simulator, and only support wormhole flow control considering only single-flit packets. Multiple vcs-per-vnet is supported beyond lab3.

```bash
--wormhole
# enable wormhole flow control
--vcs-per-vnet=$vc --buffers-per-ctrl-vc=$buffers
# vc: number of VCs per virtual network, buffers: number of buffers per VC in the ctrl vnet
```