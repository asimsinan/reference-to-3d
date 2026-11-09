import cv2, numpy as np
im=cv2.imread('ref.jpg'); lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(int); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
m=((lab[...,2]<143)&(lab[...,1]<138)&(hsv[...,1]<75)&(hsv[...,1]>28)&(lab[...,0]>110)).astype(np.uint8)
m0=m.copy()
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)); m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
m=cv2.erode(m,np.ones((7,7),np.uint8))
n,lbl,st,cen=cv2.connectedComponentsWithStats(m)
out=np.zeros_like(m); keep={}
for nm,(x,y) in {'S1':(735,620),'S2':(820,520),'bench':(200,550)}.items():
    k=lbl[y,x]; comp=(lbl==k).astype(np.uint8)
    # fill holes
    comp=cv2.dilate(comp,np.ones((7,7),np.uint8))&cv2.morphologyEx(m0,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    cs,_=cv2.findContours(comp,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); comp=np.zeros_like(m); cv2.drawContours(comp,cs,-1,1,-1)
    keep[nm]=comp; print(nm,k,comp.sum(),cv2.boundingRect(comp))
    cv2.imwrite(f'mask_{nm}.png',comp*255)
vis=im.copy()
for nm,c in keep.items(): vis[c>0]=(vis[c>0]*0.4+np.array([255,0,255])*0.6).astype(np.uint8)
cv2.imwrite('fabmask_vis.jpg',vis)
