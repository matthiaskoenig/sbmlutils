"""
Export RMSD matrix with cluster size
"""

import numpy as np

np.random.seed(12345)
N = 4  # number of clusters

# 4 clusters with different numbers of members
cluster_id = ["c1", "c2", "c3", "c4"]
cluster_size = [5, 2, 4, 1]

# RMSD matrix (4 x 4) between all clusters (here just random for simplification)
RMSD = np.random.rand(N, N)

# write network file with edge attribute
with open("cluster-graph.csv", "w") as f:
    f.write("source,target,interaction,directed,RMSD\n")
    for k in range(N):
        for i in range(N):
            f.write("{},{},pp,TRUE,{}\n".format(cluster_id[k], cluster_id[i], RMSD[k, i]))

# write node attribute size
with open("cluster-size.csv", "w") as f:
    f.write("cluster,size\n")
    for k in range(N):
        f.write("{},{}\n".format(cluster_id[k], cluster_size[k]))
