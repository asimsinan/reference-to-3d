"""boards34.py -- floor planks and wainscot boards for tram 34, coloured by the photo's own pixels (photo 8):
the pattern (board width, grooves, grain along the board) is generated at the measured spacing, every pixel then takes the
colour of the photo's pixels at the same luminance quantile, so the palette (and mean) are the photo's."""
import cv2, numpy as np
P=cv2.imread('ref2/p8.png')
def palette(boxes):
    px=np.concatenate([P[y0:y1,x0:x1].reshape(-1,3) for x0,y0,x1,y1 in boxes])
    hsv=cv2.cvtColor(px.reshape(-1,1,3),cv2.COLOR_BGR2HSV).reshape(-1,3).astype(np.float32)
    keep=(hsv[:,0]>=5)&(hsv[:,0]<=25)&(hsv[:,1]>90)&(hsv[:,2]>40)        # orange-brown wood only
    px=px[keep].astype(np.float32); print('palette px',keep.sum(),'of',len(keep),'mean BGR',px.mean(0).round())
    L=px.mean(1); o=np.argsort(L); return px[o]
def colour(lum, pal):
    q=np.argsort(np.argsort(lum.ravel()))/(lum.size-1); idx=(q*(len(pal)-1)).astype(int)
    return pal[idx].reshape(lum.shape+(3,))
rs=np.random.RandomState(3)
def boards(W,H,bw,groove,horizontal=True,seed=0):
    """W x H px, boards bw px wide running along x (horizontal) ; returns luminance field"""
    rs=np.random.RandomState(seed); yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    a=xx if horizontal else yy; b=yy if horizontal else xx
    k=(b//bw).astype(int); nb=k.max()+1
    tone=rs.normal(0,0.9 if horizontal else 0.3,nb)[k]
    grain=np.zeros_like(a)
    for f,amp in ((0.9,0.25),(2.3,0.15),(6.0,0.08)):
        ph=rs.uniform(0,6.28,nb)[k]; grain+=amp*np.sin(f*2*np.pi*(b%bw)/bw*3+ph+0.004*a*rs.uniform(0.5,1.5,nb)[k])
    streak=cv2.GaussianBlur(rs.normal(0,1,(H,W)).astype(np.float32),(0,0),sigmaX=(25 if horizontal else 0.8),sigmaY=(0.8 if horizontal else 25))*3
    lum=tone+grain+0.4*streak
    g=(b%bw)<groove; lum[g]-=2.5
    # butt joints along the board every ~ 1.2 m on the floor
    if horizontal:
        off=rs.uniform(0,W,nb)[k]; lum[((a+off)%(W*0.75))<groove]-=1.8
    return lum
# floor: planks along x, 9 cm wide; texture 1.6 m square -> 1024 px (640 px/m) ; photo-8 floor boxes away from seats
pal_f=palette([(520,640,800,852)])
lum=boards(1024,1024,int(0.09*640),3,True,1); cv2.imwrite('tex34m/floor.png',colour(lum,pal_f).astype(np.uint8))
# wainscot: vertical boards 7 cm, texture 0.8 m -> 512 px (640 px/m)
pal_w=palette([(1120,600,1280,700),(0,540,240,660)])
lum=boards(512,512,int(0.07*640),2,False,2); lum=lum*0.45+0.55*cv2.GaussianBlur(lum,(0,0),1); lum=0.45*lum+0.55*cv2.GaussianBlur(lum,(0,0),40); cv2.imwrite('tex34m/wainscot.png',colour(lum,pal_w).astype(np.uint8))
def med(x0,y0,x1,y1): return np.median(P[y0:y1,x0:x1].reshape(-1,3),0)[::-1]
print('leather back',med(470,560,540,640),'post',med(1095,200,1110,500),'ceiling',med(900,40,1000,80),'sash',med(140,380,230,395),'rib',med(470,40,500,55))
cv2.imwrite('g/boards.jpg',np.concatenate([cv2.resize(cv2.imread('tex34m/floor.png'),(512,512)),cv2.imread('tex34m/wainscot.png'),cv2.resize(P[560:850,500:800],(512,512))],1))
