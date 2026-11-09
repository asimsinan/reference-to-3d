import cv2, numpy as np
im=cv2.imread('ref.jpg'); lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(int); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
fab=((lab[...,2]<143)&(lab[...,1]<138)&(hsv[...,1]<75)&(hsv[...,1]>28)&(lab[...,0]>110))
woodish=(lab[...,2]>148)
boxes={'S1':(598,548,880,700),'S2':(700,480,930,605),'bench':(70,455,405,585)}
seeds={'S1':[(735,620),(700,600),(780,640),(650,640)],'S2':[(820,520),(780,540),(870,530)],'bench':[(200,550),(150,540),(300,500),(250,520)]}
vis=im.copy(); masks={}
for nm,(x0,y0,x1,y1) in boxes.items():
    M=np.full(im.shape[:2],cv2.GC_BGD,np.uint8); M[y0:y1,x0:x1]=cv2.GC_PR_BGD
    sub=np.zeros_like(M,bool); sub[y0:y1,x0:x1]=True
    M[sub&fab]=cv2.GC_PR_FGD; M[sub&woodish]=cv2.GC_BGD
    for (x,y) in seeds[nm]: M[y-6:y+7,x-6:x+7]=cv2.GC_FGD
    if nm=='bench': M[sub&(hsv[...,1]<20)]=cv2.GC_BGD     # curtain
    bg=np.zeros((1,65),np.float64); fg=np.zeros((1,65),np.float64)
    cv2.grabCut(im,M,None,bg,fg,6,cv2.GC_INIT_WITH_MASK)
    m=((M==cv2.GC_FGD)|(M==cv2.GC_PR_FGD)).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    n,l,st,_=cv2.connectedComponentsWithStats(m); k=l[seeds[nm][0][1],seeds[nm][0][0]]; m=(l==k).astype(np.uint8)
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); m=np.zeros_like(m); cv2.drawContours(m,cs,-1,1,-1)
    masks[nm]=m; cv2.imwrite(f'mask_{nm}.png',m*255); print(nm,m.sum(),cv2.boundingRect(m))
    cv2.drawContours(vis,cs,-1,(255,0,255),1)
cv2.imwrite('grab_vis.png',cv2.resize(vis,(2000,2000),interpolation=cv2.INTER_NEAREST)[900:1450,100:1900])
