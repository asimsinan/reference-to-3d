"""vase outer profile (z,r) bottom -> rim, metres: foot.json below Z1, profile.json above, rim top at h"""
import json, os, numpy as np
HERE=os.getcwd(); P=json.load(open(f'{HERE}/cam.json'))
pr=json.load(open(f'{HERE}/profile.json')); ZP=np.array(pr['z']); RP=np.array(pr['r'])
h=P['h']
def ro(z): return float(np.interp(z,ZP,RP))
def prof_out(n=300):
    ft=json.load(open(f'{HERE}/foot.json')) if os.path.exists(f'{HERE}/foot.json') else None
    zs=np.linspace(0,h,n); out=[]
    for z in zs:
        if ft and z<ft['Z1']: r=float(np.interp(z,np.r_[ft['KZ'],ft['Z1']],np.r_[ft['r'],ro(ft['Z1'])]))
        else: r=ro(z)
        out.append((z,r))
    return out
import math
T=0.005                 # wall / lip thickness (porcelain, a guess; the lip read ~5 mm from the rim's two ellipses)
TL=0.0075             # lip bead thickness (the photo's opening is smaller than a 5 mm wall gives)
R=P['R']; ZC=h-TL/2; RC=R-TL/2
GOLD_RIM_Z=0.3021       # rim gold: outer face above this (front row 248)
GOLD_BAND=(0.0273,0.0350)   # foot band (front rows 748-762)
Z_FLOOR=0.012
def profile():
    """(z, r, tag) bottom centre -> outside -> lip -> inside -> floor centre"""
    pts=[(0.0015,0.0,'under'),(0.0015,0.044,'under'),(0.0,0.047,'under')]
    zs=np.unique(np.r_[np.linspace(0,0.29,170),0.293,GOLD_BAND,GOLD_RIM_Z])
    zs=zs[zs<=0.293]
    pts+=[(z,r,'out') for z,r in prof_out(800) if False]
    from geom import prof_out as po
    zr=np.array(po(1200)); 
    for z in zs: pts.append((z,float(np.interp(z,zr[:,0],zr[:,1])),'out'))
    # blend from the profile to the bead's outer point
    z0=0.293; r0=pts[-1][1]
    for t in np.linspace(0,1,7)[1:]:
        s=t*t*(3-2*t); pts.append((z0+(ZC-z0)*t, r0+(R-r0)*s,'out'))
    for k in range(1,13):
        a=math.pi*k/12; pts.append((ZC+TL/2*math.sin(a), RC+TL/2*math.cos(a),'lip' if k<=6 else 'lipin'))
    zi=np.linspace(ZC-0.006,Z_FLOOR+0.008,120)
    pts+=[(z,float(np.interp(z,zr[:,0],zr[:,1]))-T,'in') for z in zi]
    rc=0.006; zc=Z_FLOOR+rc; rcx=float(np.interp(zc,zr[:,0],zr[:,1]))-T-rc
    for k in range(1,9):
        a=math.pi/2*k/8; pts.append((zc-rc*math.sin(a), rcx+rc*math.cos(a),'in'))
    pts+=[(Z_FLOOR,rcx*0.5,'floor'),(Z_FLOOR,0.0,'floor')]
    return pts
