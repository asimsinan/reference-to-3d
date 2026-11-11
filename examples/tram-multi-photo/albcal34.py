"""albcal34.py -- per material group: median linear ratio photo/render over its pixels in photos 9 and 13 (geometric
mean of the two photos), damped ^0.7, applied to the level overrides in lev34.json. Prints the groups' numbers."""
import cv2, numpy as np, json, os
idm=json.load(open('out/idmap.json'))
def s2l(v): v=v/255.0; return np.where(v<=0.04045,v/12.92,((v+0.055)/1.055)**2.4)
def l2s(v): v=np.clip(v,0,1); return np.where(v<=0.0031308,12.92*v,1.055*v**(1/2.4)-0.055)*255
names=list(idm); cols=np.array([l2s(np.array(idm[n],float)/255)[::-1] for n in names])
GRP={'paint':'red','sign':'red','white':'white','frame':'maroon'}
L=json.load(open('lev34.json')) if os.path.exists('lev34.json') else {'red':0.42,'white':0.80,'maroon':0.10,'roof':0.14}
R={g:[] for g in set(GRP.values())}
for k in ('9','13'):
    ph=s2l(cv2.imread(f'ref2/p{k}.png').astype(np.float32)); r=cv2.imread(f'out/real34_{k}.png',cv2.IMREAD_UNCHANGED).astype(np.float32)
    idr=cv2.imread(f'out/id{k}.png',cv2.IMREAD_UNCHANGED).astype(np.float32); idr=idr/257 if idr.max()>255 else idr
    a=(idr[...,3]>250)&(r[...,3]>250)
    if k=='13': a[440:800,0:205]=False
    a=cv2.erode(a.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)          # away from edges
    px=idr[...,:3][a]; best=np.argmin(((px[:,None,:]-cols[None])**2).sum(-1),1); pre=np.array([names[i].split('_')[0] for i in best])
    rl=s2l(r[...,:3]); 
    for p,g in GRP.items():
        m=pre==p
        if m.sum()<200: continue
        yp=ph[a][m].max(-1); yr=rl[a][m].max(-1)
        rat=np.median(yp)/max(np.median(yr),1e-4); R[g].append(rat)
        print(k,'%-6s px %6d  photo %.3f render %.3f ratio %.2f'%(p,m.sum(),np.median(yp),np.median(yr),rat))
for g,v in R.items():
    if not v: continue
    gm=float(np.exp(np.mean(np.log(v)))); L[g]=float(np.clip(L[g]*gm**0.7,0.01,0.9)); print('level',g,'x%.2f ->'%gm**0.7,round(L[g],3))
json.dump(L,open('lev34.json','w'),indent=1)
print('LEV='+','.join('%s=%.3f'%(k,v) for k,v in L.items()))
