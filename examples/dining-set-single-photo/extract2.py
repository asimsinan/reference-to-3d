"""Oak, legs and linen from the photo (v2): exemplars with validity masks; wood grown in long strips along the grain."""
from geom import *
import cv2, json, sys
img=cv2.imread('ref.jpg').astype(np.float32)
S=json.load(open('scene.json')); TB=S['table']; SE=S['seats']
alpha=cv2.imread('r_id/photo.png',cv2.IMREAD_UNCHANGED)[...,3]>0   # rendered model coverage (for object masks)
idimg=cv2.imread('r_id/photo.png',cv2.IMREAD_UNCHANGED)[...,:3].astype(int)
def rect(fn, nu, nv, want_mask=None):
    c,r=np.meshgrid((np.arange(nu)+.5)/nu,(np.arange(nv)+.5)/nv); P=fn(c.ravel(),1-r.ravel())
    q=proj(P).astype(np.float32); mx,my=q[:,0].reshape(nv,nu),q[:,1].reshape(nv,nu)
    t=cv2.remap(img,mx,my,cv2.INTER_CUBIC)
    m=np.ones((nv,nu),bool) if want_mask is None else cv2.remap(want_mask.astype(np.uint8),mx,my,cv2.INTER_NEAREST)>0
    return t,m
def delight(t,sig):
    lum=t.mean(2); low=cv2.GaussianBlur(lum,(0,0),sig); return t*(lum.mean()/np.maximum(low,1))[...,None]
def match(t,ref):   # mean and std per channel to the reference exemplar
    m,s=t.reshape(-1,3).mean(0),t.reshape(-1,3).std(0); mr,sr=ref.reshape(-1,3).mean(0),ref.reshape(-1,3).std(0)
    return (t-m)/np.maximum(s,1e-3)*sr+mr
MM=1.65e-3; nu=lambda a,b: int(round(abs(b-a)/MM))
ax=-TB['short_apron_x']; zb=TB['apron_zb']; zt=TB['H']-TB['T']; ly=-TB['long_apron_y']; H_=TB['H']
EX=[]
t,m=rect(lambda u,v: np.c_[np.full_like(u,ax),0.165-0.355*u,zb+0.005+(zt-zb-0.01)*v],nu(0,0.355),nu(0,zt-zb-0.01)); EX.append([delight(t,15),m])
t,m=rect(lambda u,v: np.c_[-0.40+0.35*u,np.full_like(u,ly),zb+0.005+(zt-zb-0.01)*v],nu(0,0.35),nu(0,zt-zb-0.01)); EX.append([delight(t,15),m])
# the tabletop near half: grain along X (u), across Y (v); objects and the seam masked out
top_ok=~((idimg.sum(2)>0)&False)
objmask=np.ones((1000,1000),np.uint8)
for (x0,y0,x1,y1) in [(340,330,415,395),(518,348,595,412),(484,310,610,362),(560,270,670,340)]: objmask[y0:y1,x0:x1]=0
t,m=rect(lambda u,v: np.c_[-0.60+0.75*u,-0.265+0.53*v,np.full_like(u,H_)],nu(0,0.75),nu(0,0.53),objmask)
sy=(TB['seam_y']+0.265)/0.53; rows=t.shape[0]; rs=int(round((1-sy)*rows)); m[max(0,rs-5):rs+6]=False
t=delight(t,25)   # the top: its grain is washed out by the sheen in the photo; not used
ref=EX[0][0]
for e in EX[1:]: e[0]=match(e[0],ref)
for i,(e,mm) in enumerate(EX): cv2.imwrite(f'ex2_oak_{i}.png',np.clip(np.where(mm[...,None],e,0),0,255).astype(np.uint8))
def mincut(err):
    E=err.copy()
    for i in range(1,E.shape[0]):
        l=np.r_[np.inf,E[i-1,:-1]]; r=np.r_[E[i-1,1:],np.inf]; E[i]+=np.minimum(np.minimum(l,E[i-1]),r)
    p=np.zeros(E.shape[0],int); p[-1]=int(np.argmin(E[-1]))
    for i in range(E.shape[0]-2,-1,-1):
        j=p[i+1]; lo,hi=max(0,j-1),min(E.shape[1],j+2); p[i]=lo+int(np.argmin(E[i,lo:hi]))
    return p
