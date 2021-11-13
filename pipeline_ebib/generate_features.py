import numpy as np
from scipy.stats import describe, entropy
from skimage.feature import greycomatrix, greycoprops
import matplotlib.pyplot as plt

def getfeatures(img, mrc):
	mrcmin=np.nanmin(mrc[np.nonzero(mrc)])
	mrcrange=(np.nanmax(mrc)-mrcmin)
	res = {}
	
	r = describe(img, axis=None, nan_policy="omit")._asdict()
	scaledimg = (img[np.isnan(img) == False]-mrcmin)/mrcrange
	hist = np.histogram(scaledimg)
	for feat in ["skewness", "kurtosis", "mean", "variance"]:
		res[feat] = r[feat]

	r2 = describe(scaledimg, axis=None, nan_policy="omit")._asdict()
	for feat in ["skewness", "kurtosis", "mean", "variance"]:
		res["hist_"+feat] = r2[feat]

	res["entropy"] =  entropy(img[np.isnan(img) == False].flatten(), axis=None)

	res["voxel_volume"] =  np.sum(np.isnan(img) == False)

	res["range"] = (np.nanmax(img)-np.nanmin(img[np.nonzero(img)])) / mrcrange
	res["scaledmean"] = np.nanmean(img) / mrcrange
	res["scaledvar"] = np.nanvar(img) / mrcrange
	#glcm = greycomatrix(img, distances=[1], angles=[0])

	#for glcmfeat in ["homogeneity",  "contrast", "dissimilarity", "ASM", "correlation"]:
	#	res[f"glcm_{glcmfeat}"] = greycoprops(glcm, glcmfeat)

	return res


