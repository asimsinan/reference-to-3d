"""Parametric rotary desk phone (numpy only; used by the silhouette fit and by Blender). mm; +X front, +Y left, +Z up."""
import numpy as np, json, os
HERE=os.path.dirname(os.path.abspath(__file__))
P0=dict(
 # body
 xf=118., xb=-113., wf=67., wr=67., rc=20., z0=7., hbf=30., hbr=54., db=2.0,
 a_s=5., a_f=35., a_r=35., kh=4., kr=8., Rsf=16., Rsr=20., Rsb=9., Rfr=22., Rre=7.,
 # top profile (x,z) besides the dial plane
 zr0=99.8, sr=0.431, dial_drop=5.0,
 # dial (from solve)
 cx=65.8, cz=72.1, tau=26.9, Rn=55.0, hw=1.6, Rd=45.8,
 # prongs
 xe=-16.6, xer=-71.9, ye=34.2, we=6.2, ze=122., pt=9.,
 # handset
 hx=-44., hz=118., ha=52., hra=38., hbeta=62., hbw=14., hbt=10.5, hRc=29., hew=17., het=13., cyc=84.5, czc=62., ct=18., cupH=50., seam=12.,
 # feet
 L=190., yf=52., rf=11.,
)
def load():
    p=dict(P0);f=os.path.join(HERE,'params.json')
    if os.path.exists(f): p.update(json.load(open(f)))
    return p
def smin(a,b,k):
    h=np.clip(0.5+0.5*(b-a)/k,0,1);return b+(a-b)*h-k*h*(1-h)
def grid_faces(m,n,cu=False,cv=False):
    F=[]
    for i in range(m if cu else m-1):
        for j in range(n if cv else n-1):
            a=i*n+j;b=i*n+(j+1)%n;c=((i+1)%m)*n+(j+1)%n;d=((i+1)%m)*n+j;F.append((a,b,c,d))
    return F
def top_profile(p,x):
    t=np.tan(np.radians(p['tau']))
    zd=p['cz']-p['dial_drop']-t*(x-p['cx'])
    zk=p['zr0']+p['sr']*x
    return smin(zd,zk,p['kr'])
def edge(d,ztop,z0,R,ang):
    """wall profile: drafted straight wall from the base, then an arc of radius R rolling onto the top surface"""
    R=np.minimum(R,np.maximum(ztop-z0-1,1.));t=np.tan(np.radians(ang));dl=(ztop-R-z0)*t
    zl=z0+d/np.maximum(t,1e-6)
    u=np.clip(d-dl,0,R);za=ztop-R+np.sqrt(np.maximum(R*R-(R-u)**2,0))
    return np.where(d<dl,zl,za)
def body_z(p,x,y):
    w=p['wr']+(p['wf']-p['wr'])*(x-p['xb'])/(p['xf']-p['xb'])
    d1=w-np.abs(y);front=x>(p['xf']+p['xb'])/2
    d2=np.where(front,p['xf']-x,x-p['xb']);r=p['rc']
    inc=(d1<r)&(d2<r)
    dc=r-np.hypot(r-d1,r-d2);c=np.where(inc,np.minimum(d1,d2)-dc,0.)
    d1=np.maximum(d1-c,0);d2=np.maximum(d2-c,0)
    zt=top_profile(p,x)
    Rs=np.interp(x,[p['xb'],-45.,0.,60.,p['xf']],[p['Rsb'],p['Rsb'],p['Rsr'],p['Rsf'],p['Rsf']])
    zs=edge(d1,zt,p['z0'],Rs,p['a_s'])
    ze=np.where(front,edge(d2,zt,p['z0'],p['Rfr'],p['a_f']),edge(d2,zt,p['z0'],p['Rre'],p['a_r']))
    return smin(zs,ze,p['kh'])
def outline(p,n=240):
    """plan outline at the base (d=0), counter-clockwise, with the taper"""
    xf,xb,r=p['xf'],p['xb'],p['rc'];pts=[]
    wav=(p['wf']+p['wr'])/2;Lx=xf-xb;per=2*(Lx-2*r)+2*(2*wav-2*r)+2*np.pi*r
    for s in np.linspace(0,per,n,endpoint=False):
        segs=[(Lx-2*r,'s'),(np.pi*r/2,'c'),(2*wav-2*r,'s'),(np.pi*r/2,'c'),(Lx-2*r,'s'),(np.pi*r/2,'c'),(2*wav-2*r,'s'),(np.pi*r/2,'c')]
        # start at rear-right going forward along y=-w
        corners=[(xb+r,-wav),(xf-r,-wav+r),(xf,-wav+r),(xf-r,wav-r),(xf-r,wav),(xb+r,wav-r),(xb,wav-r),(xb+r,-wav+r)]
        dirs=[(1,0),None,(0,1),None,(-1,0),None,(0,-1),None];a0=[None,-90,None,0,None,90,None,180]
        u=s
        for k,(l,ty) in enumerate(segs):
            if u<=l or k==7:
                if ty=='s': x=corners[k][0]+dirs[k][0]*u;y=corners[k][1]+dirs[k][1]*u
                else:
                    a=np.radians(a0[k])+u/r;x=corners[k][0]+r*np.cos(a);y=corners[k][1]+r*np.sin(a)
                break
            u-=l
        w=p['wr']+(p['wf']-p['wr'])*(x-xb)/(xf-xb);pts.append((x,y*w/wav))
    return np.array(pts)
