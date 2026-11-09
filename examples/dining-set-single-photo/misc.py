from geom import *
import json
from scipy.optimize import least_squares
out={}
# seam: where it meets the near short edge's top line, and a point farther along it
for nm,(u,v) in {'seam_near':(359,429.2),'seam_mid':(470,383.5)}.items():
    P=hit_z(u,v,H); print(nm,np.round(P,3)); out[nm]=P.tolist()
# slots on the near long apron (face Y=-(W/2-0.019))
for nm,(u,v) in {'slot1':(560,441),'slot2':(735.5,375)}.items():
    P=hit_plane(u,v,[0,1,0],[0,-(W/2-0.019),0]); print(nm,np.round(P,3)); out[nm]=P.tolist()
# plant pot: radius 35 mm assumed; its rim's left edge at x=615 and the rim's front at y=293 (x ~ 628)
def r(p):
    X,Y,h=p; c=np.array([X,Y,H+h]); v=CAM-c; v[2]=0; v/=np.linalg.norm(v); side=np.cross([0,0,1],v)
    q=proj(np.array([c+0.035*side,c-0.035*side,c+0.035*v])); return [min(q[:2,0])-615, q[2,1]-293.5, (q[2,0]-632)*0.2]
s=least_squares(r,[0.42,0.02,0.06]); print('pot X %.3f Y %.3f rim height %.3f'%tuple(s.x)); out['pot']=s.x.tolist()
json.dump(out,open('misc.json','w'),indent=1)
