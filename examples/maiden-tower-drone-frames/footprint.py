# footprint.py Z : visual hull of the six masks on the plane z=Z -> g/fp.png and the simplified outline
import cv2,numpy as np,json,sys
from camlib import load
cams=load('cams.json'); IGN=json.load(open('ignore.json')); Z=float(sys.argv[1]); ppm=10
xs=np.arange(-40,40,1/ppm); X,Y=np.meshgrid(xs,xs)   # rows: y, cols: x
acc=np.ones(X.shape,bool)
for i in range(1,7):
    c=cams['r%d'%i]; m=cv2.imread('mask/r%d.png'%i,0)>127
    for poly in IGN.get('r%d'%i,[]): cv2.fillPoly(m.view(np.uint8),[np.array(poly,np.int32)],1)
    P=np.stack([X,Y,np.full_like(X,Z)],-1); C=np.einsum('ij,hwj->hwi',c.R,P-c.pos)
    u=c.f*C[...,0]/C[...,2]+c.cx; v=c.f*C[...,1]/C[...,2]+c.cy
    inside=(u>=0)&(u<c.W-1)&(v>=0)&(v<c.H-1); ui=np.clip(u.astype(int),0,c.W-1); vi=np.clip(v.astype(int),0,c.H-1)
    acc&=np.where(inside,m[vi,ui],True)
acc=cv2.morphologyEx(acc.astype(np.uint8),cv2.MORPH_OPEN,np.ones((9,9),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(acc); k=1+np.argmax(st[1:,4]); acc=(lab==k).astype(np.uint8)
cs,_=cv2.findContours(acc,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); ap=cv2.approxPolyDP(cs[0],5,True)[:,0]
poly=[(round(float(xs[x]),1),round(float(xs[y]),1)) for x,y in ap]
p=json.load(open('params.json'))
vis=cv2.cvtColor(acc*120,cv2.COLOR_GRAY2BGR)
def draw(pts,col):
    q=np.array([[(x+40)*ppm,(y+40)*ppm] for x,y in pts],np.int32); cv2.polylines(vis,[q],True,col,2)
draw(p['rocks_out'],(0,0,255)); draw(p['rocks_in'],(0,255,255)); draw(p['quay'],(255,0,0)); draw(p['terrace'],(0,255,0)); draw(poly,(255,0,255))
cv2.imwrite('g/fp.png',cv2.flip(vis,0)); print(json.dumps(poly)) if len(sys.argv)<3 else None
ys_=Y[acc>0]; xs_=X[acc>0]
band=lambda a,lo,hi: a[(a>=lo)&(a<=hi)]
print('z %.1f xmax(y-5..5) %.2f  ymin(x-5..5) %.2f  ymax(x5..10) %.2f  xmin(y-5..5) %.2f'%(Z,band(xs_[(ys_>-5)&(ys_<5)],-99,99).max(),ys_[(xs_>-5)&(xs_<5)].min(),ys_[(xs_>5)&(xs_<10)].max(),xs_[(ys_>-5)&(ys_<5)].min()))
