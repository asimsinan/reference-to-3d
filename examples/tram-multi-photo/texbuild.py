"""texbuild.py -- photos -> each part's UV texture through the solved cameras with a depth test.
Each texel takes the views that see it best ((f/z)^2 cos^2, ^POW blend); unseen texels from the 180-deg partner
(-x,-y,z) (a double-ended car), then the y-mirror, then inpainting. -> tex/<obj>.png, tex/<obj>_src.png"""
import os
os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2, json, numpy as np, sys
from camlib import cam
BK=os.environ.get('BK','bake'); REF=os.environ.get('REF','ref')
J=json.load(open(os.environ.get('CAMS','cams.json'))); info=json.load(open(f'{BK}/objs.json')); occ=json.load(open(os.environ.get('OCC','occ.json')))
CXR=float(os.environ.get('CXR','0'))
POW=float(os.environ.get('POW','12'))
PRIO={'6':3.0,'1':1.6,'4':1.2,'2':0.8,'3':0.5,'5':1.0}; ONLY=sys.argv[1:]
ks=sorted(J['cams'])
SOLO=os.environ.get('SOLO'); TEXD=os.environ.get('TEXD','tex')
if SOLO: ks=[SOLO]
GAINS=json.load(open('gains.json')) if os.path.exists('gains.json') and not SOLO and not os.environ.get('NOGAIN') else {}
PH={k:cv2.imread(f'{REF}/p{k}.png').astype(np.float32) for k in ks}
for k in ks:
    if k in GAINS: g=np.array(GAINS[k]); PH[k]=PH[k]*g[:,0]+g[:,1]

DEP={}
OCC={}
for k in ks:
    d=cv2.imread(f'{BK}/depth{k}.exr',cv2.IMREAD_UNCHANGED); a=d[...,3] if d.shape[2]==4 else np.ones(d.shape[:2])
    z=d[...,2].copy(); z[a<0.5]=1e9; DEP[k]=z
    m=np.zeros(PH[k].shape[:2],np.uint8)
    for poly in occ.get(k,[]): cv2.fillPoly(m,[np.array(poly,np.int32)],1)
    OCC[k]=cv2.dilate(m,np.ones((5,5),np.uint8))>0
CAMS={k:cam(k) for k in ks}
def views(P,N):
    """per camera: colour sample and weight for points P (n,3) with normals N"""
    cols=[];ws=[]
    for k in ks:
        R,C,f,W,H,cx,cy=CAMS[k]
        Xc=(P-C)@R.T; z=Xc[:,2]; zs=np.where(z>0.05,z,1e9)
        u=f*Xc[:,0]/zs+cx; v=f*Xc[:,1]/zs+cy
        ok=(z>0.05)&(u>=1)&(v>=1)&(u<W-2)&(v<H-2)
        ui=np.clip(np.round(u).astype(int),0,W-1); vi=np.clip(np.round(v).astype(int),0,H-1)
        # depth test with a 3x3 neighbourhood min/max tolerance for edges
        zd=DEP[k][vi,ui]
        ok&=np.abs(zd-z)<0.025+0.004*z
        ok&=~OCC[k][vi,ui]
        dv=C-P; dv/=np.linalg.norm(dv,axis=1,keepdims=True); cs=(N*dv).sum(1)
        ok&=cs>0.08
        w=np.where(ok,((f/np.maximum(z,0.1))**2*cs**2)*PRIO.get(k,1.0),0.0)
        uc=np.clip(u,0,W-1.001); vc=np.clip(v,0,H-1.001); x0=np.floor(uc).astype(int); y0=np.floor(vc).astype(int); fx=(uc-x0)[:,None]; fy=(vc-y0)[:,None]
        I=PH[k]; col=(I[y0,x0]*(1-fx)*(1-fy)+I[y0,x0+1]*fx*(1-fy)+I[y0+1,x0]*(1-fx)*fy+I[y0+1,x0+1]*fx*fy)
        cols.append(col); ws.append(w)
    return np.stack(cols),np.stack(ws)
def blend(cols,ws):
    wm=ws.max(0); wn=np.where(wm[None]>0,(ws/np.maximum(wm[None],1e-12))**POW,0)
    s=wn.sum(0); c=(cols*wn[...,None]).sum(0)/np.maximum(s,1e-9)[:,None]
    return c, wm>0, np.argmax(ws,0), wm
os.makedirs(TEXD,exist_ok=True)
stats={}
for name,inf in info.items():
    if ONLY and name not in ONLY: continue
    Pi=cv2.imread(f'{BK}/{name}_P.exr',cv2.IMREAD_UNCHANGED); Ni=cv2.imread(f'{BK}/{name}_N.exr',cv2.IMREAD_UNCHANGED)
    n=Pi.shape[0]; valid=(Pi[...,3]>0.5)&(np.abs(Pi[...,:3]).sum(-1)>1e-6)
    P=Pi[...,2::-1][valid].astype(np.float64); N=Ni[...,2::-1][valid].astype(np.float64)
    N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-9)
    out=np.zeros((valid.sum(),3)); src=np.zeros(valid.sum(),np.uint8)
    best=np.zeros(len(P))
    rearpart=any(len(tk)<=3 and tk[0]=='B' and (len(tk)==1 or tk[1] in 'LR0123') for tk in name.split('_')[1:])
    fills=((10,(-1,-1),0.55),(20,(1,-1),0.01))
    if os.environ.get('MIRROR') and not rearpart: fills=((10,(-1,-1),0.01),(20,(1,-1),0.55))
    for tag,(sx,sy),fac in ((0,(1,1),1.0),)+(() if SOLO else fills):
        Q=P*np.array([sx,sy,1.0]); Q[:,0]+=(2*CXR if sx<0 else 0.0)
        c,s_,am,wm=blend(*views(Q,N*np.array([sx,sy,1.0])))
        sc=wm*fac; take=s_&(sc>best)
        out[take]=c[take]; src[take]=tag+am[take]+1; best[take]=sc[take]
    img=np.zeros((n,n,3),np.float32); img[valid]=out
    srcimg=np.zeros((n,n),np.uint8); srcimg[valid]=src
    hole=(valid&(srcimg==0)).astype(np.uint8)
    frac=float(hole.sum())/max(1,valid.sum())
    if hole.any() and hole.sum()<valid.sum():
        img=cv2.inpaint(np.clip(img,0,255).astype(np.uint8),hole,5,cv2.INPAINT_TELEA).astype(np.float32)
    elif hole.all() or (hole.sum()==valid.sum()):
        img[valid]=(60,60,60)
    # pad islands outward so bilinear lookups at island edges stay on colour
    pad=cv2.inpaint(np.clip(img,0,255).astype(np.uint8),(~valid).astype(np.uint8),3,cv2.INPAINT_TELEA) if valid.any() else img
    cv2.imwrite(f'{TEXD}/{name}.png',np.clip(pad,0,255).astype(np.uint8)); cv2.imwrite(f'{TEXD}/{name}_src.png',srcimg*12)
    stats[name]={'direct':round(float(((src>0)&(src<10)).mean()),3),'partner':round(float(((src>10)&(src<20)).mean()),3),'mirror':round(float((src>20).mean()),3),'none':round(frac,3)}
json.dump(stats,open(f'{TEXD}/stats.json','w'),indent=0)
big=sorted(info,key=lambda k:-info[k]['area'])[:30]
for b in ([] if SOLO else big):
    if b in stats: print(b,round(info[b]['area'],2),stats[b])
