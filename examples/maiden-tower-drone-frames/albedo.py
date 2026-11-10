import os; os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2,numpy as np
def lin(c): return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def srgb(c): return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.maximum(c,1e-9),1/2.4)-0.055)
for n in open('bake/names.txt').read().split():
    ph=lin(cv2.imread('tex/%s_photo.png'%n).astype(np.float32)/255.); Er=cv2.imread('tex/%s_irr.exr'%n,cv2.IMREAD_UNCHANGED); A=Er[...,3]>0.5; E=Er[...,:3].astype(np.float32)
    E=cv2.GaussianBlur(E,(0,0),1.2)
    if n=='rocks': E[:]=1.5
    a=ph/np.maximum(E,0.3); mx=a.max(2,keepdims=True); a=np.clip(a*np.minimum(1.0,0.88/np.maximum(mx,1e-6)),0.015,0.9)
    clip=(ph.min(2)>0.93); a[clip]=np.clip(a[clip],0.78,0.86)
    cv2.imwrite('tex/%s_alb.png'%n,(np.clip(srgb(a),0,1)*255+0.5).astype(np.uint8))
    print(n,'median albedo',np.round(np.median(a[A][:, ::-1],0),2),'E95',np.round(np.percentile(E[A],95),2))
# beacon: white paint + a red band at constant height; colours and band limits measured on the projected albedo
Pm=cv2.imread('bake/beacon_P.exr',cv2.IMREAD_UNCHANGED); A=Pm[...,3]>0.5; Z=Pm[...,0]
S=cv2.imread('tex/beacon_seen.png',0)>40
al=lin(cv2.imread('tex/beacon_alb.png').astype(np.float32)/255.)
red=A&S&(al[...,2]>2.2*al[...,1])&(al[...,2]>0.15)
z0,z1=2.85,3.95   # read on the r4/r5 crops as fractions of the trunk; the projected band is smeared
wcol=np.median(al[A&S&~red&(al.min(2)>0.4)],0); rcol=np.median(al[red],0)
out=np.where(((Z>=z0)&(Z<=z1))[...,None],rcol,wcol); out[~A]=wcol
cv2.imwrite('tex/beacon_alb.png',(np.clip(srgb(out),0,1)*255+0.5).astype(np.uint8))
print('beacon band z %.2f-%.2f white %s red %s'%(z0,z1,np.round(wcol[::-1],3),np.round(rcol[::-1],3)))
# sunlit stone that the photos clipped to white: the stone pattern from the shaded front wall (tex/stone_ratio.npy, ~17 px/m)
# tiled in world space on the wall plane, at the albedo measured on the unclipped sunlit stone (0.66)
T=np.load('tex/stone_ratio.npy'); TP=17.0
for n in ('fort','merlons','shaft'):
    Pm=cv2.imread('bake/%s_P.exr'%n,cv2.IMREAD_UNCHANGED); Nm=cv2.imread('bake/%s_N.exr'%n,cv2.IMREAD_UNCHANGED); A=Pm[...,3]>0.5
    X,Y,Z=Pm[...,2],Pm[...,1],Pm[...,0]; nx,ny=Nm[...,2],Nm[...,1]
    ph=cv2.imread('tex/%s_photo.png'%n).astype(np.float32)/255.; clip=(ph.min(2)>0.93)&A
    clip=cv2.GaussianBlur(clip.astype(np.float32),(0,0),2.0)
    u=np.where(np.abs(nx)>np.abs(ny),Y,X)*TP; v=Z*TP
    ui=np.mod(u,T.shape[1]).astype(np.float32); vi=np.mod(v,T.shape[0]).astype(np.float32)
    pat=cv2.remap(T,ui,vi,cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)
    al=lin(cv2.imread('tex/%s_alb.png'%n).astype(np.float32)/255.)
    base=np.array([0.62,0.63,0.66],np.float32)[::-1]
    out=al*(1-clip[...,None])+np.clip(pat*base,0,0.9)*clip[...,None]
    cv2.imwrite('tex/%s_alb.png'%n,(np.clip(srgb(out),0,1)*255+0.5).astype(np.uint8)); print(n,'clipped texels %.0f%%'%(100*(clip>0.5)[A].mean()))
