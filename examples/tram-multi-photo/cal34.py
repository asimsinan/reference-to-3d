"""cal34.py TAG -- photo vs render (photos 9, 13) in boxes per material: mean RGB, and the whole-silhouette |diff|"""
import cv2, numpy as np, sys, json
tag=sys.argv[1]; import os; ONLY=os.environ.get('KS','9,13').split(',')
B={'13':{'red_dash':(330,600,360,640),'red_side':(530,580,560,620),'white_hood':(290,215,450,232),'fender':(300,690,500,720),'black_bumper':(250,745,550,770),'sign':(300,155,350,180)},
   '9':{'red_dash':(250,520,280,560),'red_face34':(460,520,500,560),'red_side':(700,450,740,470),'white_hood':(250,215,450,235),'white_band':(700,265,740,280),'fender':(250,640,450,670),'door':(600,450,640,550)}}
occ={'13':[[[0,440],[205,440],[205,800],[0,800]]],'9':[]}
tot=[]
for k,bx in B.items():
    if k not in ONLY: continue
    ph=cv2.imread(f'ref2/p{k}.png').astype(np.float32); r=cv2.imread(f'out/{tag}34_{k}.png',cv2.IMREAD_UNCHANGED).astype(np.float32)
    a=r[...,3:]/255.; comp=r[...,:3]*a+ph*(1-a); m=a[...,0]>0.99
    o=np.zeros(m.shape,np.uint8)
    for p in occ[k]: cv2.fillPoly(o,[np.array(p,np.int32)],1)
    m&=o==0; d=np.abs(comp-ph).mean(-1); tot.append(d[m].mean())
    print('photo',k,'|diff| %.1f median %.1f'%(d[m].mean(),np.median(d[m])))
    for n,(x0,y0,x1,y1) in bx.items():
        print('   %-12s photo %s render %s'%(n,np.round(ph[y0:y1,x0:x1].reshape(-1,3).mean(0)[::-1]),np.round(comp[y0:y1,x0:x1].reshape(-1,3).mean(0)[::-1])))
    H=420; s=H/ph.shape[0]; cv2.imwrite(f'g/cal{k}.jpg',np.concatenate([cv2.resize(ph,None,fx=s,fy=s),cv2.resize(comp,None,fx=s,fy=s)],1))
print('ALL %.1f'%np.mean(tot))
