"""intcal.py -- interior materials vs photo 8 through camera 8's ID render: median linear ratio per group, damped,
cumulative. Textured groups (floor, wainscot) get new *_cal.png from the base texture; flat ones go to lev34.json."""
import cv2, numpy as np, json, os
idm=json.load(open('out/idmap.json'))
def s2l(v): v=v/255.0; return np.where(v<=0.04045,v/12.92,((v+0.055)/1.055)**2.4)
def l2s(v): v=np.clip(v,0,1); return np.where(v<=0.0031308,12.92*v,1.055*v**(1/2.4)-0.055)*255
names=list(idm); cols=np.array([l2s(np.array(idm[n],float)/255)[::-1] for n in names])
G={'wood_floor':'floor','woodlam_':'wains','leather_back':'leather','leather_cushion':'cushion'}   # thin parts (posts, ribs) and the leather (window reflections) set by hand from point samples
ph=s2l(cv2.imread('ref2/p8.png').astype(np.float32)); r=cv2.imread('out/real34_8.png',cv2.IMREAD_UNCHANGED).astype(np.float32)
idr=cv2.imread('out/id8.png',cv2.IMREAD_UNCHANGED).astype(np.float32); idr=idr/257 if idr.max()>255 else idr
a=(idr[...,3]>250)&(r[...,3]>250); a=cv2.erode(a.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
px=idr[...,:3][a]; best=np.argmin(((px[:,None,:]-cols[None])**2).sum(-1),1); nm=np.array(names)[best]
rl=s2l(r[...,:3])
gains=json.load(open('gains_int.json')) if os.path.exists('gains_int.json') else {'floor':[1.25]*3,'wains':[2.6]*3}
L=json.load(open('lev34.json'))
for pre,g in G.items():
    m=np.char.startswith(nm.astype(str),pre)
    if m.sum()<300: continue
    yp=np.median(ph[a][m],0); yr=np.median(rl[a][m],0); rat=yp/np.maximum(yr,1e-4)
    print('%-16s px %6d photo %s render %s ratio %s'%(pre,m.sum(),np.round(l2s(yp)),np.round(l2s(yr)),np.round(rat,2)))
    d=np.clip(rat,0.4,2.5)**0.7
    if g in ('floor','wains'): gains[g]=list(np.array(gains[g])*d[::-1])
    else: L[g]=float(L.get(g,1.0)*np.exp(np.mean(np.log(d))))
json.dump(gains,open('gains_int.json','w')); json.dump(L,open('lev34.json','w'),indent=1)
for g,src in (('floor','tex34m/floor.png'),('wains','tex34m/wainscot.png')):
    i=s2l(cv2.imread(src)[..., ::-1].astype(np.float32))*np.array(gains[g])[None,None,:]   # RGB gains
    cv2.imwrite(src.replace('.png','_cal.png'),l2s(i)[..., ::-1].astype(np.uint8))
print('gains',{k:np.round(v,2).tolist() for k,v in gains.items()},'lev',{k:round(v,3) for k,v in L.items()})
