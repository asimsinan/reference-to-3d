# Rectify a plane of the room from the photo: texel -> world point -> photo pixel.
from geo import *
import cv2
R=json.load(open('room.json')); cam=np.array([0,0,R['h']])
def rectify(img,origin,uvec,vvec,usize,vsize,ppm):
    """origin: world point of texel (0, bottom); u along uvec for usize m, v along vvec for vsize m (v up in image)."""
    w,h=int(round(usize*ppm)),int(round(vsize*ppm))
    us=(np.arange(w)+0.5)/ppm; vs=(np.arange(h)[::-1]+0.5)/ppm
    U,V=np.meshgrid(us,vs)
    P=np.asarray(origin)[None,None,:]+U[...,None]*np.asarray(uvec)+V[...,None]*np.asarray(vvec)
    C=(P-cam)@M          # cv-cam coords: c = M w  ->  rows: P @ M.T ... careful
    C=(P-cam)@M.T.T if False else np.einsum('ij,hwj->hwi',M,P-cam)
    x=f*C[...,0]/C[...,2]+960; y=f*C[...,1]/C[...,2]+540
    ok=(C[...,2]>0.05)&(x>=0)&(x<1919)&(y>=0)&(y<1079)
    out=cv2.remap(img,x.astype(np.float32),y.astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=(255,0,255))
    out[~ok]=(255,0,255); return out,ok
if __name__=='__main__':
    ref=cv2.imread('ref.png'); plate=cv2.imread('plate.png'); Xl,Hc,Yb=R['Xl'],R['Hc'],R['Yb']
    os.makedirs('rect',exist_ok=True) if False else None
    import os; os.makedirs('rect',exist_ok=True)
    o,_=rectify(ref,(Xl,0,0),(0,1,0),(0,0,1),Yb,Hc,150); cv2.imwrite('rect/left_wall.png',o)
    o,_=rectify(ref,(Xl,0,0),(1,0,0),(0,1,0),2.45-Xl,Yb,150); cv2.imwrite('rect/floor.png',o)
    o,_=rectify(ref,(2.45,0,0),(0,1,0),(0,0,1),Yb,Hc,150); cv2.imwrite('rect/right_wall.png',o)
    o,_=rectify(ref,(1.60,0,0),(0,1,0),(0,0,1),4.0,1.36,250); cv2.imwrite('rect/washers.png',o)
    o,_=rectify(ref,(Xl,0,Hc),(1,0,0),(0,1,0),2.45-Xl,Yb,120); cv2.imwrite('rect/ceiling.png',o)
