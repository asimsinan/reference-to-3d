"""post.py SRC OUT -- finish a texture set: the right (-Y) side's tone matched to the left side's at low frequency
(photo 5 alone sees it, darker and softer), then unseen texels synthesised from each part's own seen pixels (fill.py)."""
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2, json, numpy as np, sys, re
from scipy.spatial import cKDTree
from fill import fill, exemplar
SRC,OUT=sys.argv[1],sys.argv[2]; os.makedirs(OUT,exist_ok=True)
info=json.load(open('bake/objs.json'))
def P_of(n):
    Pi=cv2.imread(f'bake/{n}_P.exr',cv2.IMREAD_UNCHANGED); v=(Pi[...,3]>0.5)&(np.abs(Pi[...,:3]).sum(-1)>1e-6); return Pi[...,2::-1],v
TEX={}; SEEN={}; PP={}; VV={}
for n in info:
    TEX[n]=cv2.imread(f'{SRC}/{n}.png').astype(np.float32); s=cv2.imread(f'{SRC}/{n}_src.png',0); PP[n],VV[n]=P_of(n)
    SEEN[n]=(s>0)&VV[n]
def nblur(img,m,sig):
    m=m.astype(np.float32); a=cv2.GaussianBlur(img*m[...,None],(0,0),sig); b=cv2.GaussianBlur(m,(0,0),sig); return a/np.maximum(b,1e-4)[...,None], b
# 1) right side tone from the left side (mirror y)
for base in ['side_lower','side_upper','glass_side','solebar']:
    L,R=base+'_L',base+'_R'
    if L not in TEX: continue
    mL=SEEN[L]; tree=cKDTree(PP[L][mL]); colL=TEX[L][mL]
    mR=SEEN[R]; Q=PP[R][mR]*np.array([1,-1,1]); d,i=tree.query(Q,distance_upper_bound=0.03)
    ok=np.isfinite(d); ref=np.zeros_like(TEX[R]); okm=np.zeros(mR.shape,bool)
    idx=np.flatnonzero(mR.ravel())[ok]; ref.reshape(-1,3)[idx]=colL[i[ok]]; okm.ravel()[idx]=True
    sig=max(6,TEX[R].shape[0]/60)
    bref,_=nblur(ref,okm,sig); bown,_=nblur(TEX[R],okm,sig)
    g=np.clip(bref/np.maximum(bown,4),0.5,2.2); g,_=nblur(g,okm,sig)
    gm=np.where(okm[...,None],g,1.0); full,_=nblur(gm,mR,sig*2)
    TEX[R][mR]=np.clip(TEX[R][mR]*full[mR],0,255)
    print('tone',R,'mean gain',np.round(full[mR].mean(0),2))
# 2) unseen texels from the part's own pixels; zones; class sources for parts nobody saw
CLASS={'monitor':'roofboard','roofboard':'roofboard','bench':'wood','ceiling':('roof','band'),'controller':'wood',
       'underbody':('solebar_L',None),'motor':('solebar_L',None),'axle':('solebar_L',None),'floor':'floorwood','door_':'wood'}
FORCE={('roof','top'),('monitor',None),('roofboard',None),('floor',None),('bench',None),('controller',None),('ceiling',None)}
def zones(n):
    P=PP[n]
    if n=='roof': return {'band':VV[n]&(P[...,2]<3.0),'top':VV[n]&(P[...,2]>=3.0)}
    return {None:VV[n]}
EX={}
G=json.load(open('gains.json'))
def lin(c): c=c/255.0; return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def enc(l): l=np.clip(l,0,1); return np.where(l<=0.0031308,12.92*l,1.055*l**(1/2.4)-0.055)*255
ALB=os.environ.get('ALBSCALE')   # albedo set: scale photo crops into albedo by the co-seen ratio
def crop(k,y0,y1,x0,x1,scale=1.0,up=3):
    c=cv2.imread(f'ref/p{k}.png').astype(np.float32)[y0:y1,x0:x1]; g=np.array(G[k]); c=c*g[:,0]+g[:,1]
    c=enc(lin(np.clip(c,0,255))*scale*(float(ALB) if ALB else 1.0))
    return cv2.resize(c.astype(np.float32),None,fx=up,fy=up,interpolation=cv2.INTER_CUBIC)
EXT={('roof','top'):crop('6',100,125,530,610,up=1.4),'roofboard':crop('6',160,190,520,600),'wood':crop('6',250,450,267,279,up=4),'floorwood':crop('6',250,450,267,279,scale=0.35,up=4)}
for n in info:
    for zn,zm in zones(n).items():
        e=exemplar(TEX[n],SEEN[n]&zm)
        if e is not None: EX[(n,zn)]=e
for n in info:
    img=TEX[n]
    for zn,zm in zones(n).items():
        seen=SEEN[n]&zm; valid=VV[n]&zm
        if not (valid&~seen).any(): continue
        ex=None; frac=seen.sum()/max(1,valid.sum())
        key=next((k for k in CLASS if n.startswith(k)),None)
        src=CLASS.get(key) if key else None
        def get(sk): return EXT.get(sk) if sk in EXT else EX.get(sk)
        if (n,zn) in EXT: ex=EXT[(n,zn)]; seen=np.zeros_like(seen)          # never seen from above: whole zone from the photo patch
        elif key and any(n.startswith(f[0]) for f in FORCE): ex=get(src); seen=np.zeros_like(seen)
        elif frac<0.15 and src: ex=get(src)
        if ex is None: ex=EX.get((n,zn))
        if ex is None and src: ex=get(src)
        if ex is None: continue
        img,_=fill(img,valid,seen,ex=ex,seed=hash(n)%1000)
    pad=cv2.inpaint(np.clip(img,0,255).astype(np.uint8),(~VV[n]).astype(np.uint8),3,cv2.INPAINT_TELEA)
    cv2.imwrite(f'{OUT}/{n}.png',pad)
