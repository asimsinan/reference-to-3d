import json,numpy as np, importlib, camlib
from camlib import *
R=json.load(open('rails.json'))
for k,d in R.items():
    out=[]
    zs=json.load(open("cams.json"))["model"]["zs"]
    for z0 in np.arange(zs-1.6,zs-0.2,0.02):
        ym=np.mean([to_plane_z(k,np.array(s).reshape(2,2),z0)[:,1].mean() for s in d['m']])
        yp=np.mean([to_plane_z(k,np.array(s).reshape(2,2),z0)[:,1].mean() for s in d['p']])
        out.append((round(zs-z0,2),round(ym,2),round(yp,2),round(ym+yp,2)))
    best=min(out,key=lambda t:abs(t[3]))
    print(k,'z0 where symmetric',best, 'gauge',round(best[2]-best[1],2))
