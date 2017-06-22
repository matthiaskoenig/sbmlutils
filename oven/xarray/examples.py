"""
Some xarray examples to work with flux data and samples
"""

import xarray as xr
import pandas as pd
import numpy as np

np.zeros([1,2])


df1 = pd.DataFrame(data=[[1,2,3], [4,5,6]], columns=['min', 'max', 'flux'], index=["R1", "R2"])
df2 = pd.DataFrame(data=[[-1,-2,-3], [-4,-5,-6]], columns=['min', 'max', 'flux'], index=["R1", "R2"])

dsets = [
    df1, df2
]


# min, max, flux
# s1, s2, s3, .....


e = np.empty((dsets[0].shape[0], dsets[0].shape[1], len(dsets)))

for k, df in enumerate(dsets):
    # copy data frame data in 3D numpy array
    e[:][:][k] = df.T

print(e)
