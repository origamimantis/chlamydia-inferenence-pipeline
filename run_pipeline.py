#!/usr/bin/env python3

import os 
import re
import glob
from pathlib import Path
from shutil import which

import numpy as np
import pandas as pd
import argparse
import pickle

import mrcfile as mrc
import lightgbm as lgbm

import subprocess

from utils.im_utils import load_stack
from generate_features import generate_feature_table



def get_filename(x):
    return os.path.splitext(os.path.basename(x))[0] 


def get_ids(f):
    '''utility function to get M_IDs from filenames'''
    f = f.split('_')
    res = {'mid':None, 'inclusion':None}
    for t in f:
        if t.isdecimal() and len(t) > 4:
            res['mid'] = int(t)
        if 'inc' in t:
            if re.sub("[^0-9]", "", t) is not "":
                res['inclusion'] = int(re.sub("[^0-9]", "", t))
    return res['mid'],res['inclusion']


def refine_pred_with_edt(input_stack, edt_stack, inc_mask_path=None, pred_t=None, edt_t=None):
    print("\n\nProcessing stack - {}\n".format(input_stack))

    PRED_THRESH =  0.8 if pred_t is None else pred_t
    EDT_THRESH = 0.6 if edt_t is None else edt_t

    pred = load_stack("{}".format(input_stack)) / 255
    edt3d = load_stack("{}".format(edt_stack)) / 255

    edt3d = np.where(edt3d < (EDT_THRESH), 0, edt3d)

    pred_final = pred - edt3d

    pred_final = np.uint8(pred_final > (PRED_THRESH))

    if inc_mask_path:
        inc_mask = load_stack(inc_mask_path)
        pred_final = np.where(inc_mask > 0, pred_final, 0)
    
    return pred_final


def run_classifier(input_stack, classfier_path, output_path, voxel_size=None):
    '''function to run inference on features extracted from seg maps with lgbm classifier'''
    PRED_FEATURE_LIST = ['solidity','extent', 'sphericity', 'axial_ratio']
    rows = []


    lgbm_classifier = lgbm.Booster(model_file=classfier_path)
    # Generate morphological features
    rbdb_feature_df = generate_feature_table(input_stack, voxel_size=voxel_size)

    features = rbdb_feature_df[PRED_FEATURE_LIST].copy()
     
    # run inferece on features with lightGBM model
    pred_probs = lgbm_classifier.predict(features)

    pred_labels = [np.argmax(p) for p in pred_probs]

    pred_labels = ["RB" if l==1 else "DB" for l in pred_labels]

    rbdb_feature_df['prediction'] = pred_labels

    Path(output_path).mkdir(parents=True,exist_ok=True)

    rbdb_feature_df.to_csv("{}/autoseg_detections_classfied.csv".format(output_path), index=False)

    print("DONE")


def run_segmentation(input_imgs, model_dir, output_path, aug_speed=1):
    '''function to call the caffe predictions from shell'''

    CDEEP3M_PREDICTOR_PATH = which('runprediction.sh')

    if not CDEEP3M_PREDICTOR_PATH:
        CDEEP3M_PREDICTOR_PATH = '/home/cdeep3m/runprediction.sh' 
        print("""cdeep3m runpredict not found on path.
        Setting prediction script path to - {}. 
        If this is not intended please make sure runprediction.sh is callable from shell or can be found with `which`""".format(CDEEP3M_PREDICTOR_PATH))
    
    print("Starting prediction run for {}".format(input_imgs))

    subprocess.run(
        [CDEEP3M_PREDICTOR_PATH, "--augspeed {}".format(aug_speed), model_dir, input_imgs, output_path]
        ,shell=True)
    


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(
        description='Program to run segmentation and classification for Rb and DB chlamydial forms',
        epilog="""
            Example usage
            
            python3 run_pipeline.py -inc_mask masks/ tif_imgs/ lgbm_pkl_file/ outputpath
            
            """
    )

    # Add the arguments
    parser.add_argument('normal_pred',
                           type=str,
                           help='the path to folder of input predictions')
    
    parser.add_argument('edt_pred',
                           type=str,
                           help='the path to folder of edt predictions')

    parser.add_argument('-lgbm_model_dir',
                           type=str,
                           help='the path to folder of Lightgbm model')

    parser.add_argument('output_folder',
                           metavar='o',
                           type=str,
                           help='the path to save the generated results/properties for detected objs')

    parser.add_argument('-inc_mask',
                           type=str,
                           default=None,
                           help='the path to inclusion mask inmgs')

    parser.add_argument('-n_t',
                           '--n_thresh',
                           type=float,
                           default=None,
                           help='threshold for binarization of normal preds')

    parser.add_argument('-e_t',
                           '--edt_thresh',
                           type=float,
                           default=None,
                           help='threshold for binarization of distance transform pred')

    parser.add_argument('-v',
                           '--verbose',
                           action='store_true',
                           help='enable verbose error outputs')
    

    args = parser.parse_args()

    # Path("{}/predictions".format(args.output_folder)).mkdir(parents=True)

    # Run CNN predictions on input
    # # NRML
    # run_segmentation(
    #     input_imgs=args.input_imgs,
    #     model_dir=args.nm_model_dir,
    #     output_path="{}/predictions/nrml".format(args.output_folder),
    #     aug_speed=4)

    # # EDT
    # run_segmentation(
    #     input_imgs=args.input_imgs,
    #     model_dir=args.dt_model_dir,
    #     output_path="{}/predictions/edt".format(args.output_folder),
    #     aug_speed=4)

    # Extract features and run classfication on detected objects

    final_stack = refine_pred_with_edt(
        input_stack=args.normal_pred,
        edt_stack=args.edt_pred,
        inc_mask_path=args.inc_mask,
        pred_t=args.n_thresh,
        edt_t=args.edt_thresh,   
    )

    model = "/pipeline/models/lightgbm/rbdb_classifier.lgbmodel" if not args.lgbm_model_dir else args.lgbm_model_dir

    run_classifier(
        input_stack=final_stack,
        classfier_path=model,
        output_path=args.output_folder
    )