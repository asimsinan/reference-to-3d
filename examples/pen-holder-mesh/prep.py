"""Textures: contents_tex.png (the photo; where the front mesh wall covers the contents, the wires removed by a
morphological closing so the items behind read their own colours), lattice_tile.png (one cell of the wire lattice,
alpha = wire), tex_info.json. usage: py scripts/prep.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, json
from scipy import ndimage as ndi
from cam import ray, proj, P
im=cv2.imread('photo.jpg'); H,W=im.shape[:2]; sil=cv2.imread('mask_photo.png',0)>0
rw=P['rw']; h=P['h']
# ---- front wall region: pixels whose ray hits the wall cylinder between the rings
ys,xs=np.where(sil); C,d=ray(xs.astype(float),ys.astype(float))
a=d[:,0]**2+d[:,1]**2; b=2*(C[0]*d[:,0]+C[1]*d[:,1]); c=C[0]**2+C[1]**2-rw**2
disc=b*b-4*a*c; ok=disc>0; t=np.where(ok,(-b-np.sqrt(np.maximum(disc,0)))/(2*a),np.nan)
zh=C[2]+t*d[:,2]
wall=np.zeros((H,W),bool); wall[ys[ok&(zh>0.0075)&(zh<h-0.0075)],xs[ok&(zh>0.0075)&(zh<h-0.0075)]]=True
wall=ndi.binary_erosion(wall,iterations=2)
cv2.imwrite('mask_wall.png',wall.astype(np.uint8)*255)
# the wires out: a high percentile over a window the size of a cell keeps the item's own tone (a max filter spread
# every specular line of the silver pens into white)
y0,y1,x0,x1=880,1640,540,1160
un=im.copy(); sub=im[y0:y1,x0:x1]
fp=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(13,13))>0
pf=np.dstack([ndi.percentile_filter(sub[...,c],80,footprint=fp) for c in range(3)])
un[y0:y1,x0:x1]=cv2.GaussianBlur(cv2.medianBlur(pf,5),(0,0),1.0)
# the wires' own tone for the wall's colour: a low percentile (the wire), blurred
wc=im.copy(); pw=np.dstack([ndi.percentile_filter(sub[...,c],15,footprint=fp) for c in range(3)])
wc[y0:y1,x0:x1]=pw; wc=cv2.GaussianBlur(wc,(0,0),5)
idx=ndi.distance_transform_edt(~sil,return_distances=False,return_indices=True); wc=wc[idx[0],idx[1]]
cv2.imwrite('wall_color.png',wc)
wgt=cv2.GaussianBlur(wall.astype(np.float32),(0,0),2)[...,None]
tex=(un.astype(np.float32)*wgt+im.astype(np.float32)*(1-wgt)).astype(np.uint8)
cv2.imwrite('contents_tex.png',tex)
# wire colour: the darkest quarter of the wall pixels
wp=im[wall]; g=wp.mean(1); wire=np.median(wp[g<np.percentile(g,25)],0)[::-1]
if os.environ.get('WIRE_RGB'): wire=np.array([float(x) for x in os.environ['WIRE_RGB'].split(',')])
info=dict(wire_rgb=[int(x) for x in wire])
# ---- lattice tile: rhombic cells a wide, b tall, strands w wide (perpendicular)
A,B,Wd,S=3.0,3.6,float(os.environ.get('WIRE_W','0.62')),0.03   # mm, mm, mm, mm/px (WIRE_W tuned against the photo's wall tones)
nx,ny=int(round(A/S)),int(round(B/S)); X,Y=np.meshgrid((np.arange(nx)+0.5)*S,(np.arange(ny)+0.5)*S)
cosang=A/np.hypot(A,B)      # vertical gap -> perpendicular distance
def fam(sign):
    f=np.mod(Y-sign*(B/A)*X,B); return np.minimum(f,B-f)*cosang
dist=np.minimum(fam(1),fam(-1))
alpha=np.clip((Wd/2-dist)/S+0.5,0,1)          # 1 px anti-aliased edge
# the strands of expanded metal are set at an angle: shade them a little across their width
shade=0.75+0.25*np.clip(1-dist/(Wd/2),0,1)
col=np.array(wire,float)[None,None]*shade[...,None]
tile=np.dstack([col[...,::-1],alpha*255]).astype(np.uint8)
cv2.imwrite('lattice_tile.png',tile)
info.update(cell_a=A/1000,cell_b=B/1000,wire_w=Wd/1000,open_fraction=float(1-alpha.mean()))
json.dump(info,open('tex_info.json','w')); print(info)
vis=im.copy(); vis[wall]=(vis[wall]*0.5+np.array([0,0,255])*0.5).astype(np.uint8)
cv2.imwrite('masks_vis2.jpg',vis[840:1640,540:1160])
cv2.imwrite('contents_tex_crop.jpg',tex[600:1640,540:1160])
# ---- the wall as ONE texture (glTF needs colour and alpha in one image with one UV set): u = angle round the axis
# (seam at the back), v = height between the rings; colour = the wall's photo tone (angle folded at 72 deg), alpha = lattice
TW,TH_=6144,1536
rw_=P['rw']; zb_=P['zb']; e_b=np.arctan2(P['HC'],P['D']); zw0=zb_+0.0024*np.cos(e_b); zw1=P['h']-0.0026
u=(np.arange(TW)+0.5)/TW; phi=u*2*np.pi-np.pi; v=(np.arange(TH_)+0.5)/TH_; z=zw0+v*(zw1-zw0)
Af=np.radians(72); ph=phi.copy(); m_=np.abs(ph)>Af; ph[m_]=np.sign(ph[m_])*Af*(np.pi-np.abs(ph[m_]))/(np.pi-Af)
PH,Z=np.meshgrid(ph,z); X=np.stack([rw_*np.cos(PH),rw_*np.sin(PH),Z],-1).reshape(-1,3)
uv=proj(X).reshape(PH.shape+(2,)).astype(np.float32)
col=cv2.remap(wc,uv[...,0],uv[...,1],cv2.INTER_LINEAR)
NA=int(round(2*np.pi*rw_/(A/1000))); cu=(u*NA*nx).astype(int)%nx; cvv=((z-zw0)/(B/1000)*ny).astype(int)%ny
alp=(alpha*255).astype(np.uint8)[cvv[:,None],cu[None,:]]
cv2.imwrite('wall_tex.png',np.dstack([col[...,:3],alp]))
print('wall_tex.png',TW,TH_,'cells around',NA)
# ---- rim texture: the rings are black; whatever the pens and scissors cover of them in the photo is inpainted
# from the rings' own dark pixels (seen from other angles, the back of the rim carried the pens' pixels)
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
bad=(g>95).astype(np.uint8)*255
rim=cv2.inpaint(im,bad,7,cv2.INPAINT_TELEA)
cv2.imwrite('rim_tex.png',rim)
