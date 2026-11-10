# pcrop.py PREFIX view:part [view:part ...] -> g/pcrops.jpg ; crop = part's bbox in the id render (+margin), photo above render
import cv2,numpy as np,sys
names=open('id/names.txt').read().split(); pre=sys.argv[1]; cols=[]
for spec in sys.argv[2:]:
    v,part=spec.split(':'); idm=cv2.imread('id/%s.png'%v,cv2.IMREAD_UNCHANGED); idx=np.round(idm[...,2]/8.0).astype(int); idx[idm[...,3]<128]=0
    ys,xs=np.nonzero(idx==names.index(part)+1); x0,x1,y0,y1=xs.min()-15,xs.max()+15,ys.min()-15,ys.max()+15
    x0,y0=max(x0,0),max(y0,0); a=cv2.imread('ref/%s.png'%v)[y0:y1,x0:x1]; r=cv2.imread('out/%s_%s.png'%(pre,v))[y0:y1,x0:x1]
    s=min(320/(y1-y0),600/(x1-x0)); a=cv2.resize(a,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC); r=cv2.resize(r,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC)
    c=np.vstack([a,np.zeros((4,a.shape[1],3),np.uint8),r]); cv2.putText(c,spec,(4,16),0,0.5,(0,255,255),1); cols.append(c); cols.append(np.zeros((c.shape[0],6,3),np.uint8))
H=max(c.shape[0] for c in cols); cols=[np.vstack([c,np.zeros((H-c.shape[0],c.shape[1],3),np.uint8)]) for c in cols]
cv2.imwrite('g/pcrops.jpg',np.hstack(cols[:-1]))
