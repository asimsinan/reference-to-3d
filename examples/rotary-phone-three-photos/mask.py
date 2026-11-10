import cv2, numpy as np, sys
for n in ['front','side','rear']:
    im=cv2.imread(n+'.jpg');hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV).astype(int)
    h,s,v=hsv[...,0],hsv[...,1],hsv[...,2]
    red=((h<8)|(h>168))&(s>110)&(v>35)
    red=cv2.morphologyEx(red.astype(np.uint8),cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    nlab,lab,st,_=cv2.connectedComponentsWithStats(red)
    k=1+np.argmax(st[1:,4]);m=(lab==k).astype(np.uint8)
    gc=np.where(m>0,cv2.GC_PR_FGD,cv2.GC_PR_BGD).astype(np.uint8)
    gc[cv2.erode(m,np.ones((15,15),np.uint8))>0]=cv2.GC_FGD
    gc[cv2.dilate(m,np.ones((41,41),np.uint8))==0]=cv2.GC_BGD
    bg=np.zeros((1,65),np.float64);fg=bg.copy()
    cv2.grabCut(im,gc,None,bg,fg,4,cv2.GC_INIT_WITH_MASK)
    m2=((gc==1)|(gc==3)).astype(np.uint8)
    m2=cv2.morphologyEx(m2,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    cs,_=cv2.findContours(m2,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
    for c in cs:
        cv2.drawContours(m2,[c],-1,1,-1)
    cv2.imwrite('m_%s.png'%n,m2*255)
    ov=im.copy();cs,_=cv2.findContours(m2,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE);cv2.drawContours(ov,cs,-1,(0,255,0),2)
    cv2.imwrite('mo_%s.jpg'%n,cv2.resize(ov,(750,1000)))
