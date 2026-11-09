"""Overlay the solved circles (rim top, ring bottom, base) and the edge points on the photo -> cam_vis.jpg"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, json
from cam import proj, P
im=cv2.imread('photo.jpg'); E=json.load(open('edges.json'))
ang=np.linspace(0,2*np.pi,720)
def draw(z,r,col):
    uv=np.round(proj(np.stack([r*np.cos(ang),r*np.sin(ang),np.full_like(ang,z)],1))).astype(np.int32)
    cv2.polylines(im,[uv],True,col,2)
draw(P['h'],P['R'],(0,255,0)); draw(P['h']-P['t'],P['R'],(0,255,255)); draw(P['zb'],P['rb'],(255,255,0))
for k,col in (('top',(0,128,0)),('ringbot',(0,128,255)),('base',(255,0,0))):
    for u,v in E[k]: cv2.circle(im,(int(u),int(v)),3,col,-1)
cv2.imwrite('cam_vis.jpg',im[840:1640,540:1160])
