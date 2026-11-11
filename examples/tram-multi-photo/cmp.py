"""cmp.py -- photo vs render inside the model's silhouette (minus occluders): mean |diff| (0-255), per photo; sheets."""
import cv2, json, numpy as np, sys
import os
occ=json.load(open(os.environ.get('OCC','occ.json'))); REF=os.environ.get('REF','ref'); KS=os.environ.get('KS','1,2,3,4,5,6').split(','); tag=sys.argv[1] if len(sys.argv)>1 else 'match'
tot=[]
rows=[]
for k in KS:
    ph=cv2.imread(f'{REF}/p{k}.png').astype(np.float32); r=cv2.imread(f'out/{tag}{k}.png',cv2.IMREAD_UNCHANGED); r=r.astype(np.float32)/(257.0 if r.dtype==np.uint16 else 1.0)
    a=r[...,3]/255.0; m=a>0.99
    o=np.zeros(m.shape,np.uint8)
    for p in occ.get(k,[]): cv2.fillPoly(o,[np.array(p,np.int32)],1)
    m&=o==0
    comp=r[...,:3]*a[...,None]+ph*(1-a[...,None])
    d=np.abs(comp-ph).mean(-1)
    e=float(d[m].mean()); med=float(np.median(d[m])); tot.append(e)
    print(k,'mean %.1f  median %.1f'%(e,med))
    H=360; s=H/ph.shape[0]
    a1=cv2.resize(ph,None,fx=s,fy=s); a2=cv2.resize(comp,None,fx=s,fy=s); a3=cv2.resize(np.clip(d*3,0,255)[...,None].repeat(3,2),None,fx=s,fy=s)
    rows.append(np.concatenate([a1,a2,a3],1))
print('ALL %.1f'%np.mean(tot))
W=max(r.shape[1] for r in rows); sheet=np.concatenate([np.pad(r,((0,0),(0,W-r.shape[1]),(0,0))) for r in rows],0)
cv2.imwrite(f'g/sheet_{tag}.jpg',sheet)
