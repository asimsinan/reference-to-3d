# stats.py PREFIX : per frame and part group, photo vs render: mean colour diff, p5/p95 lightness, saturation; sheet out/cmp_PREFIX.jpg
import cv2,numpy as np,json,sys
pre=sys.argv[1]; FR=sys.argv[2:] or ['r2','r3','r4']; names=open('id/names.txt').read().split()
GROUP={'shaft':['shaft'],'cornice':['cornice'],'arcade':['arcade'],'balcony':['balcony','railing','posts'],'upper':['upper'],'roof':['roof','dormers'],'finial':['finial']}
IGN=json.load(open('ignore.json')); tot=[]; tiles=[]
for k in FR:
    a=cv2.imread('ref/%s.png'%k).astype(np.float32); b=cv2.imread('out/%s_%s.png'%(pre,k)).astype(np.float32); idm=cv2.imread('id/%s.png'%k,cv2.IMREAD_UNCHANGED)
    idx=np.round(idm[...,2]/8.0).astype(int); idx[idm[...,3]<128]=0
    ok=np.ones(idx.shape,np.uint8)
    for poly in IGN.get(k,[]): cv2.fillPoly(ok,[np.array(poly,np.int32)],0)
    ok=ok>0; line='%s |'%k
    for gname,parts in GROUP.items():
        sel=np.isin(idx,[names.index(p)+1 for p in parts if p in names])&ok
        sel=cv2.erode(sel.astype(np.uint8),np.ones((3,3),np.uint8))>0
        if sel.sum()<100: continue
        pa,pb=a[sel],b[sel]; la,lb=pa.mean(1),pb.mean(1)
        sa=(pa.max(1)-pa.min(1)).mean(); sb=(pb.max(1)-pb.min(1)).mean()
        d=np.abs(pa.mean(0)-pb.mean(0)).mean(); pd=np.abs(pa-pb).mean(); tot.append((d,pd,sel.sum()))
        line+=' %s d%.0f pix%.0f L[%d-%d|%d-%d] S%.0f/%.0f'%(gname,d,pd,*np.percentile(la,[5,95]),*np.percentile(lb,[5,95]),sa,sb)
    print(line)
    m=idx>0; comp=a.copy(); comp[m]=b[m]
    diff=np.abs(a-comp).mean(2); diff=cv2.applyColorMap(np.clip(diff*3,0,255).astype(np.uint8),cv2.COLORMAP_INFERNO)
    t=np.hstack([a,comp,diff.astype(np.float32)]); H=1000; t=cv2.resize(t,(int(t.shape[1]*H/t.shape[0]),H)); tiles.append(t)
print('weighted mean colour diff %.1f/255, mean per-pixel diff %.1f/255'%(sum(d*n for d,_,n in tot)/sum(n for *_,n in tot),sum(p*n for _,p,n in tot)/sum(n for *_,n in tot)))
cv2.imwrite('out/cmp_%s.jpg'%pre,np.hstack(tiles).astype(np.uint8))
