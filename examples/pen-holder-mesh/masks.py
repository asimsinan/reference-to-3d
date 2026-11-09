"""Holder silhouette (see-through mesh included) + rim/base edge points for the camera solve.
usage: py scripts/masks.py  (reads photo.jpg) -> mask_photo.png (holder only, below the rim top), edges.json, masks_vis.jpg"""
import cv2, numpy as np, json
from scipy import ndimage as ndi
im=cv2.imread('photo.jpg'); H,W=im.shape[:2]
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
yy,xx=np.mgrid[0:H,0:W]
box=(xx>=565)&(xx<=1140)&(yy>=888)&(yy<=1625)
dark=(g<85)&box
s=ndi.binary_closing(dark,structure=np.ones((11,11)),iterations=1)
s=ndi.binary_fill_holes(s)
s=ndi.binary_opening(s,iterations=3)
s=ndi.binary_opening(s,structure=np.ones((221,1)))   # short dark background blobs beside the holder (the chair) out
lab,n=ndi.label(s); s=lab==(1+np.argmax(ndi.sum(s,lab,range(1,n+1))))
cv2.imwrite('mask_photo.png',(s*255).astype(np.uint8))
# --- rim outer top edge (back half), columns free of pens/scissors
top=[]
for u in list(range(578,688,4))+list(range(1000,1118,4)):
    ys=np.where(s[:,u])[0]
    if len(ys): top.append((u,ys[0]-0.5))
# --- ring front lower edge: the ring is uniformly black (low local std); the mesh below is textured
gf=g.astype(np.float32); mu=cv2.blur(gf,(9,9)); sd=np.sqrt(np.maximum(cv2.blur(gf*gf,(9,9))-mu*mu,0))
ring=(mu<75)&(sd<9)
ringbot=[]
for u in range(590,1110,5):
    col=ring[880:1045,u]
    runs=np.split(np.arange(len(col)),np.where(np.diff(col.astype(int))!=0)[0]+1)
    cand=[r for r in runs if col[r[0]] and len(r)>=18 and r[-1]<len(col)-3]   # the front ring: the last complete run
    if cand: ringbot.append((u,880+cand[-1][-1]+0.5))
# --- base lower front contour
base=[]
for u in range(620,1085,10):
    ys=np.where(s[:,u])[0]
    if len(ys) and ys[-1]>1540: base.append((u,ys[-1]+0.5))
for v in range(1560,1600,4):
    xs=np.where(s[v])[0]
    if len(xs): base+=[(xs[0]-0.5,v),(xs[-1]+0.5,v)]
json.dump(dict(top=top,ringbot=ringbot,base=base),open('edges.json','w'))
vis=im.copy()
cv2.drawContours(vis,cv2.findContours((s*255).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0],-1,(255,0,255),2)
for (u,v) in top: cv2.circle(vis,(int(u),int(v)),4,(0,255,0),-1)
for (u,v) in ringbot: cv2.circle(vis,(int(u),int(v)),4,(0,255,255),-1)
for (u,v) in base: cv2.circle(vis,(int(u),int(v)),4,(255,255,0),-1)
cv2.imwrite('masks_vis.jpg',vis[840:1640,540:1160])
print('top',len(top),'ringbot',len(ringbot),'base',len(base))
