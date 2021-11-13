
import numpy as np
import mrcfile
from utils.im_utils import load_stack
from skimage import measure
from get_voxel_spacing import getspacing

img = load_stack("/output/finalstack.mrc");
bboxes = {}

labeller = {"RB":1, "DB":2}

with open("/output/autoseg_detections_classfied.csv") as the_file:
    the_file.readline()
    for line in the_file:
        x = line.split(",")
        label = int(x[0])
        clas = x[20].strip()
        bbox = eval((",".join(x[1:7]))[1:-1] )
        bboxes[label] = [bbox, clas]
        
for lab, (b1, clas) in bboxes.items():
    # focus the window to the bounding box
    window = img[b1[0]:b1[3], b1[1]:b1[4], b1[2]:b1[5]]

    # get connected components aka objects
    labelled = measure.label(window, background=0)
    
    # get all the connected components in the image. discard 0, since that is the background.
    # this sorting thing is probably overkill, but the number of things being sorted is so small it prolly doesn't matter
    c = list(zip(*np.unique(labelled, return_counts=True)))
    c.sort(key = lambda x: x[0])
    c = c[1:]

    # the object with the largest volume in the bounding box is the one we focus on
    obj_label = max(c, key = lambda x: x[1])[0]

    # write the box back to the image
    img[b1[0]:b1[3], b1[1]:b1[4], b1[2]:b1[5]][np.nonzero(labelled == obj_label)] = labeller[clas]

print(np.unique(img))

with mrcfile.new(f'/output/labelled.mrc',overwrite=True) as the_file:
    the_file.set_data(img)
    the_file.voxel_size = getspacing("/input/input.mrc")