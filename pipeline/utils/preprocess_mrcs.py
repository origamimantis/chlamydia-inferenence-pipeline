import mrcfile as mrc
import subprocess
import os
import glob

import numpy as np


def bin_to_target(path_regex, target_voxel_size=None):
    stackfiles = sorted(glob.glob(path_regex))
    if target_voxel_size is None:
        TARGET_VOXELS = 360,360,600
    else:
        TARGET_VOXELS = target_voxel_size
    for stack in stackfiles:
        dirn = os.path.abspath(os.path.dirname(stack))
        if not os.path.isdir("{}/binned_to_36-36-60nm".format(dirn)):
            os.mkdir("{}/binned_to_36-36-60nm".format(dirn))
        fname,ext = os.path.splitext(os.path.basename(stack))
        with mrc.open(stack) as s:
            voxelsize = list(s.voxel_size.item())
        xbin, ybin, zbin = [round(i/j) for i,j in zip(TARGET_VOXELS,voxelsize)]
        cmd = "binvol -x {} -y {} -z {} {}/{}{} {}/binned_to_36-36-60nm/{}_binned_x{}y{}z{}.mrc".format(xbin, ybin, zbin, dirn, fname, ext, dirn, fname, xbin, ybin, zbin)  

        subprocess.check_call(cmd, shell=True)

        print('done-',stack)
        


def stack_to_tifs(files):
    for stack in files:
        stack = os.path.abspath(stack)
        dirn = os.path.dirname(stack)
        fname,ext = os.path.splitext(os.path.basename(stack))
        if not os.path.isdir("{}/tif_imgs".format(dirn)):
            subprocess.call("mkdir {}/tif_imgs".format(dirn), shell=True)
        
        tif_path = "{}/tif_imgs/{}_imgs".format(dirn, fname)
        subprocess.call("mkdir {}".format(tif_path), shell=True)
        subprocess.call("mrc2tif -a 0,0 {} {}/slice".format(stack, tif_path), shell=True)
        print('done-',tif_path)



def paint_boundaries(mrc_list):
    for mrc in mrc_list:
        stack = os.path.abspath(mrc)
        dirn = os.path.dirname(stack)
        fname,ext = os.path.splitext(os.path.basename(stack))
        
        mod = "{}/mods/{}.mod".format(dirn, fname)
        inc_mrc_path = "{}/inc_masks".format(dirn)
        
        if not os.path.isdir(inc_mrc_path):
            os.mkdir(inc_mrc_path)
        
        subprocess.call("imodtrans -i {} {} {}".format(stack, mod, mod), shell=True)
        subprocess.call("imodmop -o 1 -pad 10 -mask 255 {} {} {}/{}_boundary_mask.mrc".format(mod, stack, inc_mrc_path, fname), shell=True)
#         print(f"{inc_mrc_path}/{fname}_boundary_mask.mrc")
        print("Done- ",inc_mrc_path)
    


if __name__ == '__main__':

    # bin_to_target('./24hpi/*.ali')
    # bin_to_target('./28hpi/*.ali')
    # bin_to_target('./32hpi/*.ali')


    # paint_boundaries(mrc_list)

