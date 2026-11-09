"""Tabletop objects from image readings: each round object's base sits on the top (z=H). Reading per object:
base (left x, right x, lowest y of the base), top rim (left x, right x, the rim's front-most y)."""
from geom import *
import json
from scipy.optimize import least_squares
def cyl(base, top):
    (bl,br,bv),(tl,tr,tv)=base,top
    def res(p):
        X,Y,rb,rt,h=p; c=np.array([X,Y,H])
        v=CAM-c; v[2]=0; v/=np.linalg.norm(v); side=np.cross([0,0,1],v)   # side: to the camera's right? sign checked by abs
        out=[]
        for z,r,(l,rr,vv) in ((H,rb,base),(H+h,rt,top)):
            q=proj(np.array([c+[0,0,z-H]+r*side, c+[0,0,z-H]-r*side, c+[0,0,z-H]+r*v]))
            out+= [min(q[0,0],q[1,0])-l, max(q[0,0],q[1,0])-rr, q[2,1]-vv]
        return np.array(out)
    P0=hit_z((bl+br)/2,bv,H)
    r=least_squares(res,[P0[0],P0[1],0.035,0.04,0.08]); X,Y,rb,rt,h=r.x
    return dict(X=X,Y=Y,rb=rb,rt=rt,h=h,rms=float(np.sqrt((r.fun**2).mean())))
O={}
O['cup1']=cyl((362,387,377),(355,391,341.5))
O['cup2']=cyl((545,575,398.5),(540.5,580,362))
O['candle']=cyl((621.5,659,333),(621.5,659,305))
O['plate']=cyl((503,590,356),(493,601,350))
O['muffin1']=cyl((518,546,344),(515,548,335))
O['muffin2']=cyl((560,588,343),(557,590,334))
O['coaster1']=cyl((352,396,388),(352,396,384))
O['coaster2']=cyl((530,575,406),(530,575,402))
for k,v in O.items(): print('%-8s X %.3f Y %.3f  r_base %.1f mm r_top %.1f mm  h %.1f mm  rms %.1f px'%(k,v['X'],v['Y'],v['rb']*1000,v['rt']*1000,v['h']*1000,v['rms']))
# sphere: centre on the ray through its image centre, image radius 24.5 px, resting on the top (centre z = H + R)
u,v,rp=594.5,304.0,24.5
def rs(p):
    d,Rr=p; o,dd=ray(u,v); C=o+d*dd; return [C[2]-(H+Rr), Rr*F/((C-CAM)@R[2])-rp]
s=least_squares(rs,[2.8,0.05]); o,dd=ray(u,v); Cs=o+s.x[0]*dd
O['sphere']=dict(X=Cs[0],Y=Cs[1],R=s.x[1]); print('sphere   X %.3f Y %.3f  R %.1f mm'%(Cs[0],Cs[1],s.x[1]*1000))
json.dump(O,open('objs.json','w'),indent=1)
