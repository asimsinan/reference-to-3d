"""dial textures from the front photo, rectified through the front camera onto the dial plane"""
import cv2,numpy as np,json,geom,camlib
p=geom.load();J=json.load(open('cam.json'));g=J['geom'];C,n,u,v=geom.dial_frame(p)
im=cv2.imread('front.jpg')
def rect(size_mm,ppm,h):
    N=int(size_mm*ppm);a=(np.arange(N)+0.5)/ppm-size_mm/2
    X,Y=np.meshgrid(a,-a)          # image x -> +v (phone left = image right when seen from the front), image y down -> -u
    P=C+h*n+X[...,None]*v+Y[...,None]*u
    q=camlib.proj('front',P.reshape(-1,3)).reshape(N,N,2).astype(np.float32)
    return cv2.remap(im,q[...,0],q[...,1],cv2.INTER_CUBIC),X,Y
# number ring
R,X,Y=rect(120,10,0);cv2.imwrite('t_ring_rect.jpg',R)
r=np.hypot(X,Y);ann=(r>41)&(r<53.5)
hsv=cv2.cvtColor(R,cv2.COLOR_BGR2HSV);red=np.median(R[ann&(hsv[...,1]>120)],axis=0);print('ring red BGR',red)
white=(hsv[...,1]<95)&(hsv[...,2]>150)&ann
near=np.zeros_like(white)
for k in range(10):
    ph=g['phi%d'%k];cx,cy=g['Rd']*np.sin(ph),g['Rd']*np.cos(ph);near|=np.hypot(X-cx,Y-cy)<6.5
m=(white&near).astype(np.uint8)
m=cv2.GaussianBlur(m.astype(np.float32),(0,0),0.8)
# dots under the finger holes
dots=np.zeros_like(m)
for k in (5,6,7,8,9,0):
    ph=g['phi%d'%k];cx,cy=31.5*np.sin(ph),31.5*np.cos(ph);dots=np.maximum(dots,np.clip(1.5-(np.hypot(X-cx,Y-cy)-1.4)*10/1,0,1).clip(0,1))
m=np.maximum(m,dots);cv2.imwrite('t_ring_mask.png',(m*255).astype(np.uint8))
wpx=np.median(R[white&near],axis=0);print('digit white BGR',wpx)
# card
Cd,Xc,Yc=rect(44,24,p['hw']+3.0);cv2.imwrite('t_card.png',Cd)
json.dump(dict(ring_red=red[::-1].tolist(),digit_white=wpx[::-1].tolist()),open('tex.json','w'))
v=cv2.resize(R,(600,600));mm=cv2.resize((m*255).astype(np.uint8),(600,600));cc=cv2.resize(Cd,(600,600))
cv2.imwrite('t_view.jpg',np.hstack([v,cv2.cvtColor(mm,cv2.COLOR_GRAY2BGR),cc]))
# logo plate (rear deck) -> normal map; slot interior patch
rear=cv2.imread('rear.jpg')
xs=np.linspace(-65.8,-76.0,10*10+2);ys=np.linspace(18.6,-19.2,38*10)     # rows: up-slope first; cols: +y -> -y (as seen from the rear)
Xg,Yg=np.meshgrid(xs,ys,indexing='ij');Pg=np.stack([Xg,Yg,p['zr0']+p['sr']*Xg],-1)
q=camlib.proj('rear',Pg.reshape(-1,3)).reshape(Xg.shape+(2,)).astype(np.float32)
L=cv2.remap(rear,q[...,0],q[...,1],cv2.INTER_CUBIC);cv2.imwrite('t_logo_rect.png',cv2.resize(L,(0,0),fx=3,fy=3))
g_=cv2.cvtColor(L,cv2.COLOR_BGR2GRAY).astype(np.float32);hp=g_-cv2.GaussianBlur(g_,(0,0),6);hp=cv2.GaussianBlur(hp,(0,0),0.7)
hp=cv2.resize(hp,(0,0),fx=3,fy=3,interpolation=cv2.INTER_CUBIC);hp=np.clip(hp/18,-1,1)
gx=cv2.Sobel(hp,cv2.CV_32F,1,0,ksize=3);gy=cv2.Sobel(hp,cv2.CV_32F,0,1,ksize=3);s_=1.2
nm=np.stack([-gx*s_,gy*s_,np.ones_like(gx)],-1);nm/=np.linalg.norm(nm,axis=2,keepdims=True)
os_=__import__('os');os_.makedirs('gen',exist_ok=True)
cv2.imwrite('gen/logo_normal.png',((nm[...,::-1]*0.5+0.5)*255).astype(np.uint8))
cv2.imwrite('gen/slot.png',cv2.resize(rear[1538:1614,495:541],(0,0),fx=4,fy=4,interpolation=cv2.INTER_CUBIC))
