import json, numpy as np, cv2, sys
import model
from model import *
from obs import PT, RING, SIL
S=json.load(open('solve.json')); g=S['g']; C=json.load(open('cams.json'))
class CC:
    def __init__(s,d): s.pos=np.array(d['pos']); s.R=np.array(d['R']); s.f=d['f']; s.cx=d['cx']; s.cy=d['cy']
    proj=Cam.proj
tiles=[]
for k in ['r1','r2','r3','r4']:
    im=cv2.imread('ref/%s.png'%k); c=CC(C[k]); sc=2; im=cv2.resize(im,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
    def P(p): return tuple(int(round(v*sc)) for v in p)
    for (r,z,col) in [(g['r_e'],g['z_e'],(255,0,255)),(g['r_b'],g['z_b'],(0,255,255)),(g['r_c'],0,(0,255,0))]:
        pts=c.proj(ring(r,z)); d=np.linalg.norm(ring(r,z)-c.pos,axis=1); front=d<np.median(d)
        for a,b,fr in zip(pts,np.roll(pts,-1,0),front):
            if fr: cv2.line(im,P(a),P(b),col,1)
    for fn,z0,z1 in [(lambda z:(g['z_apex']-z)*g['tana'],g['z_e'],g['z_apex']),(lambda z:g['r_s0']-g['taper']*z,-45,0)]:
        for side in 'LR':
            zs=np.linspace(z0,z1,40); pp=[]
            for z in zs:
                p=c.proj(ring(fn(z),z)); j=np.argmin(p[:,0]) if side=='L' else np.argmax(p[:,0]); pp.append(p[j])
            for a,b in zip(pp[:-1],pp[1:]): cv2.line(im,P(a),P(b),(0,128,255),1)
    for n in ['tip','ball','apex']:
        cv2.circle(im,P(c.proj(np.array([0,0,g['z_'+n]]))[0]),3,(0,0,255),-1)
    # observations
    for n,p in PT.get(k,{}).items(): cv2.drawMarker(im,P(p),(255,255,0),cv2.MARKER_CROSS,8,1)
    for n,(a,b,f) in RING.get(k,{}).items():
        for x in (a,b): cv2.drawMarker(im,P((x,f if f else 0)),(255,255,0),cv2.MARKER_TILTED_CROSS,8,1)
    for part,sd in SIL.get(k,{}).items():
        for side,pts in sd.items():
            for p in pts: cv2.drawMarker(im,P(p),(255,255,0),cv2.MARKER_CROSS,8,1)
    cv2.imwrite('out/ov_%s.png'%k,im)
