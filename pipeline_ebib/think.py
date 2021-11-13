
import numpy as np
import mrcfile
import sys
from im_utils import load_stack
from skimage import measure
from get_voxel_spacing import getspacing

img = load_stack("sus/EB_10.mrc")

print(np.unique(img))
