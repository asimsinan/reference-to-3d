"""The photo's silhouette (flood fill of the white background) and the dark handles' masks.
usage: uv run --with opencv-python-headless --with numpy python masks.py      (reads photo.jpg)
writes mask_photo.png, mask_<part>.png and masks_vis.png (each mask coloured over the photo, 2x: look at it).

The boxes below are this photo's: each part's region, so the pot's own dark reflections (its edges are dark strips)
do not join a handle. Draw a grid over the photo first (../laptop-single-photo/grid.py) and set your own.
Check masks_vis.png for a part cut short by a box edge: a tab's bottom 7 px left out of its mask stayed in the body
texture as a dark smear on the lid."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
im=cv2.imread('photo.jpg'); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(int)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
bg=((g>232)&(hsv[...,1]<25)).astype(np.uint8)
n,lab=cv2.connectedComponents(bg)
sil=(lab!=lab[0,0]).astype(np.uint8)*255
sil=cv2.morphologyEx(sil,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
cv2.imwrite('mask_photo.png',sil)
dark=((g<120)&(hsv[...,1]<80)).astype(np.uint8)
H,W=g.shape; yy,xx=np.mgrid[0:H,0:W]
PARTS={   # part: region where its dark pixels are (this photo)
  'right': ((xx>=310)&(yy<183)&(yy>140))|((xx>=368)&(yy>=183)&(yy<270)),   # main handle (lid half + pot half)
  'left':  (xx<=101)&(yy>=186)&(yy<270),                                   # helper handle on the pot
  'tab':   (xx>=90)&(xx<=185)&(yy>140)&(yy<186),                           # the lid's short tab
}
out={}
for nm,reg in PARTS.items():
    m=cv2.morphologyEx((dark*reg).astype(np.uint8)*255,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    n,l,st,_=cv2.connectedComponentsWithStats(m); keep=np.zeros_like(m)
    for i in range(1,n):
        if st[i,4]>30: keep[l==i]=255
    cv2.imwrite(f'mask_{nm}.png',keep); out[nm]=keep
vis=im.copy()
for nm,c in zip(out,[(0,0,255),(0,255,0),(255,0,0)]): vis[out[nm]>0]=c
cv2.drawContours(vis,cv2.findContours(sil,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0],-1,(255,0,255),1)
cv2.imwrite('masks_vis.png',cv2.resize(vis,None,fx=2,fy=2,interpolation=cv2.INTER_NEAREST))
