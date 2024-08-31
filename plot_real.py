import pandas as pd
import matplotlib.pyplot as plt
import math
import argparse
routing_algorithms_id2name = {
    0: "Table",
    1: "XY",
    2: "Custom",
    3: "LFT",
    4: "SouthLast",
    5: "SLLongRange",
    6: "XYZ",
}

def latency_throughput(df, name, traffic_key="Sparse"):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))  # 创建一个包含三个子图的图形
    colors = ['g', 'b', 'c', 'r', 'm', 'y', 'k']
    linestyles = ['-', '--', '-.', ':']
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*']
    cnt = 0
    for i, (experiment, traffic_matrix) in enumerate(df[["Experiment", "TrafficMatrix"]].drop_duplicates().values):
        if traffic_key not in traffic_matrix:
            continue
        subset = df[(df["Experiment"] == experiment) & (df["TrafficMatrix"] == traffic_matrix)]
        print(len(subset))
        topology = subset["Topology"].values[0]
        routing = subset["RoutingAlgorithm"].values[0]
        Label = f"{traffic_matrix} {topology} {routing}"
        color = colors[cnt % len(colors)]
        linestyle = linestyles[cnt % len(linestyles)]
        marker = markers[cnt % len(markers)]
        cnt += 1

      # 绘制第一个子图
        axes[0].plot(subset["Injection Rate"], subset["Latency"], marker=marker, linestyle=linestyle, color=color, alpha=0.5, label=Label)
        axes[0].set_xlabel("Injection Rate(packets/node/cycle)")
        axes[0].set_ylabel("Average Packet Latency(ticks)")
        axes[0].set_title("Latency-InjectionRate Curve")

        # 绘制第二个子图
        axes[1].plot(subset["Injection Rate"], subset["HopCount"], marker=marker, linestyle=linestyle, color=color, alpha=0.7)
        axes[1].set_xlabel("Injection Rate(packets/node/cycle)")
        axes[1].set_ylabel("Average HopCount")
        axes[1].set_title("HopCount-Latency Curve")

        # 绘制第三个子图
        axes[2].plot(subset["Injection Rate"], subset["ReceptionRate"], marker=marker, linestyle=linestyle, color=color, alpha=0.7)
        axes[2].set_xlabel("Injection Rate(packets/node/cycle)")
        axes[2].set_ylabel("Reception Rate(packets/node/cycle)")
        axes[2].set_title("ReceptionRate - InjectionRate Curve")


    plt.tight_layout(rect=[0, 0, 1, 0.96])  # 调整布局以适应标题和图例
    plt.savefig(f"{name}_{traffic_key}.png")
    plt.close()


if __name__ == '__main__':
    data = []
# Running experiment with the following parameters: injection rate = $rate, synthetic type = $synthetic, topology = $topology, routing algorithm = $routing, adaptive = $adaptive, wormhole = $wormhole, vcs per vnet = $vcs, buffer per ctrl vc = $buffer, matrix = $traffic_matrix, experiment = $experiment
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, help="File to parse")
    args = parser.parse_args()
    name = args.name

    with open(f"{name}.txt", "r") as file:
        for line in file:
            if line.startswith("Running"):
                parts = line.strip().split(", ")
                rate = float(parts[0].split(" = ")[1])
                synthetic_type = parts[1].split(" = ")[1]
                topology = parts[2].split(" = ")[1]
                routing_algorithm = parts[3].split(" = ")[1]
                adaptive_routing = parts[4].split(" = ")[1]
                wormhole = parts[5].split(" = ")[1]
                vcs = parts[6].split(" = ")[1]
                buffers_per_ctrl_vc = parts[7].split(" = ")[1]
                # escape_routing = parts[9].split(" = ")[1]
                traffic_matrix = parts[8].split(" = ")[1].split("/")[-1]
                sensor = parts[9].split(" = ")[1]

                experiment = parts[10].split(" = ")[1]

            elif "average_packet_latency" in line:
                latency = float(line.strip().split(" = ")[1].split("(")[0])
                latency = min(latency, 1000)
            elif "packets_received" in line:
                throughput = float(line.strip().split(" = ")[1].split("(")[0])
            elif "average_hops" in line:
                hopcount = float(line.strip().split(" = ")[1].split("(")[0])
            elif "reception_rate" in line:
                reception_rate = float(line.strip().split(" = ")[1].split("(")[0])
                data.append((synthetic_type, rate, latency, throughput, hopcount, wormhole, vcs, adaptive_routing, buffers_per_ctrl_vc, routing_algorithm, experiment, topology, traffic_matrix, reception_rate))

    df = pd.DataFrame(data, columns=["Synthetic Type", "Injection Rate", "Latency", "Throughput", "HopCount", "Wormhole", "VCS", "AdaptiveRouting", "BuffersPerCtrlVC", "RoutingAlgorithm", "Experiment", "Topology", "TrafficMatrix", "ReceptionRate"])
    traffic_keys = ["Fppp", "H264-720p", "H264-1080p", "Sparse", "Robot", "RS-32_28_8_dec", "RS-32_28_8_enc"]
    for traffic_key in traffic_keys:
        latency_throughput(df, name, traffic_key)
