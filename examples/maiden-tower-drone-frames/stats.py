# stats.py PREFIX : per view and per part, photo vs render: mean colour, p5/p95 lightness, saturation; island IoU
import cv2,numpy as np,json,sys
pre=sys.argv[1]; names=open('id/names.txt').read().split(); IGN=json.load(open('ignore.json'))
GROUP={'tower':['shaft','corbel','balcony','room','cornice','ubalcony','pole'],'dome':['dome'],'fort':['fort','merlons','court'],'annex':['annex','porch'],'roof':['annex_roof'],
       'terrace':['terrace','parapet'],'quay':['quay'],'rocks':['rocks','boulders'],'beacon':['beacon','beacon_cage']}
tot=[]
for i in range(1,7):
    a=cv2.imread('ref/r%d.png'%i).astype(np.float32); b=cv2.imread('out/%s_r%d.png'%(pre,i)).astype(np.float32); idm=cv2.imread('id/r%d.png'%i,cv2.IMREAD_UNCHANGED)
    idx=np.round(idm[...,2]/8.0).astype(int); idx[idm[...,3]<128]=0
    ok=np.ones(idx.shape,np.uint8)
    for poly in IGN.get('r%d'%i,[]): cv2.fillPoly(ok,[np.array(poly,np.int32)],0)
    ok=ok>0
    # island silhouette: photo non-sea vs model, in the model's bounding box + margin
    ys,xs=np.nonzero(idx>0); x0,x1,y0,y1=max(xs.min()-40,0),xs.max()+40,max(ys.min()-40,0),ys.max()+40
    B,G,R=a[...,0],a[...,1],a[...,2]; sea=(B>R+14)&(B>=G-4)&(R<170)
    ph=~sea; ph=cv2.morphologyEx(ph.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))>0
    box=np.zeros_like(ok); box[y0:y1,x0:x1]=True; m=box&ok
    mod=idx>0; iou=(ph&mod&m).sum()/max(((ph|mod)&m).sum(),1)
    line='r%d IoU %.3f |'%(i,iou)
    for g,parts in GROUP.items():
        sel=np.isin(idx,[names.index(p)+1 for p in parts if p in names])&ok
        sel=cv2.erode(sel.astype(np.uint8),np.ones((3,3),np.uint8))>0
        if sel.sum()<150: continue
        pa,pb=a[sel],b[sel]; la,lb=pa.mean(1),pb.mean(1)
        d=np.abs(pa.mean(0)-pb.mean(0)).mean(); tot.append((d,sel.sum()))
        line+=' %s d%.0f [%d-%d|%d-%d]'%(g,d,*np.percentile(la,[5,95]),*np.percentile(lb,[5,95]))
    print(line)
print('weighted mean colour difference %.1f/255'%(sum(d*n for d,n in tot)/sum(n for d,n in tot)))
