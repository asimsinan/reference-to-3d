"""Joint solve: 3 cameras + dial/feet/ear geometry. mm; +X front, +Y left, +Z up. Scale: finger wheel R=38.1"""
import numpy as np, json, cv2, sys
from scipy.optimize import least_squares
RW=38.1
OBS={
 'front':dict(
  wheel=[(649.5,1152,1),(1065,1175,1),(847,988,1),(865,1338,1),(704,1039,.4),(995,1040,.4),(702,1265,.4),(1020,1279,.4)],
  ring=[(547,1150,1),(850,947,1),(1161,1170,1),(860,1438,1),(574.5,1297,.5),(1106,1350,.5)],
  dig={1:(1011,1020),2:(901,975),3:(782,975),4:(674,1017),5:(609,1106),6:(607,1215),7:(680,1315),8:(798,1373),9:(936,1372),0:(1054,1313)},
  feet={'f-':(560,1654),'f+':(1171,1650)},
  ears={'--':(645,777),'-+':(701,777),'+-':(963,778),'++':(1020,778)}),
 'side':dict(
  wheel=[(811,853,1),(870,824,1),(1103,973,1),(1030,1015,1)],
  ring=[(739,847,1),(840,803,1),(1158,1003,.5),(796.7,930,1),(880,986.7,1),(963,1026.7,1),(1063,1053,1),(1030,870,.7),(1097,913,.7),(1140,957,.7)],
  dig={2:(818,820),3:(783,838),4:(785,882),5:(837,937),6:(932,1000),7:(1028,1032),8:(1097,1035),9:(1123,1008),0:(1110,962)},
  feet={'f-':(1055,1313),'r-':(282,1168)},
  ears={'-+':(598,722,),'++':(716,686)}),
 'rear':dict(wheel=[],ring=[],dig={},
  feet={'r+':(510,1638),'r-':(1033,1648)},
  ears={'r++':(587,1001),'r+-':(647,1001),'r-+':(919,1007),'r--':(978,1007)}),
}
W,H=1500,2000
def lookat(P,T):
    P=np.array(P,float);T=np.array(T,float)
    z=T-P;z/=np.linalg.norm(z);x=np.cross(z,[0,0,1]);x/=np.linalg.norm(x);y=np.cross(z,x)
    R=np.stack([x,y,z]);return cv2.Rodrigues(R)[0].ravel(),-R@P
def proj(cam,X):
    rv,t,f=cam[:3],cam[3:6],cam[6]
    R=cv2.Rodrigues(np.array(rv))[0];Xc=X@R.T+t
    return np.stack([W/2+f*Xc[:,0]/Xc[:,2],H/2+f*Xc[:,1]/Xc[:,2]],1)
NAMES=['cx','cz','tau','Rn','hw','Rd','L','yf','xer','xe','ye','we','ze']+['phi%d'%k for k in range(10)]
def geom(g):
    d=dict(zip(NAMES,g));C=np.array([d['cx'],0,d['cz']]);t=d['tau']
    n=np.array([np.sin(t),0,np.cos(t)]);u=np.array([-np.cos(t),0,np.sin(t)]);v=np.array([0,1.,0])
    a=np.linspace(0,2*np.pi,720,endpoint=False)[:,None]
    circ=lambda R,h:C+h*n+R*(np.cos(a)*u+np.sin(a)*v)
    dig={k:C+d['Rd']*(np.cos(d['phi%d'%k])*u+np.sin(d['phi%d'%k])*v) for k in range(10)}
    feet={'f-':(d['L']/2,-d['yf'],0),'f+':(d['L']/2,d['yf'],0),'r-':(-d['L']/2,-d['yf'],0),'r+':(-d['L']/2,d['yf'],0)}
    ears={s1+s2:(d['xe'],(1 if s1=='+' else -1)*d['ye']+(1 if s2=='+' else -1)*d['we'],d['ze']) for s1 in '+-' for s2 in '+-'}
    for k in list(ears): ears['r'+k]=(d['xer'],)+ears[k][1:]
    return d,circ(RW,d['hw']),circ(d['Rn'],0),dig,feet,ears
VIEWS=['front','side','rear']
def res(p,full=False):
    g=p[:len(NAMES)];d,cw,cr,dig,feet,ears=geom(g);out=[];rep={}
    for i,vn in enumerate(VIEWS):
        cam=p[len(NAMES)+7*i:len(NAMES)+7*i+7];o=OBS[vn];r=[]
        for key,c in (('wheel',cw),('ring',cr)):
            if o[key]:
                pc=proj(cam,c)
                for (x,y,w) in o[key]:
                    dd=pc-[x,y];j=np.argmin((dd**2).sum(1));r+=list(w*dd[j])
        for k,(x,y) in o['dig'].items(): r+=list(0.7*(proj(cam,dig[k][None])[0]-[x,y]))
        for k,(x,y) in o['feet'].items(): r+=list(0.5*(proj(cam,np.array(feet[k],float)[None])[0]-[x,y]))
        for k,(x,y) in o['ears'].items(): r+=list(0.7*(proj(cam,np.array(ears[k],float)[None])[0]-[x,y]))
        r.append((cam[6]-1450)/150*3)
        rep[vn]=np.sqrt(np.mean(np.square(r[:-1])));out+=r
    out.append((d['hw']-4)/4)   # weak prior: wheel a few mm above the ring plane
    return (np.array(out),rep) if full else np.array(out)
g0=[35,75,np.radians(32),54,4,46,150,55,-70,-25,33,5,105]+[np.radians(47-31*((k-1)%10)) for k in range(10)]
best=None
for fp in [(450,0,330),(380,0,420),(520,0,260)]:
  for sp in [(280,-420,140),(380,-330,120),(180,-480,160)]:
    c=[]
    for P,T in ((fp,(30,0,60)),(sp,(10,0,50)),((-fp[0],0,fp[2]-60),(0,0,60))):
        rv,t=lookat(P,T);c+=list(rv)+list(t)+[1450]
    s=least_squares(res,np.array(g0+c),x_scale='jac',max_nfev=400)
    if best is None or s.cost<best.cost: best=s
p=best.x;r,rep=res(p,True);d=dict(zip(NAMES,p))
print('cost',best.cost,'rms',rep)
for k in NAMES[:13]: print(k,round(np.degrees(d[k]) if k=='tau' else d[k],2))
print('phi',[round(np.degrees(d['phi%d'%k])%360,1) for k in [1,2,3,4,5,6,7,8,9,0]])
cams={}
for i,vn in enumerate(VIEWS):
    cam=p[len(NAMES)+7*i:len(NAMES)+7*i+7];R=cv2.Rodrigues(cam[:3])[0];P=-R.T@cam[3:6]
    print(vn,'pos',P.round(1),'f',round(cam[6],1),'look',R[2].round(3))
    cams[vn]=dict(rv=list(cam[:3]),t=list(cam[3:6]),f=cam[6],pos=list(P))
json.dump(dict(geom=d,cams=cams),open('cam.json','w'),indent=1)
