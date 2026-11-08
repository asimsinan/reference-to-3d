"""The wall's radius r(z) from the photo's silhouette, through the camera (cam.py).
usage: uv run --with opencv-python-headless --with numpy python profile.py     -> wall.json {a, b}: r = a + b z
Rows ROWS must have both edges clean (no handle, no base ring). The silhouette of a surface of revolution is where
the ray grazes it, x_t = r^2/D in front of the axis: iterate r = hw (D - x_t) / F."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, json
from cam import *
ROWS=range(240,399,2)
sil=cv2.imread('mask_photo.png',0)>0
pts=[]
for v in ROWS:
    xs=np.where(sil[v,60:420])[0]+60
    hw=(xs.max()-xs.min()+1)/2; r=hw*D/F
    for _ in range(3):
        xt=r*r/D; r=hw*(D-xt)/F
    pts.append((HC-(v-CY)*(D-xt)/F, r, (xs.max()+xs.min())/2))
pts=np.array(pts)
b,a=np.polyfit(pts[:,0],pts[:,1],1)
print('r = %.4f + %.4f z   (axis column %.1f: use it as CX)'%(a,b,pts[:,2].mean()))
print('max residual %.4f m'%np.abs(pts[:,1]-(a+b*pts[:,0])).max())
json.dump(dict(a=a,b=b),open('wall.json','w'))
