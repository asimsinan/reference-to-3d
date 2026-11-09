"""The mug's silhouette from a real photo (table and wall behind it, not a white backdrop): GrabCut seeded with a
box round the mug, bright low-saturation pixels as probable object and two sure-object polygons (this photo's numbers).
usage: uv run --with opencv-python-headless --with numpy --with scipy python masks.py      (reads photo.jpg)
writes mask_photo.png and masks_vis.jpg (look at it: the outline over the photo).
Two fixes it needed: a thin bright table edge joined the mask (opened away with a tall vertical kernel), and GrabCut
left the handle's shaded upper face (grey, seen from above) in the handle's hole: inside the hole, low saturation is
object, the beige table seen through it is not."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
"""mug silhouette by GrabCut (rect init + bright/low-sat seeds), handle = part right of body column."""
import cv2,numpy as np
im=cv2.imread('photo.jpg'); H,W=im.shape[:2]
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
mask=np.full((H,W),cv2.GC_BGD,np.uint8)
mask[870:1910,330:1230]=cv2.GC_PR_BGD
cand=(g>185)&(hsv[...,1]<30)
mask[(mask==cv2.GC_PR_BGD)&cand]=cv2.GC_PR_FGD
cv2.fillPoly(mask,[np.array([(420,1000),(920,1000),(800,1740),(520,1740)])],cv2.GC_FGD)
cv2.fillPoly(mask,[np.array([(1180,1250),(1190,1300),(1080,1440),(1060,1420)])],cv2.GC_FGD)
bgd=np.zeros((1,65)); fgd=np.zeros((1,65))
cv2.grabCut(im,mask,None,bgd,fgd,6,cv2.GC_INIT_WITH_MASK)
sil=((mask==1)|(mask==3)).astype(np.uint8)*255
sil=cv2.morphologyEx(sil,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
sil=cv2.morphologyEx(sil,cv2.MORPH_OPEN,np.ones((31,1),np.uint8))
n,l,st,_=cv2.connectedComponentsWithStats(sil); k=1+np.argmax(st[1:,4]); sil=((l==k)*255).astype(np.uint8)
cv2.imwrite('mask_photo.png',sil)
vis=im.copy(); cv2.drawContours(vis,cv2.findContours(sil,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)[0],-1,(255,0,255),3)
cv2.imwrite('masks_vis.jpg',cv2.resize(vis[850:1950,300:1300],None,fx=0.6,fy=0.6))
# the lower arm's upper face is grey (shaded), GrabCut left it in the hole: inside the handle's hole, low saturation -> object
from scipy import ndimage as ndi
s=sil>0; filled=ndi.binary_fill_holes(s); hole=filled&~s
add=hole&(hsv[...,1]<38)
add=ndi.binary_opening(add,iterations=2)
s|=add; s=ndi.binary_fill_holes(s)|s
# keep the true hole (beige) out again
s&=~(hole&~add)
lab,n=ndi.label(~s); sz=ndi.sum(np.ones_like(s),lab,range(1,n+1))
for i,z in enumerate(sz):
    if z<80: s[lab==i+1]=True
cv2.imwrite('mask_photo.png',(s*255).astype(np.uint8))
vis=im.copy(); cv2.drawContours(vis,cv2.findContours((s*255).astype(np.uint8),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)[0],-1,(255,0,255),2)
cv2.imwrite('masks_vis.jpg',cv2.resize(vis[1000:1550,850:1250],None,fx=1.2,fy=1.2))
print('added',add.sum())
