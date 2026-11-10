# stone exemplar from the shaded fort front wall in r5 (clean band without holes) -> tex/stone_tile.png (seamless, ~17 px/m like the photo)
import cv2,numpy as np
def lin(c): return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def srgb(c): return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.maximum(c,1e-9),1/2.4)-0.055)
s=lin(cv2.imread('ref/r5.png').astype(np.float32)/255.)[698:738,515:800]
s=s/cv2.GaussianBlur(s,(0,0),25)          # remove the light falloff, keep the stone pattern (ratio around 1)
P=32; pats=[s[y:y+P,x:x+P] for y in range(0,s.shape[0]-P+1,4) for x in range(0,s.shape[1]-P+1,8)]
rng=np.random.default_rng(7); N=256; acc=np.zeros((N,N,3),np.float32); w=np.zeros((N,N),np.float32); win=np.outer(np.hanning(P),np.hanning(P)).astype(np.float32)+1e-3
for _ in range(900):
    p=pats[rng.integers(len(pats))]; y,x=rng.integers(0,N,2); yy=(np.arange(P)+y)%N; xx=(np.arange(P)+x)%N
    acc[np.ix_(yy,xx)]+=p*win[...,None]; w[np.ix_(yy,xx)]+=win
t=acc/w[...,None]; t=t/np.median(t.reshape(-1,3),0)
np.save('tex/stone_ratio.npy',t.astype(np.float32)); cv2.imwrite('g/stonetile.jpg',(np.clip(srgb(np.clip(t*0.55,0,1)),0,1)*255).astype(np.uint8))
print('stone ratio spread p5/p95',np.round(np.percentile(t.mean(2),[5,95]),2))
