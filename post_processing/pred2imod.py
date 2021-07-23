#!/usr/local/bin/python3

import os
import sys
from shutil import which
import subprocess

import cv2
import h5py
import skimage
import numpy as np
import skimage.morphology
import argparse
import numpy as np
import glob
import mrcfile as mrc

from colorama import Fore, Style
from tqdm import trange, tqdm

def load_file(file_path, ret_size=False):
    name_with_path, ext = os.path.splitext(file_path)
    img_stack = []
    im_size = None
    if ext == '.mrc':
        with mrc.open(file_path) as f:
            img_stack = f.data.copy()
            im_size = img_stack.shape
            print('\nSuccessfully read {}x{} sized mrc file with {} slices.\n'.format(im_size[1], im_size[2], im_size[0]))
    elif ext.lower() in ['.png', '.tif', '.tiff']:
        ret_flag, image = cv2.imreadmulti(file_path, flags=cv2.IMREAD_GRAYSCALE)
        if ret_flag is True:
            im_array = np.array(image)
            img_stack = np.expand_dims(im_array, axis=len(im_array.shape))
            im_size = img_stack.shape
            print('\nSuccessfully read {}x{} image file with {} frames.\n'.format(im_size[1], im_size[2], im_size[0]))
        else:
            raise Exception("Something went wrong while loading the file")
    elif ext == '.h5':
        print('Reading H5 image file', file_path, '\n')
        h5file = h5py.File(file_path, 'r')
        img_stack = np.array([np.stack((h5file[key].value,), axis=-1) for key in h5file.keys()])
        im_size = img_stack.shape
        # TODO: .h5 reading is probably currently broken, need to fix  -- (A.K.)

    if ret_size:
        return img_stack, im_size
    else:
        return img_stack

def loadStack(path):
    """
    Function to take in a path and read all png/tif/tiff/h5 image files
    :param img_path: str path to folder
    :return: np.ndarray for all images in folder assuming processing is done on each 2d array
    """

    # match & read filenames conforming to regex (possible additional feature for user to filter input)
    match_all = '*'
    supported_extensions = ['.png', '.tif', '.tiff', '.h5', '.mrc']
    image_size = None
        
    list_files = []
    if os.path.isdir(path):
        path = os.path.join(path, match_all)
        for extension in supported_extensions:
            list_files.extend(glob.glob(os.path.join(path + extension)))
    else:
        list_files = glob.glob(os.path.join(path))
    
    if len(list_files) == 0:
        raise("No folder/file matches found for given input path/pattern")

    
    stack = []
    for file in sorted(list_files):
        im, cur_size = load_file(file, ret_size=True)
        if image_size is None:
            image_size = im[0].shape
        elif image_size != cur_size[-2::]:
            raise Exception("Input has different sized images/slices. All images need to have same Width & Height")
        stack.extend(im)

    return np.array(stack)


def convert_to_mod(stack_path, e_thresh, out_path):
    IMODAUTO_INSTALLATION = which('imodauto')

    if IMODAUTO_INSTALLATION is None:
        raise("Could not find imodauto executable. Make sure IMOD is installed and is included in $PATH")

    subprocess.run(['imodauto', '-m' , '1', '-h', str(e_thresh), stack_path, "{}".format(out_path)], check=True, stdout=subprocess.DEVNULL)

    # print("Done.")


def join_mods(mod_list, out_path):
    IMODAUTO_INSTALLATION = which('imodjoin')

    if IMODAUTO_INSTALLATION is None:
        raise("Could not find imodjoin executable. Make sure IMOD is installed and is included in $PATH")

    cmd = ['imodjoin', '-c'] + mod_list + [out_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def write_temp_mrc(arr, path, spacing=None):
    # os.unlink(f"{path}/temp.mrc")
    try:
        with mrc.new("{}/temp.mrc".format(path), overwrite=True) as f:
            f.set_data(arr)
            f.voxel_size = spacing if spacing is not None else (1,1,1)
    except:
        e = sys.exc_info()[0]
        print(e)

if __name__ == '__main__':
    
    bbar_frmt = "{l_bar}%s{bar}%s{r_bar}" % (Fore.BLUE, Fore.RESET)
    gbar_frmt = "{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Fore.RESET)


    # Create the parser
    parser = argparse.ArgumentParser(description=''' PRED2IMOD 
                                        - Convert Predictions to IMOD contours as a .mod file ''')
    
    # Add the arguments
    parser.add_argument('input_path',
                        type=str,
                        help='the path to folder of input predictions')
    
    parser.add_argument('output_path',
                        type=str,
                        help='the path to save the generated mod files')
    
    parser.add_argument('-l',
                        '--label',
                        type=int,
                        nargs='*',
                        help='use imodauto on a specific labels in the input')
    
    parser.add_argument('-j',
                        '--join-mods',
                        action='store_true',
                        help='enable verbose error outputs')

    parser.add_argument('-s',
                        '--spacing',
                        default=None,
                        type=int,
                        nargs=3,
                        help='set pixel spacing (in Angstroms) for the input mrc so the mod file is genereated accordingly')
    
    # -----------------------------
    # Not used currently
    parser.add_argument('-o',
                        '--options',
                        type=int,
                        nargs='*',
                        help='options to modify input or pass to the inner imodauto call')

    args = parser.parse_args()

    input_path = args.input_path
    out_path = os.path.abspath(args.output_path)

    # print(vars(args))


    if not os.path.isdir(input_path):
        if os.path.splitext(input_path)[-1] in ['.mrc', '.tif']:
            input_stack = load_file(input_path)
        else:
            print('The path specified does not exist')
            sys.exit(1)
    else:
        input_stack = loadStack(input_path)


    if not os.path.isdir(out_path):
        os.mkdir(out_path)
        
    if args.label is not None:
        num_labels = [args.label]
    else:
        num_labels = np.unique(input_stack)
        num_labels = num_labels[1:]


    print("\nProcessing objects/labels: {}".format(len(num_labels))) 


    TEMP_MRC_FOLDER = "{}/temp".format(out_path)
    for i in trange(len(num_labels), file=sys.stdout, ncols=100, desc="Processing",
                   bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Fore.RESET), position=0, leave=True):

        l = num_labels[i]
        arr = np.where(input_stack == l, input_stack, 0)
        write_temp_mrc(arr, out_path, spacing=args.spacing)
        
        convert_to_mod("{}/temp.mrc".format(out_path), l, "{}/label_{}.mod".format(out_path, l))


    if args.join_mods:
        mods = glob.glob("{}/*.mod".format(out_path))
        print("Combining all mod files")
        join_mods(sorted(mods), "{}/COMBINED.mod".format(out_path))


    os.unlink("{}/temp.mrc".format(out_path))

    print("Finished!")
 