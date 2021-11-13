import numpy as np
import mrcfile
from im_utils import load_stack

def threshold_pred(input_stack, mask):
    print("\n\nProcessing stack - {}\n".format(input_stack))

    PRED_THRESH =  240

    pred = load_stack(input_stack)


    pred = np.uint8(pred > (PRED_THRESH))
    pred = np.flip(pred, axis=1)

    msk = load_stack(mask)
    pred = np.where(msk > 0, pred, 0)

    '''
    if inc_mask_path:
        inc_mask = load_stack(inc_mask_path)
        pred_final = np.where(inc_mask > 0, pred_final, 0)
    '''
    with mrcfile.new(f'/output/ebib_finalstack.mrc',overwrite=True) as the_file:
        the_file.set_data(pred)
    return pred

threshold_pred("/output/ebib/ensembled/", "/mask/")
