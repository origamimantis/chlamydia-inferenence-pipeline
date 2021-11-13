
import numpy as np
import mrcfile
from im_utils import load_stack
from skimage import measure
from get_voxel_spacing import getspacing
import sys


imagfile = "/input/28hpi/msks/3View_5194413_incl5.mrc"
maskfile = "/input/28_5194413_5/finalstack.mrc"
predfile = "/input/scuffed_ebib/3View_5194413_incl5_predictions.csv"

img = load_stack(maskfile)



# this won't be needed for predicted masks
# probably a slight overlap
for val in np.unique(img):
    if val not in [0, 128, 255]:
        img[img == val] = 0
img = np.array((img != 0), dtype = np.int16)
print(np.unique(img, return_counts=True))



bboxes = {}

labeller = {"EB":1, "IB":2}

with open(predfile) as the_file:
    the_file.readline()
    for line in the_file:
        x = line.split(",")
        label = int(x[0])
        clas = x[-1].strip()
        bbox = eval((",".join(x[15:21]))[1:-1] )
        clas = "EB" if clas == 0 else "IB"
        bboxes[label] = [bbox, clas]
        
for lab, (b1, clas) in bboxes.items():
    #if clas == "IB": continue
    # focus the window to the bounding box
    window = img[b1[0]:b1[3]+1, b1[1]:b1[4]+1, b1[2]:b1[5]+1]
    print(window)
    print(b1)

    # get connected components aka objects
    labelled = measure.label(window, background=0)
    
    # get all the connected components in the image. discard 0, since that is the background.
    # this sorting thing is probably overkill, but the number of things being sorted is so small it prolly doesn't matter
    c = list(zip(*np.unique(labelled, return_counts=True)))
    c.sort(key = lambda x: x[0])
    c = c[1:]

    # the object with the largest volume in the bounding box is the one we focus on
    print(c)
    1/0
    obj_label = max(c, key = lambda x: x[1])[0]

    # write the box back to the image
    img[b1[0]:b1[3], b1[1]:b1[4], b1[2]:b1[5]][np.nonzero(labelled == obj_label)] = labeller[clas]

print(np.unique(img, return_counts=True))

with mrcfile.new(f'/input/28_5194413_5_labelmask.mrc',overwrite=True) as the_file:
    the_file.set_data(img)
    the_file.voxel_size = getspacing(imagfile)
