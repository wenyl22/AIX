import matplotlib.pyplot as plt
import numpy as np
import argparse

def main():
    # read data from file
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', help='path to the data file')
    args = parser.parse_args()
    types = ["Uniform", "Transpose", "HotSpot", "Fppp", "H264-720p", "H264-1080p", "Robot", "RS-32_28_8_dec", "RS-32_28_8_enc", "Sparse"]
    if "cube" in args.name:
        types = types[0:2]
    with open(f"output/{args.name}.txt") as f:
        data = f.read()

    lines = data.strip().split('\n')
    baselines = []
    randoms = []
    random_improvements = []
    optimals = []
    optimal_imporvements = []
    flg = 0
    for i, line in enumerate(lines):
        if line.startswith('['):
            if flg % 2 == 0:
                values = lines[i+1].split(' ')
                baselines.append(float(values[0]))
                randoms.append(float(values[1]))
                random_improvements.append(float(values[2]))
            else:
                values = lines[i+1].split(' ')
                optimals.append(float(values[1]))
                optimal_imporvements.append(float(values[2]))
            flg += 1
    x = np.arange(len(types)) * 1.5 
    width = 0.3  
    if "cube" in args.name:
        fig, ax = plt.subplots(figsize=(6, 6))
        bars1 = ax.bar(x - width, baselines, width, label='4x4x4Cube', color='green', alpha=0.7)
        bars2 = ax.bar(x, randoms, width, label='4x4x4Cube + Random Expess Link', color='cyan', alpha=0.7)
        bars3 = ax.bar(x + width, optimals, width, label='4x4x4Cube + Optimal Expess Link', color='magenta', alpha=0.7)

    else:
        fig, ax = plt.subplots(figsize=(15, 6))
        bars1 = ax.bar(x - width, baselines, width, label='4x4Mesh', color='green', alpha=0.7)
        bars2 = ax.bar(x, randoms, width, label='4x4Mesh + Random Expess Link', color='cyan', alpha=0.7)
        bars3 = ax.bar(x + width, optimals, width, label='4x4Mesh + Optimal Expess Link', color='magenta', alpha=0.7)
    ax.set_xlabel('Traffic Patterns')
    ax.set_ylabel('Expected HopCount')
    ax.set_title('Expected HopCount of Different Traffic Patterns on Tested Topologies')
    ax.set_xticks(x)
    ax.set_xticklabels(types)
    ax.legend(loc = 'lower right')

    # 在柱子上标出降低值
    for i, bar in enumerate(bars2):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval + 0.01, f"-{round(random_improvements[i] * 100, 1)}%", ha='center', va='bottom')
    for i, bar in enumerate(bars3):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval + 0.01, f"-{round(optimal_imporvements[i] * 100, 1)}%", ha='center', va='bottom')

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'plots/{args.name}.png')
if __name__ == '__main__':
    main()