"""Maps for the real-material version (steel.py), in the photo's UV space.
usage: uv run --with opencv-python-headless --with numpy python pbr_maps.py      (after prep.py)
writes logo_mask.png (logo = the clean back plate minus the photo), steel_basecolor.png and steel_roughness.png
(plain steel with the logo as a dark satin print, 4x and smoothed: the photo's logo is ~10 px tall), and
tex_handle_dark.png (the handle photo darkened in linear light, ^1.6). Adjustments go into the images, not into
shader nodes: the glTF exporter drops Gamma and Mix nodes, and the .glb would differ from the .blend."""
import numpy as np, cv2
f=cv2.imread('tex_front.png').astype(float); b=cv2.imread('tex_back.png').astype(float)
LOGO=(250,282,205,256)   # y0,y1,x0,x1 around the logo (this photo)
m=np.clip(((b-f).mean(2)-12)/40,0,1); keep=np.zeros_like(m); y0,y1,x0,x1=LOGO; keep[y0:y1,x0:x1]=1; m*=keep
cv2.imwrite('logo_mask.png',(m*255).astype(np.uint8))
m=cv2.resize(m.astype(np.float32),None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC)
m=np.clip((cv2.GaussianBlur(m,(0,0),1.2)-0.25)/0.5,0,1)
STEEL,INK=220,62                      # sRGB grey of polished stainless (as albedo) and of the print
bc=(STEEL*(1-m)+INK*m).astype(np.uint8); cv2.imwrite('steel_basecolor.png',cv2.merge([bc,bc,bc]))
cv2.imwrite('steel_roughness.png',((0.08*(1-m)+0.45*m)*255).astype(np.uint8))
im=cv2.imread('tex_handle.png').astype(np.float32)/255
lin=np.where(im<=0.04045,im/12.92,((im+0.055)/1.055)**2.4)**1.6
cv2.imwrite('tex_handle_dark.png',(np.where(lin<=0.0031308,lin*12.92,1.055*lin**(1/2.4)-0.055)*255+0.5).astype(np.uint8))
