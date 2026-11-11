import json, numpy as np
from scipy.optimize import least_squares
import model
from model import ring
model.TH=np.linspace(0,2*np.pi,2880,endpoint=False)
C=json.load(open('cams.json'))
class CC:
    def __init__(s,d): s.pos=np.array(d['pos']); s.R=np.array(d['R']); s.f=d['f']; s.cx=d['cx']; s.cy=d['cy']
    proj=model.Cam.proj
def ext(c,r,z,side):
    p=c.proj(ring(r,z)); j=np.argmin(p[:,0]) if side=='L' else np.argmax(p[:,0]); return p[j]
def inv(k,side,x,y,r0=5,z0=20):
    c=CC(C[k]); s=least_squares(lambda v: ext(c,v[0],v[1],side)-np.array([x,y]),[r0,z0]); return s.x
if __name__=='__main__':
    import sys
    out=[]
    for k,n,excl in [('r4','4',(345,410)),('r3','3',(240,275)),('r2','2',(235,255))]:
        for side in 'LR':
            pts=json.load(open('out/t%s%s.json'%(n,side)))
            for x,y,m in pts[::3]:
                if excl[0]<=y<=excl[1]: continue
                r,z=inv(k,side,x,y); out.append((k,side,y,float(r),float(z)))
    json.dump(out,open('out/cone_rz.json','w'))
    for k in ['r4','r3','r2']:
        for side in 'LR':
            a=[(z,r) for kk,s,y,r,z in out if kk==k and s==side]
            print(k,side,' '.join('%.1f:%.2f'%(z,r) for z,r in a[::4]))
