import pickle
import sys

with open(sys.argv[1], "rb") as t0, open(sys.argv[2], "rb") as tf:
    tt0 = pickle.load(t0)
    ttf = pickle.load(tf)

    h,m,s = str(ttf - tt0).split(':')
    h = int(h)
    m = int(m)
    s = round(float(s))
    print(f"{h}h {m}m {s}s")
