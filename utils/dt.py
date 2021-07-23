#!/usr/local/bin/python3

import edt
import cv2
import skimage
import os
import numpy as np
import skimage.morphology
import argparse
import numpy as np
import glob
from skimage import io, measure
from datetime import datetime

from colorama import Fore, Style
from tqdm import trange, tqdm
import sys


bbar_frmt = "{l_bar}%s{bar}%s{r_bar}" % (Fore.BLUE, Fore.RESET)
gbar_frmt = "{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Fore.RESET)


# Create the parser
parser = argparse.ArgumentParser(description='')

# Add the arguments
parser.add_argument('input_imgs',
                       type=str,
                       help='the path to folder of input predictions')

parser.add_argument('overlap_dist',
                       type=float,
                       help='outward distance from obj boundary to consider for determining overlap')

parser.add_argument('output_path',
                       type=str,
                       help='the path to save the generated DT overlap imgs for detected objs')

parser.add_argument('-m',
                       '--mode',
                       type=int,
                       default=2,
                       help='mode for distance transform algorithm -> 2 for 2D or 3 for 3D')

parser.add_argument('-t',
                    '--thin',
                    type=int,
                    nargs='?',
                    help='perform thinning operation with specified iters - default None')




def load_stack(path):
    """
    Function to take in a path and read all png/tif/tiff/h5 image files
    :param img_path: str path to folder
    :return: np.ndarray for all images in folder assuming processing is done on each 2d array
    """

    # match & read filenames conforming to regex (possible additional feature for user to filter input)
    match_all = '*'
    supported_extensions = ['.png', '.tif', '.tiff', '.h5', '.mrc', '.ali']
    image_size = None

    def load_files(file_path):
        name_with_path, ext = os.path.splitext(file_path)
        img_stack = []
        im_size = None
        if ext in ['.mrc', '.ali']:
            with mrc.open(file_path, "r") as f:
                img_stack = f.data.copy()
                im_size = img_stack.shape
        elif ext.lower() in ['.png', '.tif', '.tiff']:
            ret_flag, image = cv2.imreadmulti(file_path, flags=cv2.IMREAD_GRAYSCALE)
            if ret_flag is True:
                img_stack = np.array(image)
                im_size = img_stack.shape
            else:
                raise Exception("Something went wrong while loading the file")
        elif ext == '.h5':
            print('Reading H5 image file', file_path, '\n')
            h5file = h5py.File(file_path, 'r')
            img_stack = np.array([np.stack((h5file[key].value,), axis=-1) for key in h5file.keys()])
            im_size = img_stack.shape
            # TODO: .h5 reading is probably currently broken, need to fix  -- (A.K.)
        else:
            raise Exception("Unsupported File type {} - file type should be .mrc/png/tif/h5".format(ext))
        return img_stack, im_size
    
    stack = None
    if os.path.isdir(path):
        list_files = []
        path = os.path.join(path, match_all)
        for extension in supported_extensions:
            list_files.extend(glob.glob(os.path.join(path + extension)))
        
        if len(list_files) == 0:
            raise Exception("No folder content/file matches found for given input path/pattern")

        stack = []
        for file in sorted(list_files):
            im, cur_size = load_files(file)
            if image_size is None:
                image_size = im[0].shape
            elif image_size != cur_size[-2::]:
                raise Exception("Input has different sized images/slices. All images need to have same Width & Height")
            stack.extend(im)
        stack = np.array(stack)
    
    else:
        im, cur_size = load_files(os.path.abspath(path))
        stack = im
    
    

    im_size = stack.shape
    print('Successfully read {}x{} image file with total {} frames/slices.'.format(im_size[1], im_size[2], im_size[0]))

    return stack

def get_bbox_3D(img):
    
    z = np.any(img, axis=(1, 2))
    y = np.any(img, axis=(0, 2))
    x = np.any(img, axis=(0, 1))

    ymin, ymax = np.where(y)[0][[0, -1]]
    xmin, xmax = np.where(x)[0][[0, -1]]
    zmin, zmax = np.where(z)[0][[0, -1]]
    

    return zmin, zmax+1, ymin, ymax+1, xmin, xmax+1



def get_padded_3D_bbox(img, zpadding = 5, xypadding = 100):
    
    zlimit, ylimit, xlimit = img.shape

    zmin, zmax, ymin, ymax, xmin, xmax = get_bbox_3D(img)
    
    zmin, zmax = min(abs(zmin-zpadding),zmin), min(zmax+zpadding,zlimit)
    ymin, ymax = min(abs(ymin-xypadding),ymin), min(ymax+xypadding,ylimit) 
    xmin, xmax = min(abs(xmin-xypadding),xmin), min(xmax+xypadding,xlimit) 

    return zmin, zmax+1, ymin, ymax+1, xmin, xmax+1


