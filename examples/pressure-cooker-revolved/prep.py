"""Textures and handle meshes from the photo and the masks.
usage: uv run --with opencv-python-headless --with numpy --with scipy --with scikit-image python prep.py
(the first run installs scikit-image: it can take over 2 minutes; run it in the background)
writes  tex_front.png   the photo with the handles inpainted away, margin filled outward (the pot's and lid's texture)
        tex_back.png    the same without the logo (used where the photo's pixels are repeated round the back)
        tex_handle.png  the photo, margin filled from the handles' own pixels
        hmask_<part>.png, handles.json (each handle as a rounded slab: vertices in metres, faces)"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, json
from scipy import ndimage as ndi
from skimage import measure
from cam import *
im=cv2.imread('photo.jpg'); sil=cv2.imread('mask_photo.png',0)>0
yy,xx=np.mgrid[0:H,0:W]
LOGO=(253,278,210,252)                  # y0,y1,x0,x1 of the logo on the photo (this photo)
WIDTH={'right':0.040,'left':0.030,'tab':0.036}   # each handle's thickness along X, m (a guess: the photo is side-on)
BRACKETS={   # light metal brackets that belong to a handle (not dark, so not in its mask): sil & box (this photo)
  'right': (xx>=360)&(xx<=382)&(yy>=183)&(yy<=236),
  'left':  (xx>=70)&(xx<=104)&(yy>=180)&(yy<=236),
  'tab':   (xx>=84)&(xx<=100)&(yy>=176)&(yy<=200)}
OPEN={'tab'}   # parts whose mask caught a thin dark line (the lid's top edge): open it away, keep the biggest piece
hm={}
for nm in WIDTH:
    m=cv2.imread(f'mask_{nm}.png',0)>0
    if nm in OPEN:
        m=ndi.binary_opening(m,structure=np.ones((5,5))); lab,n=ndi.label(m)
        m=lab==(1+int(np.argmax(ndi.sum(m,lab,range(1,n+1)))))
    m|=sil&BRACKETS[nm]
    m=ndi.binary_fill_holes(ndi.binary_closing(m,iterations=2)); hm[nm]=m
    cv2.imwrite(f'hmask_{nm}.png',m.astype(np.uint8)*255)
allh=np.any(list(hm.values()),axis=0)
def fill_out(img,valid):
    idx=ndi.distance_transform_edt(~valid,return_distances=False,return_indices=True)
    return img[idx[0],idx[1]]
# body: handles inpainted where they cross the pot/lid; elsewhere outside the pot is margin, filled outward
hole=ndi.binary_dilation(allh,iterations=3)&sil
body=cv2.inpaint(im,hole.astype(np.uint8)*255,7,cv2.INPAINT_TELEA)
valid=(sil&~hole)|(hole&(xx>100)&(xx<368))   # x range: the pot's and lid's columns (this photo)
valid&=yy<428                                 # below: the floor's shadow, not the pot
body=fill_out(body,valid); cv2.imwrite('tex_front.png',body)
back=body.astype(float); y0,y1,x0,x1=LOGO     # logo out: each column interpolated between the rows around it
t=((np.arange(y0,y1)-y0)/(y1-y0))[:,None,None]
back[y0:y1,x0:x1]=back[y0,x0:x1][None]*(1-t)+back[y1,x0:x1][None]*t
cv2.imwrite('tex_back.png',back.astype(np.uint8))
cv2.imwrite('tex_handle.png',fill_out(im,allh))
# handles: half-thickness h(u,v) rises over r from the outline (a rounded edge), |x| <= h, meshed by marching cubes
S=2; meshes={}
for nm,m in hm.items():
    ys,xs=np.where(m); u0,v0=xs.min()-4,ys.min()-4; u1,v1=xs.max()+5,ys.max()+5
    sub=cv2.resize(m[v0:v1,u0:u1].astype(np.uint8),None,fx=S,fy=S,interpolation=cv2.INTER_LINEAR)>0
    sub=cv2.GaussianBlur(sub.astype(np.float32),(0,0),1.2)>0.5
    dist=ndi.distance_transform_edt(sub)/S*D/F
    w=WIDTH[nm]; r=min(w/2,0.008); s=np.clip(dist/r,0,1)
    h=np.where(sub,np.maximum((w/2-r)+r*np.sqrt(1-(1-s)**2),0.0015),-0.002)
    dx=0.0006; nx=int(np.ceil(w/2/dx))+3; xg=np.arange(-nx,nx+1)*dx
    vol=ndi.gaussian_filter(np.pad(h[None]-np.abs(xg)[:,None,None],1,constant_values=-1),0.7)
    vs,fs,_,_=measure.marching_cubes(vol,0.0); vs-=1
    Y,Z=unproj0(u0-0.5+(vs[:,2]+0.5)/S, v0-0.5+(vs[:,1]+0.5)/S)
    meshes[nm]=dict(v=np.stack([xg[0]+vs[:,0]*dx,Y,Z],1).tolist(),f=fs[:,::-1].tolist())
    print(nm,len(vs),'verts')
json.dump(meshes,open('handles.json','w'))
