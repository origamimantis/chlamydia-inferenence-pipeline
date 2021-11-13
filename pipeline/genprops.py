#!/usr/bin/python3

import numpy as np
import pandas as pd
import cv2
import skimage
from skimage import measure
import glob
import argparse
from colorama import Fore, Style
from tqdm import trange, tqdm
import os
import sys
# Create the parser
my_parser = argparse.ArgumentParser(description='')

# Add the arguments
my_parser.add_argument('input_imgs',
                       metavar='i',
                       type=str,
                       help='the path to folder of input predictions')

my_parser.add_argument('output_path',
                       metavar='o',
                       type=str,
                       help='the path to save the generated properties for detected objs')

my_parser.add_argument('-t',
                       '--thresh',
                       type=int,
                       help='threshold for binarization if predictions imgs are non-binary/non-discrete')

my_parser.add_argument('-v',
                       '--verbose',
                       action='store_true',
                       help='enable verbose error outputs')



# Img Loading
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



def compute_properties_alt(labeled_data, prop_names=None, verbose=False, ret_df=True):
    
    if not prop_names:
        prop_names = ['label', 'area', 'solidity','extent','major_axis_length', "minor_axis_length",'equivalent_diameter',"moments_normalized"]
    
    row_list = []
    labels = np.unique(labeled_data)
    labels = labels[1:] # excluding 0
    num_lables = len(labels)
    err_str = ""
    cols = None
    
    if verbose:
            print("setting colnames")
    while cols is None:
        try:
            i = labels[np.random.randint(0,num_lables)]
            props = skimage.measure.regionprops_table(np.uint8(labeled_data==i),properties=prop_names)
            cols = props.keys()
        except Exception as e:
            continue
    
    if verbose:
        print("Cols: ", cols)
    for i in trange(num_lables, file=sys.stdout, ncols=100, desc="Processing",
                   bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Fore.RESET)):
        
        l = labels[i]
        try:
            obj = np.uint8(labeled_data == l)*l
      
            props = skimage.measure.regionprops_table(obj, properties=prop_names)
            
            row_list.append(props)

        except Exception as e:
                err_str += "\nlabel -> {}\n\n{}\n-----------------".format(l, str(e))
                row_list.append({k:(l if k=='label' else None) for k in cols})
    print("\nDone !\n\n")
    
    if verbose:  
        print("Errors:{}".format(err_str))
    
    if ret_df:
        res_df = pd.DataFrame(data=row_list, columns=cols)
        return res_df
    else:
        return row_list, cols
    
def compute_properties(labeled_data, intensity_source_img=None, prop_names=None, verbose=False, ret_df=True):
    
    if not prop_names:
        prop_names = ['label', 'area', 'solidity','extent','major_axis_length', "minor_axis_length",'equivalent_diameter',"moments_normalized"]
    
    row_list = []
    
    num_lables = len(np.unique(labeled_data))-1
    props = measure.regionprops(labeled_data, intensity_image=intensity_source_img)
    err_str = ""
    
    for i in trange(num_lables, file=sys.stdout, ncols=100, desc="Processing",
                   bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Fore.RESET)):
        row = {}
        for prop in prop_names:
            try:
                val = props[i][prop]
                row[prop] = val
            except Exception as e:
                err_str += "\nlabel -> {}\n\n{}\n-----------------".format(i+1, str(e))
                row[prop] = None
        row_list.append(row)
    if verbose:  
        print("Errors:{}".format(err_str))
    
    if ret_df:
        res_df = pd.DataFrame(data=row_list, columns=prop_names)
        return res_df
    else:
        return row_list, prop_names

if __name__ == '__main__':
    
    args = my_parser.parse_args()

    input_path = args.input_imgs
    
    if not os.path.isdir(input_path):
        print('The path specified does not exist')
        sys.exit(1)
    
    input_images = load_stack("{}/".format(input_path))
    
    
    if args.thresh:
        input_images = np.uint8(input_images > float(args.thresh))
    
    
    labeled_stack = measure.label(input_images, connectivity=1)
    
    if args.verbose:
        print(Fore.YELLOW + "\nLoaded Image folder as stack with num_slices: " + "{}".format(input_images.shape[0]))
        print("\nDetected objects/labels: {}".format(labeled_stack.max()))
        print(Style.RESET_ALL)

    
    data, cols = compute_properties(labeled_stack, print_err=True)

    df = pd.DataFrame(data,columns=cols)
    
    out_folder = "{}/output.csv".format(os.path.abspath(args.output_path))
    
    df.to_csv(out_folder)
    if args.verbose:
        print(df.head())
        print('\n\nSaved output file at: ' + Fore.GREEN + '{}'.format(out_folder))
        print(Style.RESET_ALL)
