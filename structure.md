# Article Structure


## Introduction

Generally, topologies are categorized into two types: regular and irregular. Regular topologies are easy to design and implement, but they are not suitable for all applications. Irregular topologies are more flexible and can be optimized for specific applications. However, they usually need complex routing algorithms and flow control mechanisms to avoid deadlocks and ensure high performance. 

Inspired by the two facts, we implement an application-specific NoC based on regular mesh topology. Given the traffic pattern of the target application, we add a few long range links with limited complexity to improve the performance. The proposed topology does not only enlarges the traffic load capacity, but also takes the advantage of the regularity of mesh structurebut also takes the advantage of the regularity of mesh structure, which gives us the opportunity to design deadlock-free routing algorithms with limited resources(e.g. number of virtual channels). The highlights of our work are as follows:

- **Application-Specific NoC topology design**
- **Extend 2D to arbitrary dimension**
- **Extensive experiments on both synthetic and real-world traffic patterns**
  
## Architecture

### Problem Formulation

### Topology
*  Evaluation of Critical Traffic Load
*  Long Range Link Insertion Algorithm

### Routing and Flow Control
*  2D Mesh: South Last Routing
*  Generalize to Arbitrary Dimension: HiRy and EscapeVC

## Implementation
###  RoutingUnit
###  SwitchAllocator
###  CongestionManager
###  Different Traffic Patterns
*   Uniform Random and Transpose
*   Hotspot
*   Real-world Traffic Patterns

## Evaluation
###   Hop Count [Analytical]
*   Topology:
    *   Mesh_XY, Mesh_longrange, Mesh_longrange + best-effort -> Uniform Random, Transpose, Hotspot, and Real-world Traffic Patterns
    *   Cube_XYZ, and Cube_longrange, Cube_longrange + best-effort -> Uniform Random, Transpose, Hotspot
###   Latency & Reception Ratio & Throughput [Simulation]
*   Topology:
    *   Mesh_XY + XY_Routing, Mesh_XY + South Last Routing, and Mesh_longrange + South Last Routing -> Uniform Random, Transpose, Hotspot, and Real-world Traffic Patterns
    *   Cube_XYZ + XYZ_Routing, and Cube_longrange + HiRy Routing -> Uniform Random, Transpose, Hotspot
*   Routing & Flow Control:
    *   Mesh_longrange: South Last Routing, and EscapeVC Routing -> Uniform Random, Transpose, Hotspot, and Real-world Traffic Patterns
    *   Cube_longrange: HiRy Routing, and EscapeVC Routing -> Uniform Random, Transpose, Hotspot
