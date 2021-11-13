import datetime
import pickle
import sys

a = datetime.datetime.now()
with open(sys.argv[1], "wb") as pkf:
    pickle.dump(a, pkf)
