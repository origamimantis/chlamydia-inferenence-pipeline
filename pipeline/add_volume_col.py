import pandas as pd
import numpy as np
from get_voxel_spacing import getspacing

df = pd.read_csv('/output/autoseg_detections_classfied.csv')
print(df["voxel_volume"])

vs = getspacing("/input/input.mrc")
coeff = np.prod(vs)

# voxel spacing as coefficient, and then A^3 -> um^3  A=1e-10, um=1e-6, so the scale is 1e-4, then cube it.
df.insert(13,  "volume_um", df["voxel_volume"]*coeff*1e-12)
df.to_csv("/output/final.csv")
