"""Oak whose palette, contrast and band spacing are the photo's: procedural flow (bands ~2 cm apart with cathedral
loops, fine rings inside), coloured by luminance quantiles of the photo's oak (aprons, light divided out)."""
import numpy as np, cv2
Wp,Hp=4096,1760; SZ=(1.40,0.60)   # metres covered
U,V=np.meshgrid(np.arange(Wp)/Wp,np.arange(Hp)/Hp)
def pn(sig_u,sig_v,seed):
    r=np.random.default_rng(seed).normal(size=(Hp,Wp)); fy=np.fft.fftfreq(Hp)[:,None]; fx=np.fft.fftfreq(Wp)[None,:]
    o=np.real(np.fft.ifft2(np.fft.fft2(r)*np.exp(-2*np.pi**2*((fx*sig_u)**2+(fy*sig_v)**2)))); return o/o.std()
px=SZ[1]/Hp*1000   # mm per px across
Kc=int(round(SZ[1]*1000/6.5))                 # lines across (photo apron: ~6-7 mm apart)
warp=2.6*pn(900,300,1)+0.9*pn(220,60,2)+0.35*pn(70,25,9)
cu=(U*int(SZ[0]/0.35)+0.15*pn(1500,700,3))%1
arch=6.0*np.exp(-((cu-0.5)/0.14)**2)*(0.5+0.5*np.sin(2*np.pi*(V*2+0.2*pn(1600,500,4))))
phi=Kc*V+warp+arch
wid=np.random.default_rng(6).uniform(0.12,0.26,5000)[np.floor(phi).astype(int)%5000]
band=np.exp(-((phi%1-0.55)/wid)**2)*np.random.default_rng(5).uniform(0.25,1.0,5000)[np.floor(phi).astype(int)%5000]
fine=np.exp(-(((phi*6)%1-0.6)/0.12)**2)
streak=pn(300,1.0,6); blot=pn(1500,600,7)
mott=pn(160,14,10)
t=0.62*band+0.05*fine+0.10*streak+0.07*blot+0.08*mott           # darkness
# photo palette: delit apron pixels sorted by luminance; t's quantiles -> the same quantiles of the photo
ex=np.vstack([cv2.imread('ex2_oak_0.png').reshape(-1,3),cv2.imread('ex2_oak_1.png').reshape(-1,3)]).astype(np.float32)
ex=ex[ex.sum(1)>30]; lum=ex.mean(1); o=np.argsort(lum); nb=256
pal=np.array([ex[o[int(i*len(o)/nb):int((i+1)*len(o)/nb)]].mean(0) for i in range(nb)])   # dark -> light (BGR)
rank=np.argsort(np.argsort(-t.ravel())).reshape(t.shape)/t.size                          # high darkness -> low quantile
q=np.clip((nb*(0.1+0.8*rank)).astype(int),0,nb-1); col=pal[q]
pores=np.clip((pn(7,0.7,8)-2.0)/0.8,0,1)*(0.4+0.6*(1-band)); col=col*(1-0.22*pores[...,None])
cv2.imwrite('tex/oak_photo.png',np.clip(col,0,255).astype(np.uint8))
h=(0.5*band+0.15*fine+0.3*pores).astype(np.float32); h=cv2.GaussianBlur(h,(0,0),0.8)
dx=cv2.Sobel(h,cv2.CV_32F,1,0)*0.3; dy=cv2.Sobel(h,cv2.CV_32F,0,1)*0.3
n=np.dstack([-dx,dy,np.ones_like(dx)]); n/=np.linalg.norm(n,axis=2,keepdims=True); cv2.imwrite('tex/oak_photo_n.png',((n[...,::-1]*0.5+0.5)*255).astype(np.uint8))
# check: the generated oak at the photo's resolution next to the photo's apron
sm=cv2.resize(col,(int(SZ[0]*1000/1.65),int(SZ[1]*1000/1.65)),interpolation=cv2.INTER_AREA)
e0=cv2.imread('ex2_oak_0.png').astype(np.float32)
print('mm/px %.2f  bands %d  photo mean %s gen mean %s  photo lum std %.1f gen %.1f'%(px,Kc,np.round(e0.reshape(-1,3).mean(0)),np.round(sm.reshape(-1,3).mean(0)),e0.mean(2).std(),sm[:47].mean(2).std()))
W=900; a=cv2.resize(e0,(W,int(e0.shape[0]*W/e0.shape[1]))); b=cv2.resize(sm[:47,:e0.shape[1]],(W,a.shape[0]))
c=cv2.resize(col[:700,:2100],(W,300))
cv2.imwrite('oak2_check.jpg',np.vstack([a,np.full((6,W,3),255),b,np.full((6,W,3),255),c]).astype(np.uint8))
# plate and coasters: the same grain flow, coloured by their own pixels in the photo
img=cv2.imread('ref.jpg').astype(np.float32)
def pal_from(boxes):
    px=np.vstack([img[y0:y1,x0:x1].reshape(-1,3) for (x0,y0,x1,y1) in boxes]); o=np.argsort(px.mean(1))
    return np.array([px[o[int(i*len(o)/nb):int((i+1)*len(o)/nb)]].mean(0) for i in range(nb)])
for name,boxes in {'oak_plate':[(494,333,516,352),(590,334,602,350),(516,346,590,357),(548,328,556,346)],'oak_coaster':[(354,380,402,388),(532,400,584,406)]}.items():
    p=pal_from(boxes); qq=q if name!='oak_plate' else np.clip((nb*(0.12+0.76*rank)).astype(int),0,nb-1); c=p[qq]*(1-0.18*pores[...,None]); cv2.imwrite(f'tex/{name}.png',np.clip(c,0,255).astype(np.uint8))
    print(name,'mean RGB',np.round(c.reshape(-1,3).mean(0)[::-1]))
