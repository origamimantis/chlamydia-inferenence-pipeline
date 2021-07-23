#!/usr/local/bin/python3

import numpy as np
import glob
import cv2
import numba
import mrcfile as mrc
import os
import matplotlib.pyplot as plt
import re



def imshow(im, cmap = None):
    plt.figure(figsize=(20,15))
    cmap = "gray" if cmap is None else cmap
    plt.imshow(im,cmap = cmap)
    plt.show()
    
# Img Loading
def imseq2stack(path, flag=-1, scale_percent=None):
    im_arr_list = []
    im_file_list = sorted(glob.glob(path))
    for i in (im_file_list):
        n = cv2.imread(i, flag)
        if scale_percent:
            #calculate the 50 percent of original dimensions
            width = int(n.shape[1] * scale_percent / 100)
            height = int(n.shape[0] * scale_percent / 100)
            # resize image
            n = cv2.resize(n, (width, height))
        im_arr_list.append(n)
    return np.stack(im_arr_list, axis=0)



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


def get_bbox_3D(img, np_slice=False):

    z = np.any(img, axis=(1, 2))
    y = np.any(img, axis=(0, 2))
    x = np.any(img, axis=(0, 1))

    ymin, ymax = np.where(y)[0][[0, -1]]
    xmin, xmax = np.where(x)[0][[0, -1]]
    zmin, zmax = np.where(z)[0][[0, -1]]
    
    res = zmin, zmax+1, ymin, ymax+1, xmin, xmax+1
    
    if np_slice:
        return tuple((slice(res[i],res[i+1]) for i in range(0,len(res),2)))
    else:
        return res 


def get_padded_bbox(img, zpadding = 2, xypadding = 15, ret_np_slice=True):
    

    zlimit, ylimit, xlimit = img.shape

    zmin, zmax, ymin, ymax, xmin, xmax = get_bbox_3D(img)
    
    zmin, zmax = min(abs(zmin-zpadding),zmin), min(zmax+zpadding,zlimit)
    ymin, ymax = min(abs(ymin-xypadding),ymin), min(ymax+xypadding,ylimit) 
    xmin, xmax = min(abs(xmin-xypadding),xmin), min(xmax+xypadding,xlimit) 
    
    result  = zmin, zmax+1, ymin, ymax+1, xmin, xmax+1
    
    if ret_np_slice:
        return tuple((slice(result[i],result[i+1]) for i in range(0,6,2)))
    else:
        return result