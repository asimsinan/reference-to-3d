"""Grid-search keys_layout.py's four numbers so cap rectangles sit on bright caps and gaps on dark lines."""
import cv2, numpy as np, subprocess, json, itertools, sys
t=cv2.imread('tex/deck.png'); g=cv2.cvtColor(t,cv2.COLOR_BGR2GRAY).astype(np.float32)
hp=g-cv2.GaussianBlur(g,(0,0),25)
def layout(L,R,TOP,P,G=13):
    ns={'L':L,'R':R,'TOP':TOP,'P':P,'G':G}
    src=open('keys_layout.py').read(); body=src[src.index('u=(R-L)/14.5'):src.index('json.dump')]
    exec(body,ns); return ns['keys']
def score(keys):
    s=0
    for x0,y0,x1,y1 in keys:
        x0,y0,x1,y1=int(x0),int(y0),int(x1),int(y1)
        s+=hp[y0+4:y1-4,x0+4:x1-4].mean()-0.5*(hp[y0-6:y0-1,x0:x1].mean()+hp[y1+1:y1+6,x0:x1].mean())
    return s/len(keys)
best=None
for L,R,TOP,P in itertools.product(range(80,126,3),range(1765,1812,3),range(30,80,3),[116.5,117.5,118.5,119.5]):
    sc=score(layout(L,R,TOP,P))
    if best is None or sc>best[0]: best=(sc,L,R,TOP,P)
print(best)
