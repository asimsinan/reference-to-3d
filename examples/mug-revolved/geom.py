"""Mug profile (z, r, tag) bottom-centre -> outside -> lip -> inside -> inner-floor centre. Metres."""
import json, math, os
import numpy as np
HERE=os.getcwd()   # data (cam.json, profile.json, bottom.json) are in the working folder
P=json.load(open(f'{HERE}/cam.json')); pr=json.load(open(f'{HERE}/profile.json'))
ZP=np.array(pr['z']); RP=np.array(pr['r'])
h=P['h']
def ro(z): return float(np.interp(z,ZP,RP))
T_RIM=0.0035; T_LOW=0.0045; Z_FLOOR=0.0095
def thick(z): return T_LOW+(T_RIM-T_LOW)*min(max((z-0.02)/(h-0.03),0),1)
def profile():
    pts=[]
    # underside: recessed centre, foot ring
    bt=json.load(open(f'{HERE}/bottom.json')); rf,pw,Z1=bt['rf'],bt['p'],bt['Z1']   # fit_bottom.py
    pts+=[(0.0015,0.0,'under'),(0.0015,rf-0.0045,'under'),(0.0,rf-0.0025,'under'),(0.0,rf,'foot')]
    r1=ro(Z1)
    for t in np.linspace(0,1,13)[1:]:
        z=t*Z1; pts.append((z,rf+(r1-rf)*(1-(1-t)**pw)**(1/pw),'out'))
    zs=np.linspace(Z1+0.0025,h-0.0025,42)
    pts+=[(z,ro(z),'out') for z in zs]
    # lip: half circle from the outer to the inner wall
    rt=ro(h-0.0025); c=(h-T_RIM/2, rt-T_RIM/2); a=T_RIM/2
    for k in range(0,13):
        t=math.pi*k/12; pts.append((c[0]+a*math.sin(t), c[1]+a*math.cos(t),'lip' if k<=6 else 'in'))   # inner half: inside texture
    pts[-13]=(h-T_RIM/2,rt,'lip')
    # inside wall going down
    zi=np.linspace(h-T_RIM/2-0.003,Z_FLOOR+0.007,40)
    pts+=[(z,ro(z)-thick(z),'in') for z in zi]
    # rounded inner corner to the floor
    rc=0.006; zc=Z_FLOOR+rc; rcx=ro(zc)-thick(zc)-rc
    for k in range(1,9):
        t=math.pi/2*k/8; pts.append((zc-rc*math.sin(t), rcx+rc*math.cos(t),'in'))
    pts+=[(Z_FLOOR,rcx*0.5,'floor'),(Z_FLOOR,0.0,'floor')]
    return pts
if __name__=='__main__':
    for p in profile(): print('%.4f %.4f %s'%p)
