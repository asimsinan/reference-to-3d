from geom import *
import cv2
img=cv2.imread('ref.jpg')
PX=6.0  # texels per mm
def warp(surf, wmm, hmm, name):
    Wt,Ht=int(wmm*PX),int(hmm*PX)
    c,r=np.meshgrid(np.arange(Wt)+.5,np.arange(Ht)+.5)
    u=c/Wt; v=1-r/Ht
    P=surf(u.ravel(),v.ravel())
    q=proj(P).astype(np.float32)
    mx=q[:,0].reshape(Ht,Wt); my=q[:,1].reshape(Ht,Wt)
    out=cv2.remap(img,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    cv2.imwrite(f'tex/{name}.png',out); return out,mx,my
import os; os.makedirs('tex',exist_ok=True)
deck=lambda u,v: np.c_[D/2-v*D, -W/2+u*W, np.full_like(u,HB)]
scr =lambda u,v: np.array([HX,0,HB])+np.outer(v*LL,d)+np.c_[0*u,-W/2+u*W,0*u]
frn =lambda u,v: np.c_[np.full_like(u,D/2), -W/2+u*W, v*HB]
out,mx,my=warp(deck,W,D,'deck')
# deck texels hidden behind the lid: image y above the lid's bottom edge line -> replicate the first visible row downward from the back
yl=proj(np.array([lid(8,-W/2),lid(8,W/2)]))   # the lid's visible bottom edge in the image (8 mm up the lid, as in solve.py)
x0,y0=yl[0];x1,y1=yl[1]
lim=y0+(mx-x0)*(y1-y0)/(x1-x0)+4
hidden=my<lim
first=hidden.sum(0)   # per column, rows hidden from top (back)
for cidx in range(out.shape[1]):
    k=min(first[cidx]+4,out.shape[0]-1); out[:k,cidx]=out[k,cidx]
cv2.imwrite('tex/deck.png',out)
sc_,_,_=warp(scr,W,LL,'screen')
# The solved lid is a few px off the photo's outline, so the texture's top and sides carry the wall behind the lid
# (light grey) before the photo's black rim begins. From each edge inwards, everything before the rim -> rim colour.
# First the top edge: the photo's lid top runs from ~19 texels below the texture's top (left) to 0 (right), a few
# px of solve error. Find it per column (first rim texel, darker than the wall behind, also where the wall is dark),
# fit a line, and paint everything above it the rim's colour. Stretching the columns instead moved the screen's
# content off the photo (screen difference 4.2 -> 14.2); painting only thickens the black rim towards the left.
gr=cv2.cvtColor(sc_,cv2.COLOR_BGR2GRAY); H_=sc_.shape[0]
cs=np.arange(100,sc_.shape[1]-100,10)
ks=np.array([np.argmax(gr[:45,c]<25) if (gr[:45,c]<25).any() else np.nan for c in cs],float)
ok=~np.isnan(ks)
b,a=np.polyfit(cs[ok],ks[ok],1)
res=ks[ok]-(a+b*cs[ok]); keep=np.abs(res)<3; b,a=np.polyfit(cs[ok][keep],ks[ok][keep],1)
kc=np.clip(a+b*np.arange(sc_.shape[1]),0,None)
rim0=np.median(np.concatenate([sc_[int(kc[c])+2:int(kc[c])+6,c] for c in range(300,1500,7)]),axis=0)
for c in range(sc_.shape[1]):
    sc_[:int(np.ceil(kc[c]))+1,c]=rim0
print('lid top edge in texture: row %.1f at left -> %.1f at right'%(a,a+b*sc_.shape[1]))
gr=cv2.cvtColor(sc_,cv2.COLOR_BGR2GRAY); M=int(10*PX)        # look up to 10 mm in from the edge
rim=rim0
def clean(line_g, line_c):
    k=np.argmax(line_g[:M]<70)                                  # first rim pixel from the edge
    if line_g[k]<70 and k>0: line_c[:k+2]=rim
for c in range(sc_.shape[1]): clean(gr[:,c], sc_[:,c])
for r in range(sc_.shape[0]):
    clean(gr[r,:], sc_[r,:]); clean(gr[r,::-1], sc_[r,::-1])
cv2.imwrite('tex/screen.png',sc_)
f,_,_=warp(frn,W,HB,'front')
k=int(f.shape[0]*0.7); f[k:]=f[k-1]; cv2.imwrite('tex/front.png',f)   # the table shows under the bevelled bottom edge
print('ok', out.shape)
