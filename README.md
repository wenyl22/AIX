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
* 7: ANY_ (Adaptive, use along with a deadlock-free routing algorithm, to implement escape VC)
(Adaptive routing is only supported within wormhole flow control)

```bash
--routing-algorithm=1/3/6
# Deterministic routing
--routing-algorithm=4/5 --adaptive-routing
# Turn model routing
--routing-algorithm=7 --adaptive-routing --escape-routing=1/4/5/6
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