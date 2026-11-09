"""textures: tex_body.png (photo, margin filled outward, opening out), tex_inside.png, tex_info.json, valid mask"""
import numpy as np, cv2, json
from scipy import ndimage as ndi
import cam as C
from geom import prof_out, h, RC, TL, ZC
im=cv2.imread('../photo.jpg'); H,W=im.shape[:2]; sil=cv2.imread('mask_raw.png',0)>0
ang=np.linspace(0,2*np.pi,720,endpoint=False)
m=np.zeros((H,W),np.uint8)
for z,r in prof_out():
    cv2.fillPoly(m,[np.round(C.proj(np.stack([r*np.cos(ang),r*np.sin(ang),np.full_like(ang,z)],1))*8).astype(np.int32)],1,shift=3)
body=m>0
ri=RC-TL/2
poly=C.proj(np.stack([ri*np.cos(ang),ri*np.sin(ang),np.full_like(ang,ZC)],1))
op=np.zeros((H,W),np.uint8); cv2.fillPoly(op,[np.round(poly*8).astype(np.int32)],1,shift=3); opening=op>0
def fill_out(img,valid):
    idx=ndi.distance_transform_edt(~valid,return_distances=False,return_indices=True); return img[idx[0],idx[1]]
valid=ndi.binary_erosion(sil&body,iterations=1)&~ndi.binary_dilation(opening,iterations=2)
cv2.imwrite('tex_body.png',fill_out(im,valid)); cv2.imwrite('valid_body.png',valid.astype(np.uint8)*255)
ov=ndi.binary_erosion(opening,iterations=2)
front=np.zeros_like(ov)
for u in range(int(poly[:,0].min())+40,int(poly[:,0].max())-40):
    ys=np.where(ov[:,u])[0]
    if len(ys): front[max(ys.max()-8,0):ys.max()+1,u]=True
med=lambda mm:[int(x) for x in np.median(im[mm],0)[::-1]]
info=dict(inside_rgb=med(front&ov),under_rgb=[205,200,195])
wgt=cv2.GaussianBlur(ndi.binary_erosion(opening,iterations=3).astype(np.float32),(0,0),2)[...,None]
plain=np.array(info['inside_rgb'][::-1],np.float32)[None,None]
cv2.imwrite('tex_inside.png',(fill_out(im,ov).astype(np.float32)*wgt+plain*(1-wgt)).astype(np.uint8))
json.dump(info,open('tex_info.json','w')); print(info, 'valid px',valid.sum())
vis=im.copy(); vis[~valid&sil]=(255,0,255); cv2.drawContours(vis,[np.round(poly).astype(np.int32)],-1,(0,255,0),1)
cv2.imwrite('prep_vis.png',cv2.resize(vis[180:840,100:490],None,fx=1.2,fy=1.2))
