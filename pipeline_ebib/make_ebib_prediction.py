import pickle
import pandas as pd
import numpy as np

dt = None
with open('ebib_rforest.pkl', 'rb') as pkf:
    dt = pickle.load(pkf)

the_csv = pd.read_csv("/output/ebib_values.csv")

to_drop = ["Unnamed: 0", "bbox", "dataset", "groundtruth", "hpi", "mean", "variance"]
x = the_csv.drop(to_drop, "columns")

threshold = 0.85
replace = {0:"EB", 1:"IB"}

pyp = dt.predict_proba(x)[:,1]
pr = np.round(pyp)
cnf = np.array( np.max([pyp, 1-pyp], axis=0) > threshold , dtype=int )

the_csv["pred_proba"] = pyp
the_csv["prediction"] = pr
the_csv["confident"] = cnf

the_csv.to_csv("/output/ebib_predictions.csv")
