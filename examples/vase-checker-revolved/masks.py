"""Vase silhouette by GrabCut on a cluttered background (this photo: 600x900). writes mask_raw.png, masks_vis.jpg"""
import cv2,numpy as np
from scipy import ndimage as ndi
im=cv2.imread('../photo.jpg'); H,W=im.shape[:2]
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=np.full((H,W),cv2.GC_BGD,np.uint8)
m[185:830,115:475]=cv2.GC_PR_BGD
# sure object: polygon well inside the outline
poly=np.array([(200,215),(390,215),(360,300),(345,330),(360,380),(440,450),(445,520),(420,620),(360,710),(355,760),(370,790),(300,810),(225,790),(240,760),(235,710),(170,620),(145,520),(150,450),(230,380),(245,330),(230,300)])
cv2.fillPoly(m,[poly],cv2.GC_FGD)
bgd=np.zeros((1,65));fgd=np.zeros((1,65))
cv2.grabCut(im,m,None,bgd,fgd,8,cv2.GC_INIT_WITH_MASK)
s=((m==1)|(m==3))
s=ndi.binary_opening(s,iterations=2); lab,n=ndi.label(s); s=lab==(1+np.argmax(ndi.sum(s,lab,range(1,n+1))))
s=ndi.binary_fill_holes(s)
cv2.imwrite('mask_raw.png',s.astype(np.uint8)*255)
vis=im.copy(); cv2.drawContours(vis,cv2.findContours(s.astype(np.uint8)*255,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0],-1,(255,0,255),1)
cv2.polylines(vis,[poly],True,(0,255,0),1)
cv2.imwrite('masks_vis.png',cv2.resize(vis[170:860,90:500],None,fx=1.3,fy=1.3))
