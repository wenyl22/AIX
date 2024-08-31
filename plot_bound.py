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
    7: "EscapeVC",
}


def visualize(df):
    plt.plot(df["Injection Rate"], df["VAL1"], marker='o', label=f"N_ave/T_0")
    plt.plot(df["Injection Rate"], df["VAL2"], marker='o', label=f"N_ave/T_ave")
    plt.plot(df["Injection Rate"], df["Injection Rate"], label=f"rate", linestyle='--')

    plt.xlabel("Injection Rate(packets/node/cycle)")
    plt.legend()
    plt.savefig("bound_full.png")

if __name__ == '__main__':
    data = []

    with open("bound_full.txt", "r") as file:
        for line in file:
            if line.startswith("Running"):
                parts = line.strip().split(", ")
                rate = float(parts[0].split(" = ")[1])
            elif "average_packet_network_latency" in line:
                latency = float(line.strip().split(" = ")[1].split("(")[0])
            elif "packets_in_network_per_cpu" in line:
                network_latency_per_cpu = float(line.strip().split(" = ")[1])
                val1 = network_latency_per_cpu / 100000 / (3 + 3.75 * 2)
                val2 = network_latency_per_cpu / 100000 / latency
                if rate < 0.72:
                    data.append((rate, val1, val2))

    df = pd.DataFrame(data, columns=["Injection Rate", "VAL1", "VAL2"])
    visualize(df)