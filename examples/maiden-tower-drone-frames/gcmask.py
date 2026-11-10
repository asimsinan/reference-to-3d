# photo silhouette per view by GrabCut seeded from the model's silhouette; writes mask/rN.png and g/gc<N>.jpg, prints IoU
import cv2,numpy as np,json,sys,os
os.makedirs('mask',exist_ok=True); IGN=json.load(open('ignore.json'))
def fillholes(m):
    m=m.astype(np.uint8); h,w=m.shape; ff=m.copy(); mk=np.zeros((h+2,w+2),np.uint8); cv2.floodFill(ff,mk,(0,0),1); return (m|(1-ff))>0
res={}
for i in map(int,sys.argv[1:] or range(1,7)):
    im=cv2.imread('ref/r%d.png'%i); idm=cv2.imread('id/r%d.png'%i,cv2.IMREAD_UNCHANGED)
    mod=fillholes((idm[...,3]>=128)&(idm[...,2]>0))
    big=cv2.dilate(mod.astype(np.uint8),np.ones((61,61),np.uint8))>0; small=cv2.erode(mod.astype(np.uint8),np.ones((25,25),np.uint8))>0
    gm=np.full(mod.shape,cv2.GC_BGD,np.uint8); gm[big]=cv2.GC_PR_BGD; gm[mod]=cv2.GC_PR_FGD; gm[small]=cv2.GC_FGD
    bg=np.zeros((1,65)); fg=np.zeros((1,65)); cv2.grabCut(im,gm,None,bg,fg,6,cv2.GC_INIT_WITH_MASK)
    ph=(gm==cv2.GC_FGD)|(gm==cv2.GC_PR_FGD); ph=cv2.morphologyEx(ph.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))>0
    n,lab,st,_=cv2.connectedComponentsWithStats(ph.astype(np.uint8)); keep=np.zeros_like(ph)
    for k in range(1,n):
        if st[k,4]>2000: keep|=lab==k
    ph=fillholes(keep)
    ok=np.ones(ph.shape,np.uint8)
    for poly in IGN.get('r%d'%i,[]): cv2.fillPoly(ok,[np.array(poly,np.int32)],0)
    ok=ok>0; iou=(ph&mod&ok).sum()/max(((ph|mod)&ok).sum(),1); res[i]=iou
    cv2.imwrite('mask/r%d.png'%i,ph.astype(np.uint8)*255)
    v=(im*0.45).astype(np.uint8); v[ph&mod]=(0,170,0); v[ph&~mod]=(0,0,255); v[~ph&mod]=(255,80,0); v[~ok]=(v[~ok]*0.3).astype(np.uint8)
    cv2.imwrite('g/gc%d.jpg'%i,cv2.resize(v,None,fx=0.5,fy=0.5)); print('r%d IoU %.3f'%(i,iou))
