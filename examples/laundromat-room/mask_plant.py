import cv2, numpy as np
im=cv2.imread('ref.png'); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
b,gg,r=[im[...,i].astype(int) for i in range(3)]
m=np.zeros(g.shape,np.uint8)
roi=np.zeros(g.shape,bool); roi[503:600,738:842]=True
# wall here is ~70-80; leaves are darker and greener
bg=cv2.GaussianBlur(g,(0,0),15)
leaf=roi&(g<bg-14)
pot=np.zeros(g.shape,bool); pot[565:600,765:806]=True; pot&=(r>b+10)
roi2=np.zeros(g.shape,bool); roi2[585:627,800:842]=True; leaf|=roi2&(g<bg-14)   # hanging leaves right of the cabinet
m[(leaf|pot)]=255
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(m)
for i in range(1,n):
    if st[i,4]<12: m[lab==i]=0
cv2.imwrite('alpha_plant.png',cv2.GaussianBlur(m,(3,3),0))
x0,y0,x1,y1=735,500,845,630; a=im[y0:y1,x0:x1].copy(); a[m[y0:y1,x0:x1]>127]=(0,0,255)
cv2.imwrite('chk_plant.png',cv2.resize(np.hstack([im[y0:y1,x0:x1],a]),None,fx=4,fy=4,interpolation=cv2.INTER_NEAREST))
