from geom import *
import json
from scipy.optimize import least_squares
E=json.load(open('es1.json')); CU=json.load(open('cush.json'))
cx,cy,th,a,b,rc,zr,zt=CU['S1']; TW=0.012
c,s=np.cos(th),np.sin(th); Wp=lambda x,y,z: np.array([cx+c*x-s*y, cy+s*x+c*y, z])
def linres(P,A,B):
    q=proj(np.array([A,B])); d=q[1]-q[0]; n=np.array([-d[1],d[0]])/np.linalg.norm(d); return (np.array(P)-q[0])@n
r=least_squares(lambda p: linres(E['bot_nl'][:-2],Wp(-(a+TW),-1,p[0]),Wp(-(a+TW),1,p[0])),[0.35]); zb=r.x[0]
r2=least_squares(lambda p: linres(E['rim_nl'],Wp(-(a+TW),-1,p[0]),Wp(-(a+TW),1,p[0])),[0.39]); zrt=r2.x[0]
print('tray bottom z %.3f (rms %.2f)  rim top z %.3f (rms %.2f)  tray height %.3f'%(zb,np.sqrt((r.fun**2).mean()),zrt,np.sqrt((r2.fun**2).mean()),zrt-zb))
# leg tops: rays of the leg-top centres to plane z=zb, in the stool's frame
def local(P): d=P-np.array([cx,cy,0]); return np.array([c*d[0]+s*d[1], -s*d[0]+c*d[1]])
for nm,uv in {'S1 front-left':(647,694),'S1 front-right':(778,717)}.items():
    P=hit_z(*uv,zb); print('  %s top at local'%nm,np.round(local(P),3))
CB=CU['bench']; bcx,bcy,bth=CB[:3]
for nm,uv in {'bench L1':(118,586),'bench L2':(211,603)}.items():
    P=hit_z(*uv,zb); d=P-np.array([bcx,bcy,0]); print('  %s top at local'%nm,np.round(d[:2],3))
# leg diameters: width px * depth / f
for nm,(uv,w,z) in {'S1 FL top':((647,694),30,zb),'S1 FL bottom':((599,898),12,0.02),'S1 FR top':((778,717),31,zb),'S1 FR bottom':((795,948),13,0.02),
                    'bench L1 top':((118,588),22,zb),'bench L1 bottom':((95,762),11,0.02)}.items():
    P=hit_z(*uv,z); dep=(P-CAM)@R[2]; print('  %s diameter %.1f mm'%(nm,w*dep/F*1000))
json.dump({'zb':zb,'zrt':zrt,'TW':TW},open('tray.json','w'))
