from geom import *
import json
from scipy.optimize import least_squares
CU=json.load(open('cush.json')); TR=json.load(open('tray.json')); AX=json.load(open('legaxes.json')); zb=TR['zb']
FEET={'S1':{'FL':(598,903),'FR':(795,953),'BR':(846,830),'BL':(683,793)},'S2':{'FL':(700,776),'FR':(856,815),'BR':(904,728)},
      'bench':{'L1':(95,766),'L2':(225,802),'L3':(451,623),'L4':(338,607)}}
SIG={'FL':(-1,1),'FR':(-1,-1),'BR':(1,-1),'BL':(1,1),'L1':(-1,1),'L2':(-1,-1),'L3':(1,-1),'L4':(1,1)}
AXK={'S1':{'FL':'S1_FL','FR':'S1_FR','BR':'S1_BR'},'S2':{'FR':'S2_FR','BR':'S2_BR'},'bench':{'L1':'B_L1','L2':'B_L2','L3':'B_L3','L4':'B_L4'}}
OFF={}
def W_(nm,x,y,z):
    cx,cy,th=CU[nm][:3]; cx+=OFF.get(nm,(0,0))[0]; cy+=OFF.get(nm,(0,0))[1]; c,s=np.cos(th),np.sin(th); return np.array([cx+c*x-s*y,cy+s*x+c*y,z])
def res(p,groups):
    ux,uy,fx,fy=p[:4]; out=[]
    for i,nm in enumerate(groups): OFF[nm]=(p[4+2*i],p[5+2*i])
    for nm in groups:
        for k,uv in FEET[nm].items():
            sx,sy=SIG[k]; out.append(proj(W_(nm,sx*fx,sy*fy,0.008))[0]-uv)
        for k,ak in AXK[nm].items():
            sx,sy=SIG[k]; a=AX[ak]
            for P in (W_(nm,sx*ux,sy*uy,zb), W_(nm,sx*(0.6*ux+0.4*fx),sy*(0.6*uy+0.4*fy),0.4*zb)):
                u,v=proj(P)[0]; out.append([3*(u-(a['m']*v+a['c']))])
    return np.concatenate([np.ravel(o) for o in out])
outp={}
for name,groups,p0 in [('stool',['S1','S2'],[0.15,0.12,0.19,0.15]),('bench',['bench'],[0.40,0.12,0.45,0.15])]:
    r=least_squares(lambda p: res(p,groups),p0+[0,0]*len(groups)); ux,uy,fx,fy=r.x[:4]; res(r.x,groups); print('   offsets',{k:np.round(v,3).tolist() for k,v in OFF.items()})
    print('%s: leg tops (%.3f, %.3f) at z %.3f  feet (%.3f, %.3f)  splay x %.1f deg y %.1f deg  rms %.2f px'%(name,ux,uy,zb,fx,fy,
          np.degrees(np.arctan((fx-ux)/zb)),np.degrees(np.arctan((fy-uy)/zb)),np.sqrt((r.fun**2).mean())))
    print('   residuals',np.round(r.fun,1))
    outp[name]=dict(ux=ux,uy=uy,fx=fx,fy=fy,off={k:list(OFF[k]) for k in groups})
json.dump(outp,open('splay.json','w'),indent=1)
