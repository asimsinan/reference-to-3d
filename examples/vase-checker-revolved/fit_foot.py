"""foot below Z1: radii at fixed z knots, fitted so the union of projected discs matches the mask's rows and bottom"""
import numpy as np, cv2, json
from scipy.optimize import minimize
import cam as C
pr=json.load(open('profile.json')); ZP=np.array(pr['z']); RP=np.array(pr['r'])
sil=cv2.imread('mask_raw.png',0)>0
Z1=0.064; KZ=np.arange(0,0.064,0.004)
rows=np.arange(690,819,2); cols=np.arange(240,350,5)
obsL=np.array([np.where(sil[v])[0].min()-0.5 for v in rows]); obsR=np.array([np.where(sil[v])[0].max()+0.5 for v in rows])
obsB=np.array([np.where(sil[:,u])[0].max()+0.5 for u in cols])
ang=np.linspace(0,2*np.pi,240,endpoint=False)
r1=float(np.interp(Z1,ZP,RP))
def rz(x,z): return np.interp(z,np.r_[KZ,Z1],np.r_[x,r1])
def sil_rows(x):
    zs=np.linspace(0,Z1,90); r=rz(x,zs)
    L=np.full(len(rows),np.inf); R=np.full(len(rows),-np.inf); B=np.full(len(cols),-np.inf)
    for z,rr in zip(zs,r):
        uv=C.proj(np.stack([rr*np.cos(ang),rr*np.sin(ang),np.full_like(ang,z)],1)); u,v=uv[:,0],uv[:,1]
        vmin,vmax=v.min(),v.max(); umin,umax=u.min(),u.max()
        # ellipse ~ convex: row extent by interpolation on the polygon
        for k,vv in enumerate(rows):
            if vmin<=vv<=vmax:
                p=np.r_[uv,uv[:1]]; sg=np.sign(p[:,1]-vv); i=np.where(sg[:-1]!=sg[1:])[0]
                if len(i):
                    f=(vv-p[i,1])/(p[i+1,1]-p[i,1]); us=p[i,0]+f*(p[i+1,0]-p[i,0]); L[k]=min(L[k],us.min()); R[k]=max(R[k],us.max())
        for k,uu in enumerate(cols):
            if umin<=uu<=umax:
                p=np.r_[uv,uv[:1]]; sg=np.sign(p[:,0]-uu); i=np.where(sg[:-1]!=sg[1:])[0]
                f=(uu-p[i,0])/(p[i+1,0]-p[i,0]); vs=p[i,1]+f*(p[i+1,1]-p[i,1]); B[k]=max(B[k],vs.max())
    return L,R,B
def cost(x):
    return 0
    L,R,B=sil_rows(x); e=np.r_[L-obsL,R-obsR,B-obsB]; e[~np.isfinite(e)]=30
    sm=np.diff(np.r_[x,r1],2)*400
    return (e**2).mean()+(sm**2).mean()
x0=np.interp(KZ,ZP,RP); x0=np.clip(x0,0.03,0.06); x0=np.full(len(KZ),0.045)
print('start',cost(x0))
from scipy.optimize import least_squares
import json as _j
R0=C.P['R']; h0=C.P['h']
rim=[]
for u in range(200,390,6):
    ys=np.where(sil[:,u])[0]; rim.append((u,ys[0]-0.5))
for v in range(214,228,2):
    xs=np.where(sil[v])[0]; rim+=[(xs[0]-0.5,v),(xs[-1]+0.5,v)]
rim+=[(285,237),(300,237)]; rim=np.array(rim,float)
band=np.array([(240,743),(260,750),(290,755),(320,752),(340,745),(352,737)],float)
a2=np.linspace(0,2*np.pi,1440,endpoint=False)
def dist(pts,c): return np.sqrt(((pts[:,None]-c[None])**2).sum(2)).min(1)
NC=6
def resv(xx):
    cp=xx[:NC]; x=xx[NC:]
    C.P.update(D=cp[0],YC=cp[1],HC=cp[2],TH=cp[3],h=cp[4])
    rimc=C.proj(np.stack([R0*np.cos(a2),R0*np.sin(a2),np.full_like(a2,cp[4])],1))
    zg=cp[5]; rg=float(np.interp(zg,np.r_[KZ,Z1],np.r_[x,r1])); a3=a2[np.cos(a2)>0]
    bandc=C.proj(np.stack([rg*np.cos(a3),rg*np.sin(a3),np.full_like(a3,zg)],1))
    L,R,B=sil_rows(x); e=np.r_[L-obsL,R-obsR,0.3*(B-obsB)]; e[~np.isfinite(e)]=30
    return np.r_[e,np.diff(np.r_[x,r1],2)*400,dist(rim,rimc),dist(band,bandc)]
P0=C.P
c0=[P0['D'],P0['YC'],P0['HC'],P0['TH'],P0['h'],P0['zg']]
x0=np.r_[c0,x0]
res=least_squares(resv,x0,diff_step=0.01,x_scale=np.r_[[0.02,0.002,0.02,0.02,0.005,0.003],np.full(len(KZ),0.003)])
cp=res.x[:NC]; print('cam',np.round(cp,4),'TH deg %.2f'%np.degrees(cp[3]))
res.x=res.x[NC:]; resv(np.r_[cp,res.x])
P1=dict(_j.load(open('cam.json'))); P1.update(D=cp[0],YC=cp[1],HC=cp[2],TH=cp[3],h=cp[4],zg=cp[5]); _j.dump(P1,open('cam.json','w'),indent=1)
print('cost',cost(res.x)); print('radii',np.round(res.x,4),'r1 %.4f'%r1)
L,R,B=sil_rows(res.x)
print('row L err',np.round(L-obsL,1)); print('row R err',np.round(R-obsR,1)); print('bottom err',np.round(B-obsB,1))
json.dump(dict(KZ=KZ.tolist(),r=res.x.tolist(),Z1=Z1),open('foot.json','w'))
