"""lines.py PHOTO OUT YMIN MINLEN -- LSD segments below YMIN, long ones drawn with ids; prints them."""
import sys, cv2, numpy as np
im=cv2.imread(sys.argv[1]); out=sys.argv[2]; ymin=int(sys.argv[3]); L=float(sys.argv[4])
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
lsd=cv2.createLineSegmentDetector(0)
segs=lsd.detect(g)[0].reshape(-1,4)
keep=[]
for s in segs:
    x0,y0,x1,y1=s; l=np.hypot(x1-x0,y1-y0)
    if l>=L and min(y0,y1)>=ymin and abs(y1-y0)>0.08*l: keep.append(s)
vis=im.copy()
for i,s in enumerate(keep):
    x0,y0,x1,y1=map(int,s); col=tuple(int(c) for c in np.random.RandomState(i).randint(60,255,3))
    cv2.line(vis,(x0,y0),(x1,y1),col,2); cv2.putText(vis,str(i),((x0+x1)//2,(y0+y1)//2),0,0.5,col,2)
    print(i,[round(float(v),1) for v in s])
cv2.imwrite(out,vis[ymin-20:])
