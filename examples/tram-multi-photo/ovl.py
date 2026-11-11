"""ovl.py -- wireframe of the solved tram + observed (green) / predicted (red) points on every photo -> g/ov{k}.jpg"""
import json, numpy as np, cv2, sys
sys.argv=['x']; import importlib
from camlib import *
J=json.load(open('cams.json')); m=J['model']; P=json.load(open('pts.json')); G=J.get('G',1.05)
exec(open('solve.py').read().split('def proj')[0].split('P=json.load')[0])  # imports only
def g(k): return m[k]
hw,zs,Xs,Xf,ac,xo,yo,zwd,zws=[m[k] for k in ['hw','zs','Xs','Xf','ac','xo','yo','zwd','zws']]
L=[]
for sx in (1,-1):
  for sy in (1,-1):
    L.append([(sx*Xs,sy*hw,zs),(sx*Xs,sy*hw,zws)])
    L.append([(sx*Xs,sy*hw,zs),(0,sy*hw,zs)]); L.append([(sx*Xs,sy*hw,zws),(0,sy*hw,zws)])
    L.append([(sx*Xf,sy*ac,zwd),(sx*xo,sy*yo,zwd)])
  L.append([(sx*Xf,ac,zwd),(sx*Xf,-ac,zwd)])
  for sy in (1,-1): L.append([(sx*Xf,sy*ac,zwd),(sx*Xf,sy*ac,zs)])
for sy in (1,-1): L.append([(-2,sy*G/2,0),(8,sy*G/2,0)])
names={'HL':(m['xh'],0,m['zh']),'Bm':(m['xb'],-m['yb'],m['zb']),'Bp':(m['xb'],m['yb'],m['zb']),'SLm':(m['xsl'],-m['ysl'],m['zsl']),'SLp':(m['xsl'],m['ysl'],m['zsl']),'K':(m['xk'],0,m['zk']),
 'Dm':(Xf,-ac,zwd),'Dp':(Xf,ac,zwd),'Op':(xo,yo,zwd),'Om':(xo,-yo,zwd)}
for k in J['cams']:
    im=cv2.imread(f'ref/p{k}.png'); side=-1 if k=='5' else 1
    nm=dict(names); nm.update(SFT=(Xs,side*hw,zws),SRT=(-Xs,side*hw,zws),SFB=(Xs,side*hw,zs),SRB=(-Xs,side*hw,zs))
    for a,b in L:
        q=proj(k,np.array([a,b])).astype(int); cv2.line(im,tuple(q[0]),tuple(q[1]),(255,255,0),1,cv2.LINE_AA)
    for n,v in P[k].items():
        o=np.array(v); q=proj(k,np.array(nm[n]))[0]
        cv2.circle(im,tuple(o.astype(int)),4,(0,255,0),1); cv2.circle(im,tuple(q.astype(int)),2,(0,0,255),-1)
        cv2.putText(im,n,tuple((o+5).astype(int)),0,0.35,(0,255,0),1)
    cv2.imwrite(f'g/ov{k}.jpg',im)
