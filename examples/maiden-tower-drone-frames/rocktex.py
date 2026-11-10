# rock exemplar from the photos' rock band (r5, r4): patches quilted into a seamless 1024 tile, light divided out -> tex/rock_tile.png
import cv2,numpy as np,json
def lin(c): return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def srgb(c): return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.maximum(c,1e-9),1/2.4)-0.055)
G=json.load(open('gain.json')); pats=[]
for v,(x0,y0,x1,y1) in {'r5':(320,845,880,893),'r4':(560,925,900,975)}.items():
    im=lin(cv2.imread('ref/%s.png'%v).astype(np.float32)/255.)*np.array(G[v]['g'][::-1],np.float32)
    s=im[y0:y1,x0:x1]; s=cv2.resize(s,None,fx=2.4,fy=2.4,interpolation=cv2.INTER_CUBIC)   # ~17 px/m in the photo -> ~40 px/m in the tile
    P=96
    for y in range(0,s.shape[0]-P+1,P//2):
        for x in range(0,s.shape[1]-P+1,P//2):
            p=s[y:y+P,x:x+P]
            if p.mean()>0.03 and (p[...,0]>p[...,2]+0.05).mean()<0.3: pats.append(p)   # skip patches that are mostly sea
rng=np.random.default_rng(4); N=1024; acc=np.zeros((N,N,3),np.float32); w=np.zeros((N,N),np.float32)
win=np.outer(np.hanning(96),np.hanning(96)).astype(np.float32)+1e-3
for _ in range(1400):
    p=pats[rng.integers(len(pats))]; 
    if rng.random()<0.5: p=p[:,::-1]
    y,x=rng.integers(0,N,2); yy=(np.arange(96)+y)%N; xx=(np.arange(96)+x)%N
    acc[np.ix_(yy,xx)]+=p*win[...,None]; w[np.ix_(yy,xx)]+=win
t=acc/w[...,None]
L=json.load(open('light.json')); E=np.array(L['sun'])*0.6/np.pi+0.35          # mean irradiance on the rock slopes (lit + shaded mix)
alb=t/E[::-1]; alb*=0.30/np.median(alb.mean(2))                                  # median albedo of the rocks measured on the projected textures
cv2.imwrite('tex/rock_tile.png',(np.clip(srgb(np.clip(alb,0,0.9)),0,1)*255).astype(np.uint8)); print(len(pats),'patches; albedo median',np.round(np.median(alb.reshape(-1,3),0)[::-1],3))
