
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


SAVE = False



if not os.path.exists("csvs"):
	os.makedirs("csvs")

imgf = sys.argv[1]
mrcf = sys.argv[2]
basename = imgf.split('/')[-1].split('.')[0]
hpi = imgf.split('/')[0]

print(f"Running {basename}")

img = load_stack(imgf)
mrc = load_stack(mrcf)
vs = getspacing(mrcf)

labeller = {"EB":128, "IB":255}

n_eb = 0
n_ib = 0



data = []


mrcmin=np.nanmin(mrc[np.nonzero(mrc)])
mrcrange=(np.nanmax(mrc)-mrcmin)

for label in ["EB","IB"]:

	# get connected components aka objects
	labelled, counts = measure.label(img == labeller[label], background=0, return_num = True, connectivity=1)
	print(f"{label}: found {counts}")

	for i in tqdm(range(1, counts+1)):
		indices = np.nonzero(labelled == i)
		z,y,x = indices
		b1 = ( np.min(z), np.min(y), np.min(x), np.max(z), np.max(y), np.max(x))

		# focus the window to the bounding box
		focusedmask = labelled[b1[0]:b1[3], b1[1]:b1[4], b1[2]:b1[5]] == i
		focusedimg = mrc[b1[0]:b1[3], b1[1]:b1[4], b1[2]:b1[5]]
		finalimg = focusedimg * focusedmask * 1.0
		finalimg[finalimg == 0] = np.nan

		features = getfeatures(finalimg, mrc)
		features["bbox"] = str(b1)
		features["hpi"] = hpi
		features["dataset"] = basename
		features["groundtruth"] = label

		data.append(features)

		plt.hist((finalimg[np.isnan(finalimg) == False]-mrcmin)/mrcrange)
		plt.savefig(f"hists/{label}/{i}.png")
		plt.clf()
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


things = pd.DataFrame(data)
csvname = f"csvs/{basename}.csv"
things.to_csv(csvname)
print(f"saved to {csvname}")