def body(p,n=240):
    o=outline(p,n);xs0,xs1=p['xb']+p['wr']*0.9,p['xf']-p['wf']*0.9
    sp=np.stack([np.clip(o[:,0],xs0,xs1),0*o[:,1]],1)
    dl=np.concatenate([np.linspace(0,8,26)[:-1],8+np.linspace(0,1,60)**1.5*(p['wr']*0.9-8)])
    S=dl/(p['wr']*0.9)
    V=[];
    V.append(np.c_[sp+(1-0.05)*(o-sp),np.full(len(o),p['z0'])])       # underside ring
    for s in S:
        q=sp+(1-s)*(o-sp);z=body_z(p,q[:,0],q[:,1]);V.append(np.c_[q,z])
    V=np.concatenate(V);F=grid_faces(len(S)+1,n,False,True)
    F.append(tuple(range(n))[::-1])
    return V,F
def tube(C,T,N,B,a,b,e=2.5,n=40):
    """loft superellipse sections (half-axes a along N, b along B) along centres C"""
    th=np.linspace(0,2*np.pi,n,endpoint=False);c,s=np.cos(th),np.sin(th)
    ex=2/e;cx=np.sign(c)*np.abs(c)**ex;sx=np.sign(s)*np.abs(s)**ex
    V=C[:,None,:]+a[:,None,None]*cx[None,:,None]*N[:,None,:]+b[:,None,None]*sx[None,:,None]*B[:,None,:]
    return V.reshape(-1,3),grid_faces(len(C),n,False,True)
def cup_profile(p):
    R=p['hRc'];H=p['cupH']
    pr=[(0.01,0.8),(R-9,0.8),(R-7.5,0.0),(R-3,0.0),(R-0.8,1.2),(R,4.0),(R,p['seam']-0.35),(R-0.5,p['seam']),(R,p['seam']+0.35)]
    for t in np.linspace(0,1,14)[1:]:
        h=p['seam']+0.35+(H-p['seam'])*t;pr.append((R*max(1-t**7.0,0)**0.5+0.01,h))
    return pr
