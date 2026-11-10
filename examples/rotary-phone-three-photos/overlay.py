"""draw the model's silhouette (per part) over each photo; report mask IoU.  usage: overlay.py [out_prefix]"""
import cv2,numpy as np,sys,json
import geom,camlib
def sil(v,pts,F):
    m=np.zeros((2000,1500),np.uint8);q=np.round(camlib.proj(v,pts)*8).astype(np.int32)
    for f in F: cv2.fillConvexPoly(m,q[list(f)],1,shift=3) if len(f)<=4 else cv2.fillPoly(m,[q[list(f)]],1,shift=3)
    return m
if __name__=='__main__':
    p=geom.load();P=geom.parts(p);col=dict(body=(0,255,0),handset=(255,255,0),ring=(255,0,255),wheel=(255,128,0))
    outs=[]
    for v in ['front','side','rear']:
        im=cv2.imread(v+'.jpg');tot=np.zeros((2000,1500),np.uint8)
        for k,(V,F) in P.items():
            m=sil(v,V,F);tot|=m
            cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);cv2.drawContours(im,cs,-1,col.get(k,(0,200,255)),2)
        ph=cv2.imread('m_%s.png'%v,0)>0
        print(v,'IoU(with cord in photo mask)',round((ph&(tot>0)).sum()/(ph|(tot>0)).sum(),3))
        ys,xs=np.where(tot|ph);y0,y1=max(ys.min()-40,0),min(ys.max()+40,2000)
        outs.append(cv2.resize(im[600:1750],(0,0),fx=0.6,fy=0.6))
        if len(sys.argv)>2 and sys.argv[2]==v: cv2.imwrite(sys.argv[1]+'_'+v+'.jpg',im[max(y0,0):y1,150:1400])
    cv2.imwrite((sys.argv[1] if len(sys.argv)>1 else 'ov')+'.jpg',np.hstack(outs))
