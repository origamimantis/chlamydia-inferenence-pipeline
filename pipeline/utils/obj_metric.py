#!/usr/local/bin/python3

"""
comparison.py

Contains defined methods for computing object level metrics for predictions by computing
certain cardinalities between each labeled obj
    1. True Positive (TP)
    2. Partial Detection (PD)
    3. False Merging (FM)
    4. False Positive (FP)
    
and then uses these to compute score like harmonic mean (F-score) or other metrics to quantify
obj level prediction performance

paper ref -  "Rethinking Task and Metrics of Instance Segmentation on 3D Point Clouds"
                Kosuke Arase| Yusuke Mukuta | Tatsuya Harada
-----------------------------------------------------------------------------
 Author: Akshay Kulkarni -- Date: 12/2020
-----------------------------------------------------------------------------

"""
import os
import argparse
import matplotlib.pyplot as plt
from skimage import data, filters, measure, morphology
from skimage.util import img_as_ubyte
from skimage import io
import numpy as np
import glob
import cv2
import numba 

from skimage import measure
from skimage.util import img_as_ubyte
from skimage import io
import numpy as np
from collections import namedtuple

import numba 


def img_seq2stack(path , scale_percent=None):
    im_arr_list = []
    im_file_list = sorted(glob.glob(path))
    for i in (im_file_list):
        n = cv2.imread(i, 0)
        if scale_percent:
            #calculate the 50 percent of original dimensions
            width = int(n.shape[1] * scale_percent / 100)
            height = int(n.shape[0] * scale_percent / 100)
            # resize image
            n = cv2.resize(n, (width, height))
        im_arr_list.append(n)
    return np.stack(im_arr_list, axis=0)


@numba.jit(nopython=True, parallel=True, fastmath=True)
def IntersectionOverSet(a,b):
    '''
    Asymetric fucntion to compute overlap of one array with other
    
    IoS(A,B) = N(A∩B)/ N(A)
    
    '''
    n_ab = np.sum(np.logical_and(a,b))
    n_a = np.sum(a)
    
    if n_a == 0 or n_ab == 0:
        return 0.0
    else:
        return n_ab/n_a
    

    
def MarkMappings(gt2pred, pred2gt, ret_fields = False):
    results = {k:[0,0,0,0] for k in pred2gt.keys()}
    fields = ['TP', 'PD', 'FP', 'FM']
    
    for gi, g2p in gt2pred.items():
        for p in g2p:
            if gi in pred2gt[p]:
                results[p][0] += 1  # Mark True Positive
            else:
                results[p][1] += 1  # Mark Partial Positive
    
    for pi, p2g in pred2gt.items():
        if len(p2g) == 0 and results[pi] == [0,0,0,0]:
            results[pi][2] += 1  # Mark False Positive
        
        for g in p2g:
            if pi not in gt2pred[g]:
                results[pi][3] += 1 # Mark False Merging
    if ret_fields:
        return results, fields
    else:
        return results

    
def compute_obj_metrics(gt, pred, threshold=0.5, fields = True):
    '''
    Function to a map from the GTs to the prediction outputs (gt2pred) 
    that describes which prediction outputs are contained in each GT, 
    and conversely calculate a map from the prediction outputs to the GTs (pred2gt)
    
    
    Input: 2 numpy arrays with each value labeled according to their pixel instance label 
    
    '''
    gt_labels = gt
    pred_labels = pred
    
    gt2pred_map = {i:[] for i in range(1,gt_labels.max() + 1)}   # map from GT to preds
    pred2gt_map = {i:[] for i in range(1,pred_labels.max() + 1)}   # map from pred to GTs
    
    
    for g_i in range(1, gt_labels.max() + 1):
        
        g = (gt_labels == g_i)  # Masking to keep only the refernced obj 
        
        contained_preds = np.unique(pred_labels[g]) # reducing search space (only iterating over preds in G)
        
        # Removing background label 0
        contained_preds = contained_preds[1:] if contained_preds[0] == 0 else contained_preds 
        
        for p_i in contained_preds:
            
            p = (pred_labels == p_i)
            
            if IntersectionOverSet(g,p) >= threshold: # obj in G is included in obj in P
                pred2gt_map[p_i].append(g_i)
                
            if IntersectionOverSet(p,g) >= threshold: # obj in P is included in obj in G
                gt2pred_map[g_i].append(p_i)           
    
    
    mapping, colnames = MarkMappings(gt2pred_map,pred2gt_map, ret_fields=fields)
    
    TP = sum([l[0] for l in mapping.values()])
    # Defined as the ratio of TP to the number of prediction objs
    obj_precision = TP / pred_labels.max()
    
    # Defined as the ratio of TP to the number of ground truth objs
    obj_recall = TP / gt_labels.max()
    
    results = {
        'total_preds': pred_labels.max(),
        'total_gts': gt_labels.max(),
        'tag_map': mapping,
        'map_colnames':colnames,
        'object_wise_precision': obj_precision,
        'object_wise_recall': obj_recall,
        'F1' : 2*((obj_precision*obj_recall)/(obj_precision+obj_recall))
        }
    
    return results 


def print_result_summary(res):
    import pandas as pd
    
    print('\n'+"-"*20)
    result, cols = res['tag_map'], res['map_colnames']

    result_df = pd.DataFrame.from_dict(result, orient='index',
                       columns=cols, dtype='int16')
    
    [print(k ,'=>', res[k]) for k in res if k != 'tag_map']
    print(result_df)
    print('\nCounts \n{}'.format(result_df.sum()))
    print('\n'+"-"*20)
    pass

      
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description=''' PRED2IMOD 
                                        - Convert Predictions to IMOD contours as a .mod file ''')
    
    # Add the arguments
    parser.add_argument('input_gt',
                        type=str,
                        help='the path to folder of input gt')
    
    parser.add_argument('input_pred',
                        type=str,
                        help='the path to folder of input predictions')
    
    parser.add_argument('-t',
                        '--thresh',
                        action='store_true',
                        help='threshold for input predictions')
    
    
    args = parser.parse_args()
    
    print('Reading GT and Pred')

    gt = img_seq2stack('{}/*.png'.format(os.path.abspath(args.input_gt)))
    preds = img_seq2stack('{}/*.png'.format(os.path.abspath(args.input_pred)))


    gt_labels = measure.label(gt, connectivity=1)
    pred_labels = measure.label(preds, connectivity=1)
    
    print('Computing Metrics')

    res = compute_obj_metrics(gt_labels, pred_labels)
    

    print_result_summary(res)
    
    print('done')