"""outline of chosen parts over a photo crop: ovpart.py view x0 y0 x1 y1 scale out.jpg part1,part2"""
import cv2,numpy as np,sys,geom,camlib
from overlay import sil
v=sys.argv[1];x0,y0,x1,y1=map(int,sys.argv[2:6]);s=float(sys.argv[6]);P=geom.parts(geom.load());im=cv2.imread(v+'.jpg')
im=cv2.resize(im[y0:y1,x0:x1],(0,0),fx=s,fy=s,interpolation=cv2.INTER_CUBIC)
cols=[(0,255,0),(255,255,0),(255,0,255),(0,200,255)]
for i,k in enumerate(sys.argv[8].split(',')):
    for kk in [q for q in P if q.startswith(k)]:
        m=sil(v,*P[kk])[y0:y1,x0:x1];m=cv2.resize(m,(0,0),fx=s,fy=s,interpolation=cv2.INTER_NEAREST)
        cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);cv2.drawContours(im,cs,-1,cols[i%4],1)
cv2.imwrite(sys.argv[7],im)
