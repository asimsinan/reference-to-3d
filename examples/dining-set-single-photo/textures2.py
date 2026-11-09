import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
# ---- linen (tileable 1024 px = 6 cm): warp and weft threads, slub noise
N=1024; rng=np.random.default_rng(3); yy,xx=np.mgrid[:N,:N]/N
th=60   # threads per tile
def slub(n):  # per-thread thickness / brightness variation, tileable along the thread
    t=np.zeros(N); 
    for k in range(1,6): t+=rng.normal()/k*np.sin(2*np.pi*(k*np.arange(N)/N+rng.random()))
    return t
warp=np.array([slub(N) for _ in range(th)]); weft=np.array([slub(N) for _ in range(th)])
iw=(xx*th).astype(int)%th; ih=(yy*th).astype(int)%th
fx=(xx*th)%1; fy=(yy*th)%1
over=((iw+ih)%2==0)
hw=np.sin(np.pi*fx)**0.7*(0.85+0.08*warp[iw,(yy*N).astype(int)])
hf=np.sin(np.pi*fy)**0.7*(0.85+0.08*weft[ih,(xx*N).astype(int)])
h=np.where(over,np.maximum(hw,hf*0.8),np.maximum(hf,hw*0.8))
h=h+0.04*rng.normal(size=(N,N)); h=cv2.GaussianBlur(h.astype(np.float32),(0,0),0.8)
col=np.array([152,160,178],np.float32)   # BGR, the cushions' mean colour with the light taken out
fab=col*(0.86+0.22*h[...,None])+rng.normal(0,3,(N,N,1))
cv2.imwrite('tex/linen.png',np.clip(fab,0,255).astype(np.uint8))
dx=cv2.Sobel(h,cv2.CV_32F,1,0)*0.9; dy=cv2.Sobel(h,cv2.CV_32F,0,1)*0.9
n=np.dstack([-dx,dy,np.ones_like(dx)]); n/=np.linalg.norm(n,axis=2,keepdims=True)
cv2.imwrite('tex/linen_n.png',((n[...,::-1]*0.5+0.5)*255).astype(np.uint8))
# ---- the cup's print: "coffee" in a script, black on white; the label wraps the whole cup (u = angle)
LW,LH=4096,1024
lab=Image.new('RGB',(LW,LH),(244,243,240)); d=ImageDraw.Draw(lab)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/SnellRoundhand.ttc',600,index=1)
txt='coffee'; bb=d.textbbox((0,0),txt,font=font); tw=bb[2]-bb[0]; thh=bb[3]-bb[1]
# text centre at u=0.5 (the angle chosen in the build), vertical centre at 55% height
d.text((LW//2-tw//2-bb[0], int(LH*0.42)-thh//2-bb[1]),txt,font=font,fill=(20,18,18))
lab.save('tex/cup_label.png'); print('label text px',tw,thh)
# ---- leaf gradient (u along the leaf: base dark green -> tip light)
g=np.linspace(0,1,256)[None,:,None]
base=np.array([28,58,22]); mid=np.array([40,92,38]); tip=np.array([150,190,120])
leaf=np.where(g<0.75, base+(mid-base)*(g/0.75), mid+(tip-mid)*((g-0.75)/0.25))
leaf=np.repeat(leaf,16,0).astype(np.uint8); Image.fromarray(leaf).save('tex/leaf.png')
