"""Lighting-free colour maps: the photo's local detail (specks, water marks) kept as a ratio to its smooth shading,
put on a flat porcelain white. writes alb_body.png, alb_back.png, alb_inside.png, alb_handle.png
usage: uv run --with opencv-python-headless --with numpy --with scipy python pbr_maps.py
The ratio is trusted only away from the silhouette, the rim's lip and the opening's edge (their shading would come
back as dark rings all round); elsewhere it fades to 1."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv2, numpy as np
from scipy import ndimage as ndi
import cam as C
from geom import ro, T_RIM, P
body=cv2.imread('out/body_mask.png',cv2.IMREAD_UNCHANGED)[...,3]>127
hm=cv2.imread('mask_handle.png',0)>0
h=P['h']; ri=ro(h-0.0025)-T_RIM; a=np.linspace(0,2*np.pi,720)
poly=C.proj(np.stack([ri*np.cos(a),ri*np.sin(a),np.full_like(a,h)],1))
opening=np.zeros(body.shape,np.uint8); cv2.fillPoly(opening,[np.round(poly).astype(np.int32)],1); opening=opening>0
# where the detail is trusted: inside the outline, off the lip's and the edges' shading
KEEP={'body':body&~ndi.binary_dilation(opening,iterations=12),'inside':ndi.binary_erosion(opening,iterations=10),
      'handle':hm}
KEEP={k:cv2.GaussianBlur(ndi.binary_erosion(v,iterations=12).astype(np.float32),(0,0),4)[...,None] for k,v in KEEP.items()}
WHITE=np.array([240,240,236],np.float32)   # BGR: porcelain glaze, a touch cool
for src,dst,sg,lo,k in [('tex_body.png','alb_body.png',18,0.7,'body'),('tex_back.png','alb_back.png',18,0.7,'body'),
                     ('tex_inside.png','alb_inside.png',18,0.85,'inside'),('tex_handle.png','alb_handle.png',18,0.8,'handle')]:
    im=cv2.imread(src).astype(np.float32)+1
    sm=cv2.GaussianBlur(im,(0,0),sg)
    ratio=np.clip(im/sm,lo,1.03)
    lum=ratio.mean(2,keepdims=True); ratio=lum+0.6*(ratio-lum)   # keep a little of the specks' colour
    ratio=1+(ratio-1)*KEEP[k]
    cv2.imwrite(dst,np.clip(WHITE*ratio,0,255).astype(np.uint8))
    print(dst,'min ratio %.2f'%ratio.min())