if os.environ.get('DEREFLECT'):
    _d=cv2.cvtColor(cv2.imread(f'{OUT}/dash_F.png'),cv2.COLOR_BGR2LAB).astype(np.float32); _r=VV['dash_F']&(_d[...,1]>150)&(_d[...,0]>40)
    PAINT=np.median(_d[_r],0); print('one red paint (Lab, from the front dash):',np.round(PAINT))
    for n in info:
        if not n.startswith(('side_lower','dash_','fender_','side_upper','cab_','sign_','signtab_')): continue
        img=cv2.imread(f'{OUT}/{n}.png').astype(np.float32); v=VV[n]
        lab=cv2.cvtColor(img.astype(np.uint8),cv2.COLOR_BGR2LAB).astype(np.float32)
        red=v&(lab[...,1]>150)&(lab[...,0]>40)
        if red.sum()<500: continue
        # broad pale areas inside red panels are reflections (the white trim lines are thin and survive the opening)
        reg=cv2.GaussianBlur(red.astype(np.float32),(0,0),max(8,img.shape[0]/50))>0.22
        pale=v&reg&~red&(lab[...,0]>120)
        if n.startswith(('dash_','sign','cab_')): pale[:]=False          # lettering lives there: never treat white as reflection
        kw=max(5,int(img.shape[0]/170))|1
        broad=cv2.morphologyEx(pale.astype(np.uint8),cv2.MORPH_OPEN,np.ones((kw,kw),np.uint8)).astype(bool)
        broad=cv2.dilate(broad.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&v
        if broad.any():
            img=cv2.inpaint(img.astype(np.uint8),broad.astype(np.uint8),7,cv2.INPAINT_TELEA).astype(np.float32)
            lab=cv2.cvtColor(img.astype(np.uint8),cv2.COLOR_BGR2LAB).astype(np.float32)
            red=v&(lab[...,1]>150)&(lab[...,0]>40)
        sig=max(6,img.shape[0]/45)
        lo,_=nblur(lab,red,sig); tgt=PAINT if n.startswith(('side_lower','dash_','fender_','sign','cab_')) else np.median(lab[red],0)
        # also catch pale reflection streaks inside red panels: texels whose low-pass is red but which are pale themselves
        out=lab.copy(); m=red
        for c in range(3): out[...,c][m]=lab[...,c][m]-lo[...,c][m]+tgt[c]
        res=cv2.cvtColor(np.clip(out,0,255).astype(np.uint8),cv2.COLOR_LAB2BGR)
        cv2.imwrite(f'{OUT}/{n}.png',np.where(v[...,None],res,img.astype(np.uint8)))
        print('dereflect',n,'red frac %.2f'%(red.sum()/v.sum()),'broad pale %.3f'%(broad.sum()/v.sum()),'target Lab',np.round(tgt))
    # side panels and fender: the photos show sky reflections over almost the whole panel; the paint is rebuilt as the
    # one red measured on the front dash, keeping the thin white lining, the dark joints and the photo's fine detail
    # panel interiors (measured on the rectified side: dividers at x = +-1.82, 0.57, -0.64, -1.86, ends +-2.11, rail at z 1.21)
    XS=[(2.03,1.90),(1.74,0.65),(0.49,-0.56),(-0.72,-1.78),(-1.94,-2.03)]; ZS=[(0.77,1.13),(1.29,1.70)]
    def interiors(P):
        x,y,z=P[...,0],P[...,1],P[...,2]; m=np.zeros(x.shape,bool)
        for a,b in XS:
            for c,d in ZS: m|=(x<=a)&(x>=b)&(z>=c)&(z<=d)
        return m&(np.abs(y)>D_HW-0.01)
    D_HW=json.load(open('params.json'))['hw']
    for n in info:
        if not n.startswith(('side_lower','fender_')): continue
        img=cv2.imread(f'{OUT}/{n}.png').astype(np.float32); v=VV[n]
        lab=cv2.cvtColor(img.astype(np.uint8),cv2.COLOR_BGR2LAB).astype(np.float32)
        region=v if n.startswith('fender') else v&interiors(PP[n])
        hp=lab-cv2.GaussianBlur(lab,(0,0),3)
        out=PAINT[None,None,:]+0.3*hp
        soft=cv2.GaussianBlur(region.astype(np.float32),(0,0),1.5)[...,None]
        res=lab*(1-soft)+out*soft
        res=cv2.cvtColor(np.clip(res,0,255).astype(np.uint8),cv2.COLOR_LAB2BGR)
        cv2.imwrite(f'{OUT}/{n}.png',np.where(v[...,None],res,img.astype(np.uint8)))
        print('paint rebuilt',n,'region %.3f'%(region.sum()/v.sum()))
    # roof canvas: keep the photo patch's fine texture, halve its contrast around its median
    img=cv2.imread(f'{OUT}/roof.png').astype(np.float32); top=VV['roof']&(PP['roof'][...,2]>=3.0)
    med=np.median(img[top],0)*0.75; img[top]=med+0.25*(img[top]-np.median(img[top],0)); cv2.imwrite(f'{OUT}/roof.png',np.clip(img,0,255).astype(np.uint8))
    for n in ('monitor','roofboard'):
        img=cv2.imread(f'{OUT}/{n}.png').astype(np.float32); m=VV[n]; med=np.median(img[m],0); img[m]=med+0.5*(img[m]-med); cv2.imwrite(f'{OUT}/{n}.png',np.clip(img,0,255).astype(np.uint8))
print('done')
