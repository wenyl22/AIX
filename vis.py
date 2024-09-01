import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
def main(mode, n = 6):
    path = []
    if mode == "transpose":
        for i_x in range(n):
            for i_y in range(n):
                path.append((i_y, i_x, i_x, i_y, n * n)) # transpose
    elif mode == "uniform":
        for i_x in range(n):
            for i_y in range(n):
                for j_x in range(n):
                    for j_y in range(n):
                        path.append((i_x, i_y, j_x, j_y, 1)) # uniform

    row_link = np.zeros((n, n - 1))
    col_link = np.zeros((n - 1, n))
    for row in range(n):
        for col in range(n - 1):
            for p in path:
                src_x, src_y, dst_x, dst_y, _ = p
                if src_y == row and (src_x <= col < dst_x or dst_x <= col < src_x):
                    row_link[row][col] += _
    for row in range(n - 1):
        for col in range(n):
            for p in path:
                src_x, src_y, dst_x, dst_y, _ = p
                if dst_x == col and (src_y <= row < dst_y or dst_y <= row < src_y):
                    col_link[row][col] += _

    fig, ax = plt.subplots()
    ax.set_xticks(np.arange(0, n, 1))
    ax.set_yticks(np.arange(0, n, 1))
    ax.set_xticklabels([])  # 隐藏 x 轴刻度标签
    ax.set_yticklabels([])  # 隐藏 y 轴刻度标签
    ax.grid(which='both')
    for spine in ax.spines.values():
        spine.set_visible(False)
    norm = mcolors.Normalize(vmin=0, vmax=max(30, 200))
    cmap = plt.get_cmap('Reds')
    # 绘制 row_link
    for i in range(n):
        for j in range(n - 1):
            color = cmap(norm(row_link[i][j]))
            ax.plot([j, j + 1], [i, i], color=color, linewidth=2)
            ax.text(j + 0.5, i, f'{row_link[i][j]:.1f}', ha='center', va='center', color='black')

    # 绘制 col_link
    for i in range(n - 1):
        for j in range(n):
            color = cmap(norm(col_link[i][j]))
            ax.plot([j, j], [i, i + 1], color=color, linewidth=2)
            ax.text(j, i + 0.5, f'{col_link[i][j]:.1f}', ha='center', va='center', color='black')

    plt.gca().invert_yaxis()
    plt.savefig(f'{mode}_link_map.png')
if __name__ == '__main__':
    main("transpose")
    main("uniform")