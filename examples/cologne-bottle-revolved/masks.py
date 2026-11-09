"""Bottle silhouette by GrabCut (real background: grey wall, white door, beige table). writes mask_photo.png, masks_vis.jpg"""
import cv2,numpy as np
from scipy import ndimage as ndi
im=cv2.imread('photo.jpg'); H,W=im.shape[:2]
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
mask=np.full((H,W),cv2.GC_BGD,np.uint8)
mask[430:1600,560:1020]=cv2.GC_PR_BGD
# sure object: well inside each part
cv2.fillPoly(mask,[np.array([(745,480),(885,480),(890,690),(740,690)])],cv2.GC_FGD)        # cap
cv2.fillPoly(mask,[np.array([(705,715),(880,715),(895,855),(700,855)])],cv2.GC_FGD)        # collar
cv2.fillPoly(mask,[np.array([(650,1020),(930,1020),(940,1520),(655,1520)])],cv2.GC_FGD)    # label
# probable object: the clear part of the body between shoulder and label, and the base
cv2.fillPoly(mask,[np.array([(640,890),(935,890),(935,1010),(640,1010)])],cv2.GC_PR_FGD)
bgd=np.zeros((1,65)); fgd=np.zeros((1,65))
cv2.grabCut(im,mask,None,bgd,fgd,8,cv2.GC_INIT_WITH_MASK)
s=((mask==1)|(mask==3))
s=ndi.binary_opening(s,iterations=2); lab,n=ndi.label(s); s=lab==(1+np.argmax(ndi.sum(s,lab,range(1,n+1))))
s=ndi.binary_fill_holes(s)
cv2.imwrite('mask_photo.png',(s*255).astype(np.uint8))
vis=im.copy(); cv2.drawContours(vis,cv2.findContours((s*255).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0],-1,(255,0,255),2)
cv2.imwrite('masks_vis.jpg',vis[420:1600,540:1040])
# per-row edges of the mask
for v in range(470,1580,30):
    xs=np.where(s[v])[0]
    if len(xs): print(v,xs[0],xs[-1],xs[-1]-xs[0])