def thresh_and_skeletonize(img, thresh):
    return skimage.morphology.skeletonize(img > thresh)


def thresh_and_thin(img, thresh, iters):
    if len(img.shape) == 3:
        return np.stack([skimage.morphology.thin(np.uint8(img[i] > thresh), max_iter=iters) for i in range(img.shape[0])], axis=0)
    else:
        return skimage.morphology.thin(img > thresh, max_iter=iters)
    

def dist_transform_overlap(src, thresh_dist, skeletonize_output=False, thin_iters=True):

    labels = measure.label(src, connectivity=1)
    res = np.zeros_like(labels, dtype='uint8')
        
    for l in trange(1,labels.max()+1, file=sys.stdout, ncols=100, desc="Processing", bar_format=bbar_frmt):
        ob = (labels == l)
        
        inv_ob = np.uint8(np.logical_not(ob))
        
        ob_dt = cv2.distanceTransform(inv_ob, cv2.DIST_L2, 3)

        r = np.copy(ob_dt)
        r[r > thresh_dist] = 0
        r[r != 0] = 1
        res += np.uint8(r)    
    
    if skeletonize_output is True:
        res = thresh_and_skeletonize(res, 1)
    elif thin_iters is not None:
        print("\nEroding/Thinning overlap maps for maxiters = 3")
        res = thresh_and_thin(res,1,thin_iters)
    else:
        res = res>1
        
    res = np.uint8(res) * 255
    return res


def dist_transform_overlap_3D(src, thresh_dist, skeletonize_output=False, thin_iters=None):

    labels = measure.label(src, connectivity=1)
    res = np.zeros_like(labels, dtype='uint8')
        
    for l in trange(1,labels.max()+1, file=sys.stdout, ncols=100, desc="Processing", bar_format=bbar_frmt):
        ob = np.uint8(labels == l)
        z1,z2,y1,y2,x1,x2 = get_padded_3D_bbox(ob)
        
        cropped_obj = ob[z1:z2,y1:y2,x1:x2] 

        inv_ob = np.uint8(np.logical_not(cropped_obj))
        
        ob_dt = edt.edt(inv_ob, black_border=False, order='C', parallel=-1)

        r = np.copy(ob_dt)
        r[r > thresh_dist] = 0
        r[r != 0] = 1
        res[z1:z2,y1:y2,x1:x2] += np.uint8(r)    
    
    if skeletonize_output is True:
        res = thresh_and_skeletonize(res, 1)
        
    elif thin_iters is not None:
        print("\nEroding/Thinning overlap maps for maxiters = {}".format(thin_iters))
        res = thresh_and_thin(res,1,thin_iters)
        
    else:
        res = res>1
        
    res = np.uint8(res) * 255
    return res

    
if __name__ == '__main__':
    
    args = parser.parse_args()
  
    #attrs = vars(args)
    #print(', '.join("%s: %s" % item for item in attrs.items()))
    
    input_path = args.input_imgs
    overlap_dist = args.overlap_dist
    if not os.path.isdir(input_path):
        print('\nERROR : The path specified does not exist')
        sys.exit(1)

    input_images = load_stack("{}/".format(input_path))
    out_path = args.output_path
    
    if not os.path.isdir(out_path):
        os.mkdir(out_path)
    else:
        print("\nERROR: output dir already exists ... creating new folder")
        date_string = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        print("new path = ", "{}_{}".format(out_path, date_string))
        out_path = "{}_{}".format(outpath, date_string)

    print(Fore.YELLOW + "\nLoaded Image folder as stack with: num_slices = " + "{}".format(input_images.shape[0]))
    print(Style.RESET_ALL)
        

    
    if args.mode == 3:
        print('\nPerforming 3D DT overlap calculation')
        res = dist_transform_overlap_3D(input_images, overlap_dist, skeletonize_output=False, thin_iters=args.thin)
        
        print('\nSaving imgs as pngs')
        for i in trange(res.shape[0], file=sys.stdout, ncols=100, desc="Processing", bar_format=gbar_frmt):
            
            io.imsave(os.path.join(out_path,"slice_{:03d}_dt_overlap.png".format(i)), res[i],check_contrast=False)
    else:
        print('performing slicewise 2D DT overlap calculation and saving')
        
        for i in trange(input_images.shape[0], file=sys.stdout, ncols=100, desc="Processing", bar_format=gbar_frmt):
            
            res = dist_transform_overlap(input_images[i], overlap_dist, skeletonize_output=False, thin_iters=args.thin) 
            io.imsave(os.path.join(out_path,"slice_{:03d}_dt_overlap.png".format(i)), res,check_contrast=False)
    
    print("Finished")
    