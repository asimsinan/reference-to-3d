# Repeatable textures cut from the photo, rectified on their planes. Writes tiles/*.png and tiles.json (world mapping).
from rect import *
import os
os.makedirs('tiles',exist_ok=True)
ref=cv2.imread('ref.png'); plate=cv2.imread('plate.png'); pB=cv2.imread('plate_B.png'); pC=cv2.imread('plate_C.png')
Xl,Hc,Yb,Xr=R['Xl'],R['Hc'],R['Yb'],2.45
def flatten(o,s):
    o=o.astype(np.float32); b=cv2.GaussianBlur(o,(0,0),s); m=o.reshape(-1,3).mean(0)
    return np.clip(o/np.maximum(b,1)*m,0,255)
def calm(o,s,k):
    o=flatten(o,s); m=o.reshape(-1,3).mean(0); return m+k*(o-m)
def fill_magenta(o,axis):
    o=o.astype(np.float32); mag=np.abs(o-np.array([255,0,255])).sum(2)<60
    if axis==1: o=o.transpose(1,0,2); mag=mag.T
    for r in range(o.shape[0]):
        if mag[r].any():
            good=np.where(~mag[r])[0]
            if len(good):
                idx=good[np.abs(good[None,:]-np.arange(o.shape[1])[:,None]).argmin(1)]; o[r,mag[r]]=o[r,idx[mag[r]]]
    return o.transpose(1,0,2) if axis==1 else o
def mirror4(o): return np.vstack([np.hstack([o,o[:,::-1]]),np.hstack([o[::-1],o[::-1,::-1]])])
def seam(o,frac=0.12):
    """make edges wrap: cross-fade the left/right and top/bottom bands with the opposite side"""
    o=o.astype(np.float32); h,w=o.shape[:2]
    for ax,n in ((1,w),(0,h)):
        k=int(n*frac); a=np.linspace(0,1,k)[:, None] if ax==0 else np.linspace(0,1,k)[None,:]
        a=a[...,None]
        if ax==1:
            L=o[:,:k].copy(); Rr=o[:,-k:].copy(); o[:,:k]=L*a+Rr*(1-a)
        else:
            T=o[:k].copy(); B=o[-k:].copy(); o[:k]=T*a+B*(1-a)
    return o
T={}
def save(name,img,mapping): cv2.imwrite(f'tiles/{name}.png',np.clip(img,0,255).astype(np.uint8)); T[name]=mapping
# floor: exactly 2 x 2 tiles, grout to grout (period 0.2875 m)
P=0.2875; gx,gy=-0.13,3.045
o,_=rectify(plate,(gx,gy,0),(1,0,0),(0,1,0),2*P,2*P,600)
save('floor',flatten(o,60),dict(u=[1,0,0],v=[0,1,0],o=[gx,gy,0],su=2*P,sv=2*P))
# ceiling concrete
o,_=rectify(plate,(-0.8,3.1,Hc),(1,0,0),(0,1,0),0.9,1.1,300)
save('ceiling',seam(calm(o,15,0.7)),dict(u=[1,0,0],v=[0,1,0],o=[-0.8,3.1,Hc],su=0.9,sv=1.1))
# wall concrete (right wall above the machines)
o,_=rectify(plate,(Xr,3.3,1.45),(0,1,0),(0,0,1),0.6,0.9,300)
save('wall',seam(calm(o,10,0.55)),dict(u=[0,1,0],v=[0,0,1],o=[Xr,3.3,1.45],su=0.6,sv=0.9))
# window bay (left wall), Y 2.30..3.35; under the bench (Z<0.62) rebuilt from the glass band above, kick plate at the foot
y0,y1=2.30,3.35
o,_=rectify(plate,(Xl,y0,0),(0,1,0),(0,0,1),y1-y0,Hc,300).__getitem__(0),None
o=o[0] if isinstance(o,tuple) else o
o=o.astype(np.float32); H_=o.shape[0]; zrow=lambda z: int(round(H_-z*300))
r62=zrow(0.62); band=o[zrow(1.20):r62]
fill=np.vstack([band[::-1],band])[:H_-r62]
o[r62:]=fill[:H_-r62]
o[zrow(0.10):]=o[zrow(0.10):]*0.35+np.array([40,42,42])*0.65
mag=(np.abs(o-np.array([255,0,255])).sum(2)<30)
for r in range(H_):                       # the beam above is horizontal: fill each row from its first known pixel on the right
    if mag[r].any():
        good=np.where(~mag[r])[0]
        if len(good): o[r,mag[r]]=o[r,good[0]]
save('window',o,dict(u=[0,1,0],v=[0,0,1],o=[Xl,y0,0],su=y1-y0,sv=Hc))
# washer unit W4 (Y 2.982..3.78) from the mid layer (bucket removed)
o,_=rectify(pB,(1.60,2.982,0),(0,1,0),(0,0,1),0.798,1.36,500)
save('washer',o,dict(u=[0,1,0],v=[0,0,1],o=[1.60,2.982,0],su=0.833,sv=1.36))
# bench seat (top, along Y) and backrest (its plane), from the front layer (the photo)
o,_=rectify(ref,(-0.80,1.9,0.445),(1,0,0),(0,1,0),0.385,0.8,600)
save('bench_seat',fill_magenta(o,1),dict(u=[1,0,0],v=[0,1,0],o=[-0.80,1.9,0],su=0.385,sv=0.8))
o,_=rectify(ref,(-0.80,1.9,0.40),(0,1,0),(-0.052/0.427,0,0.424/0.427),0.8,0.427,600)
save('bench_back',fill_magenta(o,0),dict(u=[0,1,0],v=[0,0,1],o=[0,1.9,0.40],su=0.8,sv=0.424))
# light fixture underside
o,_=rectify(ref,(0.128,4.376,Hc-0.09),(1,0,0),(0,1,0),1.441,0.16,400)
save('light',fill_magenta(o,0),dict(u=[1,0,0],v=[0,1,0],o=[0.128,4.376,0],su=1.441,sv=0.16))
json.dump(T,open('tiles.json','w'),indent=1)
sheet=[cv2.resize(cv2.imread(f'tiles/{k}.png'),(300,int(300*cv2.imread(f'tiles/{k}.png').shape[0]/cv2.imread(f'tiles/{k}.png').shape[1]))) for k in T]
Hm=max(s.shape[0] for s in sheet); sheet=[np.vstack([s,np.zeros((Hm-s.shape[0],300,3),np.uint8)]) for s in sheet]
cv2.imwrite('tiles_sheet.jpg',np.hstack(sheet)); print(list(T))
