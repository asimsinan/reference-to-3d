from geom import *
import json
from scipy.optimize import least_squares
E=json.load(open('e3.json'))
def linres(P,a,b):
    q=proj(np.array([a,b])); d=q[1]-q[0]; n=np.array([-d[1],d[0]])/np.linalg.norm(d); return (np.array(P)-q[0])@n
def r1(p):
    o,zb=p
    return np.r_[linres(E['apron_short_bot'],(-L/2+o,-1,zb),(-L/2+o,1,zb)), linres(E['apron_long_bot'],(-1,-W/2+o,zb),(1,-W/2+o,zb))]
s=least_squares(r1,[0.06,0.65]); print('apron setback %.3f  bottom z %.3f  (apron height %.3f below top underside) rms %.2f'%(s.x[0],s.x[1],H-T-s.x[1],np.sqrt((s.fun**2).mean())))
json.dump({'apron_o':s.x[0],'apron_zb':s.x[1]},open('apron.json','w'))
# leg tops: symmetric (tx,ty), z free per leg
tops={'A':((-1,1),(264.0,480)),'B':((-1,-1),(498.0,470)),'C':((1,-1),(736.4,400)),'D':((1,1),(546.7,510))}
def r2(p):
    tx,ty=p[:2]; out=[]
    for i,(k,((sx,sy),uv)) in enumerate(tops.items()):
        out.append(proj([sx*tx,sy*ty,p[2+i]])[0]-uv)
    return np.ravel(out)
s=least_squares(r2,[0.53,0.23,.6,.6,.6,.6]); print('leg tops tx %.3f ty %.3f  z'%tuple(s.x[:2]),np.round(s.x[2:],3),' resid px',np.round(s.fun.reshape(-1,2)[:,0],1))
print('leg bottoms bx %.3f by %.3f'%(C_['bx'],C_['by']))
# leg radii from image widths at known points
for k,(uv,wpx) in {'A_top':((264,480),33.8),'A_bot':((262.4,840),33.5),'B_top':((498,470),38.5),'B_bot':((510.6,920),35.3),'D_bot':((545,622),22.2),'C_top':((736,400),23.6)}.items():
    leg=k[0]; (sx,sy)=dict(A=(-1,1),B=(-1,-1),C=(1,-1),D=(1,1))[leg]
    # depth of the leg axis at that row: intersect ray with vertical plane through the leg's (approx) axis, facing camera
    c=np.array([sx*C_['bx'],sy*C_['by'],0]); n=CAM-c; n[2]=0; n/=np.linalg.norm(n)
    X=hit_plane(uv[0],uv[1],n,c); dep=((X-CAM)@R[2]); print('  %s diameter %.1f mm (z %.2f)'%(k,wpx*dep/F*1000,X[2]))
r=0.0275
for name,ox,oy in [('flush legs',L/2-(C_['bx']+r),W/2-(C_['by']+r))]:
    def r3(p): zb=p[0]; return np.r_[linres(E['apron_short_bot'],(-L/2+ox,-1,zb),(-L/2+ox,1,zb)), linres(E['apron_long_bot'],(-1,-W/2+oy,zb),(1,-W/2+oy,zb))]
    s=least_squares(r3,[0.65]); f=s.fun; print(name,'ox %.3f oy %.3f zb %.3f  rms short %.2f long %.2f'%(ox,oy,s.x[0],np.sqrt((f[:14]**2).mean()),np.sqrt((f[14:]**2).mean())))
# separate: short side o from the short line with zb from long line given oy flush
def r4(p): ox,zb=p; return np.r_[linres(E['apron_short_bot'],(-L/2+ox,-1,zb),(-L/2+ox,1,zb)), linres(E['apron_long_bot'],(-1,-W/2+0.019,zb),(1,-W/2+0.019,zb))]
s=least_squares(r4,[0.03,0.65]); print('long flush, short free: ox %.3f zb %.3f rms %.2f'%(s.x[0],s.x[1],np.sqrt((s.fun**2).mean())))
