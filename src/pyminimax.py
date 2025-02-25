import math
import numpy as np
import matplotlib.pyplot as plt
from pandas import DataFrame
from scipy.cluster import hierarchy
from scipy.spatial.distance import pdist


class LinkageUnionFind:
    """Structure for fast cluster labeling in unsorted dendrogram."""
#     cdef int[:] parent
#     cdef int[:] size
#     cdef int next_label

    def __init__(self, n):
        self.parent = np.arange(2 * n - 1)
        self.next_label = n
        self.size = np.ones(2 * n - 1)

    def merge(self, x, y):
        self.parent[x] = self.next_label
        self.parent[y] = self.next_label
        size = self.size[x] + self.size[y]
        self.size[self.next_label] = size
        self.next_label += 1
        return size

    def find(self, x):
        p = x

        while self.parent[x] != x:
            x = self.parent[x]

        while self.parent[p] != x:
            p, self.parent[p] = self.parent[p], x

        return x


def label(Z, n):
    """Correctly label clusters in unsorted dendrogram."""
    uf = LinkageUnionFind(n)
    for i in range(n - 1):
        x, y = int(Z[i, 0]), int(Z[i, 1])
        x_root, y_root = uf.find(x), uf.find(y)
        if x_root < y_root:
            Z[i, 0], Z[i, 1] = x_root, y_root
        else:
            Z[i, 0], Z[i, 1] = y_root, x_root
        Z[i, 3] = uf.merge(x_root, y_root)
        


def condensed_index(n, i, j):
    """
    Calculate the condensed index of element (i, j) in an n x n condensed
    matrix.
    """
    if i < j:
        return int(round(n * i - (i * (i + 1) / 2) + (j - i - 1)))
    elif i > j:
        return int(round(n * j - (j * (j + 1) / 2) + (i - j - 1)))

    
# def nn_chain(dists, n, method):
def minimax(dists):
    """Perform hierarchy clustering using nearest-neighbor chain algorithm.
    Parameters
    ----------
    dists : ndarray
        A condensed matrix stores the pairwise distances of the observations.
    Returns
    -------
    Z : ndarray, shape (n - 1, 4)
        Computed linkage matrix.
    """
    n = int((np.sqrt(8*len(dists) + 1) + 1)/2)
    
    Z_arr = np.empty((n - 1, 4))
    Z = Z_arr

    D = dists.copy()  # Distances between clusters.
    size = np.ones(n, dtype=np.intc)  # Sizes of clusters.
    
    indices = [set([i]) for i in range(n)]

#     new_dist = linkage_methods[method]

    # Variables to store neighbors chain.
    cluster_chain = np.ndarray(n, dtype=np.intc)
    chain_length = 0

#     cdef int i, j, k, x, y, nx, ny, ni
#     cdef double dist, current_min

    for k in range(n - 1):
        if chain_length == 0:
            chain_length = 1
            for i in range(n):
                if size[i] > 0:
                    cluster_chain[0] = i
                    break

        # Go through chain of neighbors until two mutual neighbors are found.
        while True:
            x = cluster_chain[chain_length - 1]

            # We want to prefer the previous element in the chain as the
            # minimum, to avoid potentially going in cycles.
            if chain_length > 1:
                y = cluster_chain[chain_length - 2]
                current_min = D[condensed_index(n, x, y)]
            else:
                current_min = np.inf   # NPY_INFINITYF

            for i in range(n):
                if size[i] == 0 or x == i:
                    continue
                
                dist = D[condensed_index(n, x, i)]
                if dist < current_min:
                    current_min = dist
                    y = i

            if chain_length > 1 and y == cluster_chain[chain_length - 2]:
                break

            cluster_chain[chain_length] = y
            chain_length += 1

        # Merge clusters x and y and pop them from stack.
        chain_length -= 2

        # This is a convention used in fastcluster.
        if x > y:
            x, y = y, x

        # get the original numbers of points in clusters x and y
        nx = size[x]
        ny = size[y]

        # Record the new node.
        Z[k, 0] = x
        Z[k, 1] = y
        Z[k, 2] = current_min
        Z[k, 3] = nx + ny
        size[x] = 0  # Cluster x will be dropped.
        size[y] = nx + ny  # Cluster y will be replaced with the new cluster

        indices[y] |= indices[x]
        indices[x] = set()

        aaa=1

        # Update the distance matrix.
        for i in range(n):
            ni = size[i]
            if ni == 0 or i == y:
                continue
                
            # D[condensed_index(n, i, y)] = max(D[condensed_index(n, i, x)], D[condensed_index(n, i, y)])  # complete linkage

            all_indices = indices[y] | indices[i]
            
            # max_idx = max(all_indices)
            # mm = [[dists[condensed_index(n, j, k)] for k in all_indices if j < k] for j in all_indices - {max_idx}]            
            # for row in mm:
            #     print(row)
            # print(y, i, min(max(dists[condensed_index(n, j, k)] for k in all_indices if j < k) for j in all_indices - {max_idx}))
            # print()

            D[condensed_index(n, i, y)] = min(max(dists[condensed_index(n, j, k)] if j!=k else 0 for k in all_indices) for j in all_indices)

            aaa=1
            
            # 要 implement minimax 需要知道 x y 裡各有哪些原本資料點的 index，
            # 原本的 distance matrix 要從 dists 裡拿，因為 D 裡的值會一直被覆蓋過去

            # watch D matrix: [[(i, j, D[condensed_index(12, i, j)]) for j in range(12) if i>j] for i in range(12)]

    # Sort Z by cluster distances.
    order = np.argsort(Z_arr[:, 2], kind='mergesort')
    Z_arr = Z_arr[order]

    # Find correct cluster labels inplace.
    label(Z_arr, n)

    return Z_arr


if __name__ == "__main__":
    X = [[0, 0], [0, 1], [1, 0], [0, 4], [0, 3], [1, 4], [4, 0], [3, 0], [4, 1], [4, 4], [3, 4], [4, 3]]
    Z = minimax(pdist(X))

    fig, ax = plt.subplots(1, 1, figsize=(5, 8))
    hierarchy.dendrogram(Z, ax=ax, orientation='left')
    ax.set(title='Dendrogram with Complete Linkage')
    plt.show()

    print(DataFrame(Z))
