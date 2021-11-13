#!/usr/local/bin/python3

import numpy as np

import skimage

from colorama import Fore, Style
from tqdm import trange, tqdm
import os
import sys

def get_padded_3D_bbox(img, zpadding = 1, xypadding = 5, ret_np_slice=False):
    
    def get_bbox_3D(img):
    
        z = np.any(img, axis=(1, 2))
        y = np.any(img, axis=(0, 2))
        x = np.any(img, axis=(0, 1))
    
        ymin, ymax = np.where(y)[0][[0, -1]]
        xmin, xmax = np.where(x)[0][[0, -1]]
        zmin, zmax = np.where(z)[0][[0, -1]]
    

        return zmin, zmax+1, ymin, ymax+1, xmin, xmax+1
    
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


    

def fill_obj(arr,bounds=None, selem=None):
    
    assert arr.max() == 1 , 'input should be a stack with 0s and 1s'
    
    if not bounds:
        bounds = get_padded_3D_bbox(arr, ret_slice_tuple=True)
    else:
        if not all([isinstance(i,slice) for i in bounds]):
            raise Exception('bounds param should be a tuple of all slice() objs')
    
    obj = arr[bounds]
    
    obj = skimage.morphology.closing(obj, selem=selem)
        
    return obj
        
    

def fill_stack_objs(label_arr, selem=None):
    '''
    Function to take each component labeled by skimge.label and perform a 3D morphological 
    closing/filling to complete the object in 3D 
    
    @args:
        label_arr - np.ndarray ( output from skimage.measure.label)
        selem [optional]: skimage struct array like skimage.morphlogy.ball or diam etc
    
    @returns:
        outout - np.ndarray ( same shape as input )
    '''
    
    
    output = np.zeros_like(label_arr, dtype=np.int16)
    
    
    labels = np.unique(label_arr)
    labels = labels[1:] # excluding 0
    
    for i in trange(len(labels), file=sys.stdout, ncols=100, desc="Processing",
                   bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Fore.RESET)):
    
        l = labels[i]
        
        obj = np.uint8(label_arr == l)
        
        bounds = get_padded_3D_bbox(obj, ret_slice_tuple=True)
        
        obj = fill_obj(obj, bounds, selem)
        
        obj = obj * l

        output[bounds] += obj
        
        #TODO: see if the closing can cause overlap of distinct labels
    
    return output
    
    
