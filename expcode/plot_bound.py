import pandas as pd
import matplotlib.pyplot as plt
import math
import argparse


def visualize(df, name):
    plt.plot(df["Injection Rate"], df["VAL1"], marker='o', label=f"N_ave/T_0")
    plt.plot(df["Injection Rate"], df["VAL2"], marker='o', label=f"N_ave/T_ave")
    plt.plot(df["Injection Rate"], df["Injection Rate"], label=f"injection rate", linestyle='--')
    plt.xlabel("Injection Rate(packets/node/cycle)", fontsize=14)
    plt.legend(prop={'size': 12})  # 设置图例字体大小
    plt.savefig(f"plots/{name}.png", dpi = 300)

if __name__ == '__main__':
    data = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, default="bound_cube")
    args = parser.parse_args()
    with open(f"output/{args.name}.txt", "r") as file:
        for line in file:
            if line.startswith("Running"):
                parts = line.strip().split(", ")
                rate = float(parts[0].split(" = ")[1])
            elif "average_packet_network_latency" in line:
                latency = float(line.strip().split(" = ")[1].split("(")[0])
            elif "packets_in_network_per_cpu" in line:
                network_latency_per_cpu = float(line.strip().split(" = ")[1])
                if "cube" in args.name:
                    val1 = network_latency_per_cpu / 100000 / (3 + 3.75 * 2)
                    val2 = network_latency_per_cpu / 100000 / latency
                else:
                    val1 = network_latency_per_cpu / 100000 / (3 + 5.25 * 2)
                    val2 = network_latency_per_cpu / 100000 / latency
                if rate < 0.72 or "cube" in args.name:
                    data.append((rate, val1, val2))

    df = pd.DataFrame(data, columns=["Injection Rate", "VAL1", "VAL2"])
    visualize(df, args.name)