"""gainfit.py -- per-photo per-channel affine colour (gain, offset) to the consensus, from texels seen in several photos -> gains.json"""
import cv2, numpy as np, json
objs=['side_lower_L','side_upper_L','dash_F','cab_F','fender_F','roof','bumper_F','solebar_L','headlamp_F','sign_F','glass_cab_F','glass_side_L','bulkhead_F','monitor']
ks=['1','2','3','4','5','6']
C={k:[] for k in ks}; M={k:[] for k in ks}
for o in objs:
    for k in ks:
        t=cv2.imread(f'tex_s{k}/{o}.png').astype(np.float32); s=cv2.imread(f'tex_s{k}/{o}_src.png',0)
        sm=cv2.resize(t,None,fx=0.25,fy=0.25,interpolation=cv2.INTER_AREA); mm=cv2.resize((s>0).astype(np.float32),None,fx=0.25,fy=0.25,interpolation=cv2.INTER_AREA)>0.99
        C[k].append(sm.reshape(-1,3)); M[k].append(mm.ravel())
C={k:np.concatenate(v) for k,v in C.items()}; M={k:np.concatenate(v) for k,v in M.items()}
G={k:np.array([[1.0,0.0]]*3) for k in ks}
for it in range(6):
    A=np.stack([C[k]*G[k][:,0]+G[k][:,1] for k in ks]); W=np.stack([M[k] for k in ks]).astype(float)
    n=W.sum(0); cons=(A*W[...,None]).sum(0)/np.maximum(n,1)[:,None]; use=n>=2
    for i,k in enumerate(ks):
        sel=use&M[k]
        for c in range(3):
            x=C[k][sel,c]; y=cons[sel,c]; g=y.std()/max(x.std(),1e-6)
            G[k][c]=[g, y.mean()-g*x.mean()]
    # fix the overall level: mean gain 1, mean offset 0
    mg=np.mean([G[k][:,0] for k in ks],0); mo=np.mean([G[k][:,1] for k in ks],0)
    for k in ks: G[k][:,0]/=mg; G[k][:,1]=(G[k][:,1]-mo)/mg
for k in ks: print(k,'co-seen',int((M[k]&(np.stack([M[j] for j in ks]).sum(0)>=2)).sum()),'BGR gain',np.round(G[k][:,0],3),'off',np.round(G[k][:,1],1))
json.dump({k:G[k].tolist() for k in ks},open('gains.json','w'))