def handset(p,side_n=48):
    """handle bar (lofted superellipse, ends bending down) + two cups (lathed bulbs on tilted axes)"""
    Vs=[];Fs=[];off=0
    a,ra,beta=p['ha'],p['hra'],np.radians(p['hbeta'])
    ys=list(np.linspace(-a,a,12));zs=[0.]*12;ang=[0.]*12
    for t in np.linspace(0,beta,12)[1:]:
        ys.append(a+ra*np.sin(t));zs.append(-ra*(1-np.cos(t)));ang.append(t)
        ys.insert(0,-(a+ra*np.sin(t)));zs.insert(0,-ra*(1-np.cos(t)));ang.insert(0,-t)
    ys,zs,ang=map(np.array,(ys,zs,ang));n=len(ys)
    g=np.clip((np.abs(ys)-a*0.5)/(a*0.5+ra*np.sin(beta)),0,1);g=g*g*(3-2*g)
    A=p['hbw']+(p['hew']-p['hbw'])*g;B=p['hbt']+(p['het']-p['hbt'])*g
    C=np.c_[np.full(n,p['hx']),ys,p['hz']+zs];T=np.c_[np.zeros(n),np.cos(ang),-np.sin(ang)]
    N=np.tile([1.,0,0],(n,1));Bn=np.cross(T,N)
    th=np.linspace(0,2*np.pi,side_n,endpoint=False);ex=2/2.6;c,s_=np.cos(th),np.sin(th)
    cx=np.sign(c)*np.abs(c)**ex;sx=np.sign(s_)*np.abs(s_)**ex
    # rounded ends: extra rings shrinking along the tangent
    er=p.get('hend',14.);phis=np.radians([18,36,54,70,82,89])
    def endrings(i,sgn):
        return [(C[i]+sgn*T[i]*er*np.sin(f),A[i]*np.cos(f),B[i]*np.cos(f),N[i],Bn[i]) for f in phis]
    rings=[(C[i],A[i],B[i],N[i],Bn[i]) for i in range(n)]
    rings=endrings(0,-1)[::-1]+rings+endrings(n-1,1);n=len(rings)
    V=np.stack([c_+a_*cx[:,None]*n_+b_*sx[:,None]*bn_ for (c_,a_,b_,n_,bn_) in rings])
    Vs.append(V.reshape(-1,3));Fs+=grid_faces(n,side_n,False,True)+[tuple(range(side_n)),tuple(range((n-1)*side_n,n*side_n))[::-1]];off+=n*side_n
    pr=cup_profile(p);t=np.radians(p['ct'])
    for sg in (1,-1):
        ax=np.array([0,-sg*np.sin(t),-np.cos(t)])          # cap normal: down and inward
        Pc=np.array([p['hx'],sg*p['cyc'],p['czc']]);e1=np.array([1.,0,0]);e2=np.cross(ax,e1)
        ring=[Pc-ax*h+r*(np.cos(th)[:,None]*e1+np.sin(th)[:,None]*e2) for (r,h) in pr]
        Vs.append(np.concatenate(ring));F=grid_faces(len(pr),side_n,False,True)
        Fs+=[tuple(i+off for i in (f if sg>0 else f[::-1])) for f in F];off+=len(pr)*side_n
    V=np.concatenate(Vs)
    # roll about the handle's long axis (caps swing to +x for positive roll), yaw about z, slide along y
    r=np.radians(p.get('hroll',0.));dx=V[:,0]-p['hx'];dz=V[:,2]-p['hz']
    V=np.c_[p['hx']+dx*np.cos(r)-dz*np.sin(r),V[:,1],p['hz']+dx*np.sin(r)+dz*np.cos(r)]
    w=np.radians(p.get('hyaw',0.));dx=V[:,0]-p['hx'];dy=V[:,1]
    V=np.c_[p['hx']+dx*np.cos(w)-dy*np.sin(w),dx*np.sin(w)+dy*np.cos(w)+p.get('hdy',0.),V[:,2]]
    return V,Fs
def box(c,h,rot=None):
    c=np.array(c,float);h=np.array(h,float)
    V=np.array([[sx,sy,sz] for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)],float)*h+c
    F=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)];return V,F
def cyl(c,axis,r,h,n=48,r2=None):
    c=np.array(c,float);axis=np.array(axis,float);axis/=np.linalg.norm(axis)
    u=np.cross(axis,[0,1.,0]);
    if np.linalg.norm(u)<1e-6:u=np.cross(axis,[1.,0,0])
    u/=np.linalg.norm(u);v=np.cross(axis,u);th=np.linspace(0,2*np.pi,n,endpoint=False)
    r2=r if r2 is None else r2
    ring=lambda rr,hh:c+axis*hh+rr*(np.cos(th)[:,None]*u+np.sin(th)[:,None]*v)
    V=np.concatenate([ring(r,0),ring(r2,h)]);F=grid_faces(2,n,False,True)+[tuple(range(n))[::-1],tuple(range(n,2*n))]
    return V,F
def dial_frame(p):
    t=np.radians(p['tau']);C=np.array([p['cx'],0,p['cz']])
    n=np.array([np.sin(t),0,np.cos(t)]);u=np.array([-np.cos(t),0,np.sin(t)]);v=np.array([0,1.,0]);return C,n,u,v
def prong_z(p): return p['ze']
def parts(p):
    out={}
    out['body']=body(p)
    out['handset']=handset(p)
    C,n,u,v=dial_frame(p)
    out['ring']=cyl(C-n*p['dial_drop'],n,p['Rn'],p['dial_drop'],96,p['Rn']-1.0)
    out['wheel']=cyl(C+n*(p['hw']-1.5),n,38.1,3.,96)
    zb=top_profile(p,np.array([p['xe']]))[0]-8
    for nm,x in (('pf',p['xe']),('pr',p['xer'])):
        for sg in (1,-1):
            out['%s%+d'%(nm,sg)]=box((x,sg*p['ye'],(p['ze']+zb)/2),(p['pt']/2,p['we'],(p['ze']-zb)/2))
    for i,(sx,sy) in enumerate([(1,1),(1,-1),(-1,1),(-1,-1)]):
        out['foot%d'%i]=cyl((sx*p['L']/2,sy*p['yf'],0),(0,0,1),p['rf'],p['z0']+1,24)
    return out
