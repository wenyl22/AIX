import pandas as pd
import matplotlib.pyplot as plt
import math
import argparse
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

routing_algorithms_id2name = {
    0: "Table",
    1: "XY",
    2: "Custom",
    3: "LFT",
    4: "TM",
    5: "GTM",
    6: "XYZ",
    7: "GTM",
    8: "EscapeVC"
}

def latency_throughput(df, name, synthetic_type):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True) 
    colors = ['g', 'b', 'c', 'r', 'm', 'y', 'k']
    linestyles = ['-', '--', '-.', ':']
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*']
    for experiment, val in df[["Experiment", "Synthetic Type"]].drop_duplicates().values:
        if synthetic_type != val:
            continue
        subset = df[(df["Experiment"] == experiment) & (df["Synthetic Type"] == synthetic_type)]
        topology = subset["Topology"].values[0]
        routing = int(subset["RoutingAlgorithm"].values[0])
        congestion_sensor = subset["Sensor"].values[0]
        buffer = subset["Buffer"].values[0]
        if int(experiment) < 3:
            topology = topology.split("_")[0]
        Label = f"{topology} {routing_algorithms_id2name[routing]} {congestion_sensor}"
        exp = int(experiment)
        color = colors[exp % len(colors)]
        linestyle = linestyles[exp % len(linestyles)]
        marker = markers[exp % len(markers)]
        if buffer <= congestion_sensor:
            continue

        axes[0].plot(subset["Injection Rate"], subset["Latency"], marker=marker, linestyle=linestyle, color=color, alpha=0.5)
        axes[0].set_ylim(5, 30)
        axes[0].set_xlabel("Injection Rate(packets/node/cycle)")
        axes[0].set_ylabel("Average Packet Latency(ticks)")
        axes[0].set_title("Latency-InjectionRate Curve")

        axes[1].plot(subset["Injection Rate"], subset["HopCount"], marker=marker, linestyle=linestyle, color=color, alpha=0.5)
        axes[1].set_xlabel("Injection Rate(packets/node/cycle)")
        axes[1].set_ylabel("Average HopCount")
        axes[1].set_title("HopCount-InjectionRate Curve")

        axes[2].plot(subset["Injection Rate"], subset["ReceptionRate"], marker=marker, linestyle=linestyle, color=color, alpha=0.5, label=Label)
        axes[2].set_xlabel("Injection Rate(packets/node/cycle)")
        axes[2].set_ylabel("Reception Rate(packets/node/cycle)")
        axes[2].set_title("ReceptionRate - InjectionRate Curve")
    axes[2].legend(loc = 'lower right')
    axins = inset_axes(axes[0], width="20%", height="20%", loc='center left')
    for experiment, val in df[["Experiment", "Synthetic Type"]].drop_duplicates().values:
        if synthetic_type != val:
            continue
        subset = df[(df["Experiment"] == experiment) & (df["Synthetic Type"] == synthetic_type)]
        topology = subset["Topology"].values[0]
        routing = int(subset["RoutingAlgorithm"].values[0])
        congestion_sensor = subset["Sensor"].values[0]
        buffer = subset["Buffer"].values[0]
        exp = int(experiment)
        color = colors[exp % len(colors)]
        linestyle = linestyles[exp % len(linestyles)]
        marker = markers[exp % len(markers)]
        if buffer <= congestion_sensor:
            continue
        axins.plot(subset["Injection Rate"], subset["Latency"], marker=marker, linestyle=linestyle, color=color, alpha=0.5)
    axins.set_xlim(0.0, 0.10)
    if synthetic_type == "transpose":
        lower = 6
        upper = 12
    if synthetic_type == "uniform_random":
        if "cube" in name:
            lower = 10
            upper = 15
        else:
            lower = 9
            upper = 11
    if synthetic_type == "hotspot":
        lower = 9
        upper = 12
    axins.set_ylim(lower, upper) 
    axins.set_xticks([])
    axins.set_yticks([])

    mark_inset(axes[0], axins, loc1=2, loc2=4, fc="none", ec="0.5")

    #plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f"plots/{name}_{synthetic_type}.png", dpi=300) 
    plt.close()

if __name__ == '__main__':
    data = []

    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, help="File to parse")
    args = parser.parse_args()
    name = args.name

    with open(f"output/{name}.txt", "r") as file:
        for line in file:
            if line.startswith("Running"):
                parts = line.split(", ")
                for part in parts:
                    if "rate" in part:
                        rate = float(part.split(" = ")[1])
                    if "synthetic" in part:
                        synthetic_type = part.split(" = ")[1]
                    if "topology" in part:
                        topology = part.split(" = ")[1]
                    if "routing" in part and "escape" not in part:
                        routing_algorithm = part.split(" = ")[1]
                    if "experiment" in part:
                        experiment = part.split(" = ")[1]
                    if "sensor" in part:
                        sensor = part.split(" = ")[1]
                    if "buffer" in part:
                        buffer = part.split(" = ")[1]
            elif "average_packet_latency" in line:
                latency = float(line.strip().split(" = ")[1].split("(")[0])
            elif "packets_received" in line:
                throughput = float(line.strip().split(" = ")[1].split("(")[0])
            elif "average_hops" in line:
                hopcount = float(line.strip().split(" = ")[1].split("(")[0])
            elif "reception_rate" in line:
                reception_rate = float(line.strip().split(" = ")[1].split("(")[0])
                data.append((synthetic_type, rate, latency, throughput, hopcount, routing_algorithm, experiment, topology, reception_rate, sensor, buffer))

    df = pd.DataFrame(data, columns=["Synthetic Type", "Injection Rate", "Latency", "Throughput", "HopCount", "RoutingAlgorithm", "Experiment", "Topology", "ReceptionRate", "Sensor", "Buffer"])
    if "synth" in name:
        latency_throughput(df, name, "uniform_random")
        latency_throughput(df, name, "transpose")
    else:
        latency_throughput(df, name, "hotspot")
    #hop_count(df, name)
    #reception_injection_rate(df, name)