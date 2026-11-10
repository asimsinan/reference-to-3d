import sys,numpy as np
from camlib import load
cams=load('cams.json')
# hit.py IMG AXIS VALUE x,y x,y ...
c=cams['r'+sys.argv[1]]; ax='xyz'.index(sys.argv[2]); val=float(sys.argv[3])
for a in sys.argv[4:]:
    x,y=map(float,a.split(',')); print(a,np.round(c.hit(x,y,ax,val),2))
