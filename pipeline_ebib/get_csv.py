
import numpy as np
import mrcfile
import pandas as pd
import os
import sys
from im_utils import load_stack
import  matplotlib.pyplot as plt
from skimage import measure
from get_voxel_spacing import getspacing
from generate_features import getfeatures
from tqdm import tqdm
import math


SAVE = False



if not os.path.exists("csvs"):
	os.makedirs("csvs")

imgf = "/output/ebib_finalstack.mrc"

mrcf = "/input/input.mrc"
basename = imgf.split('/')[-1].split('.')[0]
hpi = imgf.split('/')[0]

print(f"Running {basename}")

img = load_stack(imgf)
mrc = load_stack(mrcf)


vs = getspacing(mrcf)

prod = vs[0]*vs[1]*vs[2]
minvol = math.floor(2500000000.0 / prod)

data = []

mrcmin=np.nanmin(mrc[np.nonzero(mrc)])
mrcrange=(np.nanmax(mrc)-mrcmin)


# get connected components aka objects
labelled, counts = measure.label(img, background=0, return_num = True, connectivity=1)
bodies = np.unique(labelled)[1:]  # remove background value of 0

dropped = []



for i in tqdm(bodies):
	indices = np.nonzero(labelled == i)
	z,y,x = indices
	if ( len(x) < minvol ):
		continue

	b1 = ( np.min(z), np.min(y), np.min(x), np.max(z), np.max(y), np.max(x))

	# focus the window to the bounding box
	focusedmask = labelled[b1[0]:b1[3]+1, b1[1]:b1[4]+1, b1[2]:b1[5]+1] == i
	focusedimg = mrc[b1[0]:b1[3]+1, b1[1]:b1[4]+1, b1[2]:b1[5]+1]
	finalimg = focusedimg * focusedmask * 1.0
	finalimg[finalimg == 0] = np.nan

	features = getfeatures(finalimg, mrc)
	features["bbox"] = str(b1)
	features["hpi"] = hpi
	features["dataset"] = basename
	features["groundtruth"] = ""

	data.append(features)

	if SAVE:
		name = f"sus/{label}_{i}"
		#if not os.path.exists(name):
		#	os.makedirs(name)
		#for zz in range(finalimg.shape[0]):
		#	plt.imsave(f"{name}/{zz}.png", finalimg[zz], cmap="gray")
		with mrcfile.new(f'{name}.mrc',overwrite=True) as the_file:
			the_file.set_data(finalimg)
			the_file.voxel_size = vs
		values = finalimg.flatten()
		plt.hist(values)
		plt.savefig(f"{name}_hist.png")
		plt.clf()

		print(f"saved {name}")


print("dropped")
print(dropped)
print()
things = pd.DataFrame(data)
csvname = f"/output/ebib_values.csv"
things.to_csv(csvname)
print(f"saved to {csvname}")
