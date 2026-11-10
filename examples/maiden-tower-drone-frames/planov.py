# planov.py Z views... : rectified plan at height Z from each view with the model's terrace/parapet/quay/fort/annex outlines -> g/planov.jpg
import cv2,numpy as np,json,sys
from camlib import load
cams=load('cams.json'); p=json.load(open('params.json')); Z=float(sys.argv[1]); ppm=12; X0,X1,Y0,Y1=-30,24,-34,30
def to_px(x,y): return int((y-Y0)*ppm),int((X1-x)*ppm)
outs=[]
for v in sys.argv[2:]:
    im=cv2.imread('ref/r%s.png'%v); t,ok=cams['r'+v].rectify(im,(X0,Y0,Z),(0,1,0),(1,0,0),Y1-Y0,X1-X0,ppm)
    def poly(pts,col,cl=True): cv2.polylines(t,[np.array([to_px(x,y) for x,y in pts],np.int32)],cl,col,1,cv2.LINE_AA)
    poly(p['terrace'],(0,255,0)); poly(p['quay'],(255,0,0)); F=p['fort']; poly([(F['x0'],F['y0']),(F['x1'],F['y0']),(F['x1'],F['y1']),(F['x0'],F['y1'])],(0,255,255))
    a=p['annex']; poly([(a['x0'],a['y0']),(a['x1'],a['y0']),(a['x1'],a['y1']),(a['x0'],a['y1'])],(255,0,255))
    for m in range(-30,31,5):
        x_,y_=to_px(0,m); cv2.putText(t,str(m),(x_,10),0,0.3,(0,0,255),1); cv2.line(t,(x_,0),(x_,6),(0,0,255),1)
        if X0<=m<=X1: x_,y_=to_px(m,Y0); cv2.putText(t,str(m),(2,y_),0,0.3,(0,0,255),1)
    cv2.putText(t,'r'+v,(4,t.shape[0]-6),0,0.6,(0,255,0),2); outs.append(t)
cv2.imwrite('g/planov.jpg',np.hstack(outs))
