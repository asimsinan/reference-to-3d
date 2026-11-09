"""Camera + table dims from one photo. World: table centre on the floor, X along the length (short end AB at -L/2,
the near long side BC at Y=-W/2), z up, metres. Top surface at H=0.75 (assumed: standard dining height)."""
import numpy as np, json, sys
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
E=json.load(open('e2.json')); H=0.75; RB=0.018; CX=500.0
LEGS={'A':((-1,1),(262.5,862.5)),'B':((-1,-1),(509,944)),'D':((1,1),(545.5,636))}
FIX_PITCH = '--level' in sys.argv
def unpack(p):
    rv,t,f,cy,L,W,T,bx,by=p[0:3],p[3:6],p[6],p[7],p[8],p[9],p[10],p[11],p[12]
    return Rot.from_rotvec(rv).as_matrix(),t,f,cy,L,W,T,bx,by
def proj(p,X):
    R,t,f,cy,*_=unpack(p); Xc=X@R.T+t
    return np.c_[f*Xc[:,0]/Xc[:,2]+CX, f*Xc[:,1]/Xc[:,2]+cy]
def lines(p):
    R,t,f,cy,L,W,T,bx,by=unpack(p)
    return {'near_short_top':((-L/2,-1,H),(-L/2,1,H)),'near_short_bot':((-L/2,-1,H-T),(-L/2,1,H-T)),
            'near_long_top':((-1,-W/2,H),(1,-W/2,H)),'near_long_bot':((-1,-W/2,H-T),(1,-W/2,H-T)),
            'far_long':((-1,W/2,H),(1,W/2,H)),'far_short':((L/2,-1,H),(L/2,1,H))}
def res(p):
    R,t,f,cy,L,W,T,bx,by=unpack(p); out=[]
    for k,(a,b) in lines(p).items():
        q=proj(p,np.array([a,b],float)); d=q[1]-q[0]; n=np.array([-d[1],d[0]])/np.linalg.norm(d)
        P=np.array(E[k]); out.append((P-q[0])@n)
    C=-R.T@t
    for k,((sx,sy),uv) in LEGS.items():
        c=np.array([sx*bx,sy*by,0.0]); h=C-c; h[2]=0; h/=np.linalg.norm(h)
        out.append(3*(proj(p,(c+RB*h)[None])[0]-uv))
    if FIX_PITCH:   # camera's y axis (down) has no horizontal component along its viewing direction: level camera
        out.append([300*R[2,2]])
    return np.concatenate([np.ravel(o) for o in out])
best=None
for yaw in [30,45,60]:
  for pitch in [5,15,30]:
    for dist in [2.5,3.5,5]:
      fwd=np.array([np.cos(np.radians(yaw)),np.sin(np.radians(yaw)),0]); right=np.array([fwd[1],-fwd[0],0]); down=np.array([0,0,-1.])
      R0=np.array([right,down,fwd]); R0=Rot.from_euler('x',-pitch,degrees=True).as_matrix()@R0
      C0=np.array([0,0,0.75])-dist*R0[2]
      p0=np.r_[Rot.from_matrix(R0).as_rotvec(),-R0@C0,1500,500,1.2,0.6,0.03,0.5,0.25]
      try:
        r=least_squares(res,p0,bounds=([-np.inf]*6+[300,-3000,0.4,0.3,0.005,0.1,0.05],[np.inf]*6+[8000,3000,3,1.5,0.1,1.5,0.7]))
      except Exception as e: continue
      if best is None or r.cost<best.cost: best=r
p=best.x; R,t,f,cy,L,W,T,bx,by=unpack(p); C=-R.T@t
rr=res(p); print('rms %.2f px  max %.2f'%(np.sqrt((rr**2).mean()),np.abs(rr).max()))
pitch=np.degrees(np.arcsin(R[2,2])); yaw=np.degrees(np.arctan2(R[2,1],R[2,0])); roll=np.degrees(np.arctan2(-R[0,2],-R[1,2]))
print('f %.0f cy %.1f  L %.3f W %.3f T %.3f  legs bx %.3f by %.3f'%(f,cy,L,W,T,bx,by))
print('camera at',np.round(C,3),' pitch(fwd z) %.2f deg yaw %.1f'%(pitch,yaw))
J=best.jac; cov=np.linalg.pinv(J.T@J)*(rr**2).mean(); sd=np.sqrt(np.diag(cov))
print('sd f %.0f cy %.0f L %.3f W %.3f'%(sd[6],sd[7],sd[8],sd[9]))
for k,((sx,sy),uv) in LEGS.items(): pass
json.dump({'R':R.tolist(),'t':t.tolist(),'f':f,'cx':CX,'cy':cy,'L':L,'W':W,'T':T,'H':H,'bx':bx,'by':by,'C':C.tolist()},open('cam.json' if '--level' not in sys.argv else 'cam_level.json','w'),indent=1)
