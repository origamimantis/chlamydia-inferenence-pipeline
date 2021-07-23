import os
import numpy as np
import pandas as pd
from skimage import measure


from utils.stack_preprocess import get_padded_3D_bbox
from genprops import compute_properties

def generate_feature_table(input_stack, voxel_size=None, props=None, ret_fulldf=False):
    ''' Function to loop over unique objects to compute features for downstream classifier'''
    
    def sphericity(arr, diam):
        sp_ar = 4*(np.pi*((diam/2)**2))
        v,f,_,_ = measure.marching_cubes(arr)
        mesh_ar = measure.mesh_surface_area(v,f)
        return sp_ar/mesh_ar
    
    final_df = None
    
    for label in np.unique(input_stack)[1:]:
        obj_labeled = measure.label(np.uint8(input_stack == label), connectivity=1)    
            
        if not props:
            props = ['label', 'bbox', 'centroid', 'area', 'solidity', 'extent','major_axis_length', "minor_axis_length", 'equivalent_diameter']
    
        print(f"\ncomputing props for label-{label} with num objs " , len(np.unique(obj_labeled))-1 )
    
        obj_df = compute_properties(labeled_data=obj_labeled, prop_names=props, ret_df=True, verbose=False)
        
        print("computing sphericity")
        sp = []
        for i,d in zip(obj_df.label, obj_df.equivalent_diameter):
            print(i, end='\r', flush=True)
            obj_arr = np.uint8(obj_labeled == i)
            
            obj_cropped = obj_arr[get_padded_3D_bbox(obj_arr,zpadding=1, xypadding=5, ret_np_slice=True)]
                
            sp.append(sphericity(obj_cropped,d))
        
        obj_df['sphericity'] = sp
        
        print("Done")
        obj_df['gt_label'] = label
        
        if final_df is None:
            final_df = obj_df.copy()
        else:
            final_df = pd.concat([final_df, obj_df], ignore_index=True)
    
    
    # filter contours
    z_lb = 4
    
    print(f'dropping objs with less than {z_lb} -  shape =',final_df.shape)
    final_df['zspan'] = [i[3]-i[0] for i in final_df['bbox']]
    
    final_df = final_df[final_df.zspan > z_lb]
    print('shape =',final_df.shape)
    
    final_df['axial_ratio'] = final_df['minor_axis_length']/final_df['major_axis_length']
    
    print("Before dropping NAs and 0 labels")
    print(final_df.shape)
    final_df = final_df.dropna()
    print("After dropping NAs and 0 labels")
    print(final_df.shape)    
    
    
    
    # Atribute modification 
    if voxel_size is not None:
        vx, vy, vz = voxel_size
        print(f"using voxel sizes given: X = {vx}, Y = {vy}, Z= {vz} ")
        final_df['volume_um3'] = final_df.area * (vx*vy*vz) * 1e-12

    
    return final_df