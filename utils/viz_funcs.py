#!/usr/local/bin/python3

import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
from skimage import measure

# helper function to plot multiple imgs

def imshowgrid(*imarrays, ncols=1, figsize=(15,15), title_list=None, cmap=None):
    
    assert isinstance(ncols, int), "number of cols must be an int but {} was supplied".format(ncols)
    if cmap is None:
        cmap = 'viridis'
    n_imgs = len(imarrays)
    blanks =[]
    if ncols is not 1:
        quo, rem = n_imgs//ncols, n_imgs%ncols
        if rem is not 0:
            nrows = quo+rem
            # specifying blank plot spaces
            blanks = [(nrows-1,ncols-1-j) for j in range(rem)]
        else:
            nrows = quo
    else:
        nrows = n_imgs
                   
    fig, ax = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, squeeze=False)
    idx = 0
    for i in range(nrows):
        for j in range(ncols):
            if (i,j) in blanks:
                ax[i][j].axis('off')
            else:
                ax[i][j].imshow(imarrays[idx], cmap=cmap)
                idx+=1

    plt.show()


def render_mesh(obj, spacing=(1.0, 1.0, 1.0), full_scene=False, ret_obj=False, hovertext=None, flip_y=False, opacity = 1):
    # Download data set from plotly repo
    verts, faces, _, _ = measure.marching_cubes(obj, spacing = spacing)
    z, y, x = verts.T
    i, j, k = faces.T    
    if flip_y:
        y_range = [obj.shape[1]-1, 0]
        full_scene = True
    else:
        y_range = [0,obj.shape[1]-1]
    
    if full_scene is True:
        layout=go.Layout(showlegend=True, margin=dict(l=0, r=0, t=0, b=0),
                          #paper_bgcolor = 'black',
                          scene = dict(xaxis=dict(title='H', 
                                                  titlefont_color='black', 
                                                  range=[0,obj.shape[2]-1], 
                                                  backgroundcolor='white',
                                                  color='black',
                                                  gridcolor='gray'),
                                       yaxis=dict(title='W',
                                                  titlefont_color='black',
                                                  range=y_range,
                                                  backgroundcolor='white',
                                                  color='black',
                                                  gridcolor='gray'
                                                  ),
                                       zaxis=dict(title='Z', 
                                                  range=[0,obj.shape[0]-1],
                                                  backgroundcolor='white',
                                                  color='black', 
                                                  gridcolor='gray'
                                                 )
                                      )
                        )
    else:
        layout = None
    
    
    fig_obj = go.Mesh3d(
            x=x, y=y, z=z,
            i=i, j=j, k=k,
            hovertext=hovertext,
            opacity = opacity
        
    )
    
    
    if ret_obj:
        return fig_obj
    else:
        fig = go.Figure(data=[fig_obj], layout = layout)
        fig.show(width=1500, height=1500, autosize=False)
    

def get_matched_mask(source_label,sourceArr, targetArr):
    temp = np.zeros_like(targetArr, dtype='bool')
    for i in np.unique(targetArr[sourceArr == source_label]):
        print(i)
        if i != 0:
            temp = np.logical_or(temp, (targetArr == i))
    return temp