def quilt(exs, H, W, PH, PW, OH, OW, seed=0, ncand=600):
    rng=np.random.default_rng(seed); sh,sw=PH-OH,PW-OW; assert H%sh==0 and W%sw==0
    cands=[]
    for k,(e,m) in enumerate(exs):
        ii=cv2.integral(m.astype(np.uint8)); 
        for y in range(0,e.shape[0]-PH+1,2):
            for x in range(0,e.shape[1]-PW+1,3):
                if ii[y+PH,x+PW]-ii[y,x+PW]-ii[y+PH,x]+ii[y,x]==PH*PW: cands.append((k,y,x))
    out=np.zeros((H,W,3),np.float32); filled=np.zeros((H,W),bool)
    for i in range(H//sh):
        for j in range(W//sw):
            ys=(np.arange(PH)+i*sh)%H; xs=(np.arange(PW)+j*sw)%W
            reg=out[np.ix_(ys,xs)]; fm=filled[np.ix_(ys,xs)]
            pick=rng.choice(len(cands),min(ncand,len(cands)),replace=False); errs=np.empty(len(pick))
            for n,c_ in enumerate(pick):
                k,y,x=cands[c_]; p=exs[k][0][y:y+PH,x:x+PW]; errs[n]=(((p-reg)**2).sum(2)*fm).sum()
            ok=np.where(errs<=errs.min()*1.12+1e-6)[0]; k,y,x=cands[pick[rng.choice(ok)]]
            p=exs[k][0][y:y+PH,x:x+PW]; d=((p-reg)**2).sum(2); keep=np.zeros((PH,PW),bool)
            if fm[:, :OW].all():
                pth=mincut(d[:, :OW]); [keep.__setitem__((r_,slice(0,pth[r_])),True) for r_ in range(PH)]
            if fm[:, -OW:].all():
                pth=mincut(d[:, -OW:][:, ::-1]); [keep.__setitem__((r_,slice(PW-pth[r_],PW)),True) for r_ in range(PH)]
            if fm[:OH,:].all():
                pth=mincut(d[:OH,:].T); [keep.__setitem__((slice(0,pth[c2]),c2),True) for c2 in range(PW)]
            if fm[-OH:,:].all():
                pth=mincut(d[-OH:,:].T[:, ::-1]); [keep.__setitem__((slice(PH-pth[c2],PH),c2),True) for c2 in range(PW)]
            out[np.ix_(ys,xs)]=np.where(keep[...,None]&fm[...,None],reg,p); filled[np.ix_(ys,xs)]=True
    return out
def pnoise(shape, sig_u, sig_v, seed):
    r=np.random.default_rng(seed).normal(size=shape); fy=np.fft.fftfreq(shape[0])[:,None]; fx=np.fft.fftfreq(shape[1])[None,:]
    o=np.real(np.fft.ifft2(np.fft.fft2(r)*np.exp(-2*np.pi**2*((fx*sig_u)**2+(fy*sig_v)**2)))); return o/o.std()
def finish(q, name, fine, nstr):
    big=np.clip(cv2.resize(q,None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC)*(1+fine[...,None]),0,255)
    cv2.imwrite(f'tex/{name}.png',big.astype(np.uint8))
    g=cv2.GaussianBlur(big.mean(2).astype(np.float32),(0,0),1.0); g=g-cv2.GaussianBlur(g,(0,0),8)
    dx=cv2.Sobel(g,cv2.CV_32F,1,0)/255*nstr; dy=cv2.Sobel(g,cv2.CV_32F,0,1)/255*nstr
    n=np.dstack([-dx,dy,np.ones_like(dx)]); n/=np.linalg.norm(n,axis=2,keepdims=True); cv2.imwrite(f'tex/{name}_n.png',((n[...,::-1]*0.5+0.5)*255).astype(np.uint8))
    return big
what=sys.argv[1:] or ['oak','leg','fab']
if 'oak' in what:
    q=quilt(EX, 360, 840, 40, 160, 10, 40, 1)       # 0.59 m x 1.39 m
    cv2.imwrite('q_oak.png',np.clip(q,0,255).astype(np.uint8))
    sh=(q.shape[0]*4,q.shape[1]*4); fine=-0.18*np.clip((pnoise(sh,7,0.7,4)-2.0)/0.8,0,1)+0.02*pnoise(sh,200,0.9,5)
    finish(q,'oak_photo',fine,0.5)
if 'leg' in what:
    def leg_strip(lx,ly,z0,z1,r=0.027,span=0.6):
        d=CAM[:2]-np.array([lx,ly]); a0=np.arctan2(d[1],d[0])
        return rect(lambda u,v: np.c_[lx+r*np.cos(a0+(v-0.5)*2*span), ly+r*np.sin(a0+(v-0.5)*2*span), z0+(z1-z0)*u],int((z1-z0)/1.5e-3),int(2*span*r/1.5e-3))
    L_=[]
    for k in (1,0):
        t,m=leg_strip(*TB['legs'][k],0.06,0.62); t=t/np.maximum(t.mean(1,keepdims=True),1)*t.reshape(-1,3).mean(0); L_.append([delight(t,30),m])
    L_[1][0]=match(L_[1][0],L_[0][0])
    for i,(e,mm) in enumerate(L_): cv2.imwrite(f'ex2_leg_{i}.png',np.clip(e,0,255).astype(np.uint8))
    q=quilt(L_, 96, 800, 16, 200, 4, 40, 2)
    cv2.imwrite('q_leg.png',np.clip(q,0,255).astype(np.uint8))
    sh=(q.shape[0]*4,q.shape[1]*4); fine=-0.12*np.clip((pnoise(sh,6,0.7,7)-2.1)/0.8,0,1)+0.015*pnoise(sh,150,0.8,8)
    finish(q,'leg_photo',fine,0.4)
if 'fab' in what:
    F_=[[delight(img[595:640,670:800],8),None],[delight(img[505:545,770:880],8),None],[delight(img[600:650,640:700],8),None]]
    for f in F_: f[1]=np.ones(f[0].shape[:2],bool)
    for f in F_[1:]: f[0]=match(f[0],F_[0][0])
    q=quilt(F_, 300, 300, 20, 20, 5, 5, 3)
    cv2.imwrite('q_fab.png',np.clip(q,0,255).astype(np.uint8))
    sh=(q.shape[0]*4,q.shape[1]*4); yy,xx=np.mgrid[:sh[0],:sh[1]]
    w=np.where(((xx//2+yy//2)%2)==0,np.sin(np.pi*(xx%2+0.5)/2),np.sin(np.pi*(yy%2+0.5)/2))
    fine=0.05*(w-w.mean())+0.03*pnoise(sh,0.8,0.8,9)
    finish(q,'linen_photo',fine,1.2)
print('done')
