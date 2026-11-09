"""Laminate floor tile (tileable): planks 1.22 x 0.205 m staggered, grain coloured by the photo floor's palette."""
import numpy as np, cv2, json
E=json.load(open('env.json'))
img=cv2.imread('ref.jpg').astype(np.float32)
E['colors']['wall']=np.round(img[240:470,895:1000].reshape(-1,3).mean(0)[::-1]).astype(int).tolist(); print('wall',E['colors']['wall'])
json.dump(E,open('env.json','w'),indent=1)
PL,PW=1.22,0.24; MM=2e-3; TU,TV=3*PL,20*PW
Wp,Hp=int(round(TU/MM)),int(round(TV/MM))
U,V=np.meshgrid(np.arange(Wp)/Wp,np.arange(Hp)/Hp)
def pn(sig_u,sig_v,seed):
    r=np.random.default_rng(seed).normal(size=(Hp,Wp)); fy=np.fft.fftfreq(Hp)[:,None]; fx=np.fft.fftfreq(Wp)[None,:]
    o=np.real(np.fft.ifft2(np.fft.fft2(r)*np.exp(-2*np.pi**2*((fx*sig_u)**2+(fy*sig_v)**2)))); return o/o.std()
row=np.floor(V*20).astype(int); rng=np.random.default_rng(3)
off=rng.uniform(0,1,20)                                     # stagger per row
uu=(U*3+off[row])%3; plank=np.floor(uu).astype(int)+row*3  # plank id
pid_off=rng.uniform(0,40,200)[plank]
phi=(V*20*6+1.5*pn(500,40,1)+0.6*pn(120,15,2))+pid_off       # ~6 lines per plank width
wid=rng.uniform(0.15,0.3,4000)[np.floor(phi).astype(int)%4000]
band=np.exp(-((phi%1-0.5)/wid)**2)*rng.uniform(0.3,1,4000)[np.floor(phi).astype(int)%4000]
t=0.45*band+0.25*pn(300,8,4)+0.25*pn(900,60,5)+rng.normal(0,0.10,200)[plank]
pal=np.load('floor_pal.npy'); nb=len(pal)
rank=np.argsort(np.argsort(-t.ravel())).reshape(t.shape)/t.size; col=pal[np.clip((nb*(0.08+0.84*rank)).astype(int),0,nb-1)]   # the middle of the photo's range: its extremes are shading
# joints: thin dark grooves along the rows and at the plank ends
fv=(V*20)%1; fu=uu%1
joint=np.maximum(np.exp(-((np.minimum(fv,1-fv))*PW/0.0011)**2), np.exp(-((np.minimum(fu,1-fu))*PL/0.0011)**2))
col=col*(1-0.45*joint[...,None])
cv2.imwrite('tex/floor.png',np.clip(col,0,255).astype(np.uint8))
h=(0.4*band-1.5*joint).astype(np.float32); h=cv2.GaussianBlur(h,(0,0),0.8)
dx=cv2.Sobel(h,cv2.CV_32F,1,0)*0.3; dy=cv2.Sobel(h,cv2.CV_32F,0,1)*0.3
n=np.dstack([-dx,dy,np.ones_like(dx)]); n/=np.linalg.norm(n,axis=2,keepdims=True); cv2.imwrite('tex/floor_n.png',((n[...,::-1]*0.5+0.5)*255).astype(np.uint8))
cv2.imwrite('floor_check.jpg',cv2.resize(col[:800,:1600],(800,400)).astype(np.uint8)); print('floor tile %.2f x %.2f m'%(TU,TV), col.shape)
