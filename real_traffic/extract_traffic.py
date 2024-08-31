import glob
def main():
    # Extract traffic data from the real_traffic folder
    files = glob.glob('*/*/*.rtp')
    for file in files:
        print(file)
        row = int(file.split('/')[1].split('_')[1].split('x')[0])
        col = int(file.split('/')[1].split('_')[1].split('x')[1])
        num = row * col
        with open(file, 'r') as f:
            lines = f.readlines()
            parts = lines[17].split('\t')
            num_tasks = int(parts[0])
            num_edges = int(parts[1])
            task2id = [-1] * num_tasks
            traffic_matrix = [[0 for i in range(num)] for j in range(num)]
            for i in range(20, 20 + num_tasks):
                parts = lines[i].split('\t')
                x = int(parts[1].split(',')[0].split('(')[1])
                y = int(parts[1].split(',')[1].split(')')[0])
                task2id[i - 20] = x + y * row
            for i in range(20 + num_tasks, 20 + num_tasks + num_edges):
                parts = lines[i].split('\t')
                src = int(parts[1])
                dst = int(parts[2])
                sum = 0
                for part in parts[3:]:
                    if '.' in part:
                        sum += float(part) * 100
                traffic_matrix[task2id[src]][task2id[dst]] = int(sum)
            
            new_file = file.split('.')[0] + '_traffic.txt'
            with open(new_file, 'w') as nf:
                for i in range(num):
                    for j in range(num):
                        nf.write(str(traffic_matrix[i][j]) + ' ')
                    nf.write('\n')
                

if __name__ == '__main__':
    main()