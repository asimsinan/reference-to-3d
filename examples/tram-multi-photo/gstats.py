"""gstats.py TAG -- mean |photo-render| per part group per photo, via the ID renders"""
import cv2, json, numpy as np, sys, re
tag=sys.argv[1]; idm=json.load(open('out/idmap.json')); occ=json.load(open('occ.json'))
def group(n):
    for g,pat in [('glass','^glass|^door_'),('paint_lo','^side_lower|^dash'),('upper','^side_upper|^cab_'),('roof','^roof$|^monitor|^roofboard'),('fender','^fender|^bumper'),
                  ('under','^solebar|^underbody|^wheel|^flange|^axle|^spring|^motor|^brake|^step'),('ends','^head|^bolt|^sig|^sign|^toplamp|^mirror|^coupler|^chain'),('bow','^bow|^volt'),('inside','^bulkhead|^floor|^bench|^ceiling|^controller|^pole|^gate')]:
        if re.search(pat,n): return g
    return 'other'
def srgb(v):
    v=v/255.0; return np.where(v<=0.0031308,12.92*v,1.055*v**(1/2.4)-0.055)*255
names=list(idm); cols=np.array([srgb(np.array(idm[n],float))[::-1] for n in names])  # BGR, display-encoded
gn=[group(n) for n in names]
G=sorted(set(gn)); print('photo '+' '.join('%8s'%g for g in G))
for k in ['1','2','3','4','5','6']:
    ph=cv2.imread(f'ref/p{k}.png').astype(np.float32); r=cv2.imread(f'out/{tag}{k}.png',cv2.IMREAD_UNCHANGED).astype(np.float32); r=r/257 if r.max()>255 else r
    idr=cv2.imread(f'out/id{k}.png',cv2.IMREAD_UNCHANGED).astype(np.float32); idr=idr/257 if idr.max()>255 else idr
    a=(idr[...,3]>250)&(r[...,3]>250)
    px=idr[...,:3][a]; best=np.zeros(len(px),int); bd=np.full(len(px),1e9)
    for i,cc in enumerate(cols):
        dd=((px-cc)**2).sum(1); m=dd<bd; bd[m]=dd[m]; best[m]=i
    gm=np.full(a.shape,'?',dtype=object); gm[a]=np.array(gn,dtype=object)[best]
    o=np.zeros(a.shape,np.uint8)
    for p in occ.get(k,[]): cv2.fillPoly(o,[np.array(p,np.int32)],1)
    a&=o==0; d=np.abs(r[...,:3]-ph).mean(-1)
    print(k,'    '+' '.join('%8s'%('%.1f/%d%%'%(d[a&(gm==g)].mean(),100*(a&(gm==g)).sum()/a.sum()) if (a&(gm==g)).any() else '-') for g in G))
