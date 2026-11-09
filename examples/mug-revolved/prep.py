"""Textures and the handle from the photo, the masks and the lathed body's own silhouette.
usage: uv run --with opencv-python-headless --with numpy --with scipy --with scikit-image python prep.py
needs out/body_mask.png (Blender -b -P build.py -- out --body-mask): the handle is the photo's silhouette minus it.
writes tex_body.png (the photo, handle roots and the opening out, margin filled), tex_back.png (dirt specks
inpainted: they would be mirrored onto the back), tex_inside.png (the photo inside the rim's opening, the plain inside
colour outside it, blended), tex_handle.png, tex_info.json, mask_handle.png, handle.json, masks_vis2.jpg.
The handle is a swept tube, not a marching-cubes slab (the slab showed ridges across the handle from the mask's pixel
steps, and weighed 270k vertices): the in-plane shape S is where both faces (x = +-0.7 w/2) project inside the mask
(seen from above the mask holds the arm's upper face too), its skeleton the centre line, its distance transform the
half thickness. S underestimates the thickness (x1.12), the skeleton's tips thin out (hold the value from 3 mm off
the body) and the roots flare (this photo: lower +50 %, upper +30 %). Check the outline from the photo's camera."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, json, math
from scipy import ndimage as ndi
from skimage import measure
import cam as C
from geom import ro, T_RIM, P
im=cv2.imread('photo.jpg'); sil=cv2.imread('mask_photo.png',0)>0
b=cv2.imread('out/body_mask.png',cv2.IMREAD_UNCHANGED)[...,3]>127
H,W=sil.shape; yy,xx=np.mgrid[0:H,0:W]
# ---- handle mask: silhouette right of the body, biggest piece ----
hm=sil&~ndi.binary_dilation(b,iterations=2)&(xx>930)&(yy>1000)&(yy<1600)
hm=ndi.binary_opening(hm,iterations=2); lab,n=ndi.label(hm); hm=lab==(1+np.argmax(ndi.sum(hm,lab,range(1,n+1))))
hm=ndi.binary_fill_holes(ndi.binary_closing(hm,iterations=2))
hroot=hm|(ndi.binary_dilation(hm,iterations=10)&b)        # roots run into the body
cv2.imwrite('mask_handle.png',hm.astype(np.uint8)*255)
def smooth_fill(img,valid):
    """margin filled by normalized Gaussian convolution, finest scale first: no nearest-pixel streaks"""
    out=img.astype(np.float32).copy(); done=valid.copy(); m=valid.astype(np.float32)
    for sg in (2,4,8,16,32,64):
        num=cv2.GaussianBlur(img.astype(np.float32)*m[...,None],(0,0),sg); den=cv2.GaussianBlur(m,(0,0),sg)
        ok=(den>0.02)&~done; out[ok]=num[ok]/den[ok][:,None]; done|=ok
    return np.clip(out,0,255).astype(np.uint8)
def fill_out(img,valid):
    idx=ndi.distance_transform_edt(~valid,return_distances=False,return_indices=True); return img[idx[0],idx[1]]
# ---- opening (inside of the cup) from the inner rim circle ----
h=P['h']; ri=ro(h-0.0025)-T_RIM
a=np.linspace(0,2*np.pi,720); poly=C.proj(np.stack([ri*np.cos(a),ri*np.sin(a),np.full_like(a,h)],1))
opening=np.zeros((H,W),np.uint8); cv2.fillPoly(opening,[np.round(poly).astype(np.int32)],1); opening=opening>0
# ---- body texture: body pixels minus handle roots and the opening ----
hole=ndi.binary_dilation(hm,iterations=4)
valid=sil&b&~hole&~ndi.binary_dilation(opening,iterations=3)
body=fill_out(im,valid); cv2.imwrite('tex_body.png',body)
# back: same, small dark specks (dirt) inpainted so they are not mirrored onto the back
g=cv2.cvtColor(body,cv2.COLOR_BGR2GRAY).astype(float); med=cv2.medianBlur(body,31)
speck=(cv2.cvtColor(med,cv2.COLOR_BGR2GRAY).astype(float)-g>10)&valid
speck=ndi.binary_dilation(speck,iterations=4)
back=cv2.inpaint(body,speck.astype(np.uint8)*255,9,cv2.INPAINT_TELEA); cv2.imwrite('tex_back.png',back)
print('specks px',speck.sum())
# ---- inside ----
ov=ndi.binary_erosion(opening,iterations=2)
# colour near the lowest visible line of the far wall: just above the front inner rim edge
front=np.zeros_like(ov)
for u in range(int(poly[:,0].min())+40,int(poly[:,0].max())-40):
    ys=np.where(ov[:,u])[0]
    if len(ys): front[max(ys.max()-14,0):ys.max()+1,u]=True
def med_rgb(m): return [int(x) for x in np.median(im[m],0)[::-1]]
info=dict(inside_rgb=med_rgb(front&ov),handle_side_rgb=med_rgb(ndi.binary_erosion(hm,iterations=3)),under_rgb=[212,206,196])
json.dump(info,open('tex_info.json','w')); print(info)
# inside texture: the photo inside the opening, the plain inside colour outside it, blended over a few px
wgt=cv2.GaussianBlur(ndi.binary_erosion(opening,iterations=6).astype(np.float32),(0,0),3)[...,None]
plain=np.array(info['inside_rgb'][::-1],np.float32)[None,None]
cv2.imwrite('tex_inside.png',(fill_out(im,ov).astype(np.float32)*wgt+plain*(1-wgt)).astype(np.uint8))
cv2.imwrite('tex_handle.png',smooth_fill(im,ndi.binary_erosion(hm,iterations=5)))   # edge pixels (mixed with the table) out: the side faces read the handle's own colour
# ---- handle slab: in-plane shape S whose front and back faces both project inside the handle mask ----
WID=0.0125; RR=0.006; G=0.0001   # depth along x (a guess), edge rounding, grid step (m)
ys_,xs_=np.where(hroot); pts=C.unproj_plane_x0(xs_.astype(float),ys_.astype(float))
y0,y1=pts[:,1].min()-0.003,pts[:,1].max()+0.003; z0,z1=pts[:,2].min()-0.003,pts[:,2].max()+0.003
Yg,Zg=np.meshgrid(np.arange(y0,y1,G),np.arange(z0,z1,G))
def inmask(x):
    uv=C.proj(np.stack([np.full(Yg.size,x),Yg.ravel(),Zg.ravel()],1))
    u=np.clip(np.round(uv[:,0]).astype(int),0,W-1); v=np.clip(np.round(uv[:,1]).astype(int),0,H-1)
    return hroot[v,u].reshape(Yg.shape)
Sm=inmask(0.0)&inmask(0.7*WID/2)&inmask(-0.7*WID/2)
Sm=ndi.binary_opening(Sm,iterations=2); lab,n=ndi.label(Sm); Sm=lab==(1+np.argmax(ndi.sum(Sm,lab,range(1,n+1))))
Sm=ndi.gaussian_filter(Sm.astype(float),5)>0.5          # smooth outline: the photo's pixel steps made ridges
dist=ndi.distance_transform_edt(Sm)*G
print('max in-plane half thickness %.4f'%dist.max())
# ---- swept tube: the in-plane shape's centre line, its half thickness along it, an oval section ----
from skimage.morphology import skeletonize
sk=skeletonize(Sm); yy_,xx_=np.where(sk); pts2=list(zip(yy_,xx_)); S_=set(pts2)
nb=lambda q:[(q[0]+a,q[1]+b) for a in (-1,0,1) for b in (-1,0,1) if (a or b) and (q[0]+a,q[1]+b) in S_]
def bfs(s):
    prev={s:None}; fr=[s]; last=s
    while fr:
        nf=[]
        for q in fr:
            for r in nb(q):
                if r not in prev: prev[r]=q; nf.append(r); last=r
        fr=nf
    return last,prev
a_,_=bfs(pts2[0]); b_,prev=bfs(a_); path=[b_]
while prev[path[-1]] is not None: path.append(prev[path[-1]])
path=np.array(path,float)                                   # (row=z index, col=y index)
yz=np.stack([y0+path[:,1]*G, z0+path[:,0]*G],1)
th=dist[path[:,0].astype(int),path[:,1].astype(int)]
L=np.r_[0,np.cumsum(np.linalg.norm(np.diff(yz,axis=0),axis=1))]
sN=np.arange(0,L[-1],0.0005); yz=np.stack([np.interp(sN,L,yz[:,0]),np.interp(sN,L,yz[:,1])],1); th=np.interp(sN,L,th)
yz=ndi.gaussian_filter1d(yz,8,axis=0,mode='nearest'); th=ndi.gaussian_filter1d(th,10,mode='nearest')
# the skeleton stops short of the ends by the half thickness: carry each end on along its tangent into the body
def extend(yz,th,first):
    e=yz[0] if first else yz[-1]; t=(yz[0]-yz[6]) if first else (yz[-1]-yz[-7]); t/=np.linalg.norm(t)
    ext=np.array([e+t*k*0.0005 for k in range(1,15)]); te=np.full(len(ext),th[0] if first else th[-1])
    return (np.r_[ext[::-1],yz],np.r_[te,th]) if first else (np.r_[yz,ext],np.r_[th,te])
rb_=np.array([ro(z) for z in yz[:,1]]); out_=np.where(yz[:,0]>rb_+0.003)[0]   # tips of a skeleton thin out: hold the
th[:out_[0]]=th[out_[0]]; th[out_[-1]:]=th[out_[-1]]                            # thickness from 3 mm off the body
# roots flare where they meet the body (the photo's lower root widens; the both-faces cut thins it)
sL=np.r_[0,np.cumsum(np.linalg.norm(np.diff(yz,axis=0),axis=1))]; dA=np.abs(sL-sL[out_[0]]); dB=np.abs(sL-sL[out_[-1]])
th=th*(1.12+0.5*np.exp(-dA/0.007)+0.3*np.exp(-dB/0.006))   # dA: the lower root (path start), dB: the upper
yz,th=extend(yz,th,True); yz,th=extend(yz,th,False)
# keep only what is outside the body by up to 4 mm inside it (the wall is 3.5-4.5 mm)
rad=np.hypot(0,yz[:,0]); rbody=np.array([ro(z) for z in yz[:,1]])
keep=yz[:,0]>rbody-0.0025; yz=yz[keep]; th=th[keep]
NS=40; ang=np.linspace(0,2*np.pi,NS,endpoint=False); EXP=2.6   # superellipse section (a little squarer than oval)
cs=np.sign(np.cos(ang))*np.abs(np.cos(ang))**(2/EXP); sn=np.sign(np.sin(ang))*np.abs(np.sin(ang))**(2/EXP)
V=[];F=[]
tan=np.gradient(yz,axis=0); tan/=np.linalg.norm(tan,axis=1,keepdims=True)
nrm=np.stack([-tan[:,1],tan[:,0]],1)                        # in-plane normal (y,z)
for k in range(len(yz)):
    for a in range(NS):
        x=WID/2*cs[a]; w=th[k]*sn[a]
        V.append([x, yz[k,0]+w*nrm[k,0], yz[k,1]+w*nrm[k,1]])
for k in range(len(yz)-1):
    for a in range(NS):
        b=(a+1)%NS; F.append([k*NS+a,k*NS+b,(k+1)*NS+b,(k+1)*NS+a])
for k,rev in ((0,True),(len(yz)-1,False)):                  # caps (inside the body)
    V.append([0,yz[k,0],yz[k,1]]); c=len(V)-1
    for a in range(NS):
        b=(a+1)%NS; F.append([k*NS+b,k*NS+a,c] if rev else [k*NS+a,k*NS+b,c])
P3=np.array(V)
json.dump(dict(v=P3.tolist(),f=F),open('handle.json','w'))
print('handle tube: %d rings, %d verts, length %.3f m, half thickness %.4f..%.4f'%(len(yz),len(V),L[-1],th.min(),th.max()))
sl=np.zeros((H,W),bool); uv=np.round(C.proj(P3)).astype(int); sl[np.clip(uv[:,1],0,H-1),np.clip(uv[:,0],0,W-1)]=True
print('tube projection inside the handle mask: %.3f'%(hroot[sl].mean()))
vis=im.copy(); vis[hm]=(0,0,255); vis[hroot&~hm]=(0,255,0); vis[sl]=(0,255,255); vis[speck]=(255,0,255)
cv2.drawContours(vis,[np.round(poly).astype(np.int32)],-1,(255,0,0),2)
cv2.imwrite('masks_vis2.jpg',cv2.resize(vis[850:1850,300:1250],None,fx=0.6,fy=0.6))
