"""cut34.py -- textures and colours for tram 34's real-material version, all from the photos (ref2)."""
import cv2, numpy as np, json
from fill import synth
I={k:cv2.imread(f'ref2/p{k}.png') for k in ('7','8','9','11','12','13','15','18')}
def warp(k,quad,W,H):
    M=cv2.getPerspectiveTransform(np.float32(quad),np.float32([[0,0],[W,0],[W,H],[0,H]])); return cv2.warpPerspective(I[k],M,(W,H),flags=cv2.INTER_CUBIC)
def lin(c): c=np.asarray(c,float)/255; return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def enc(l): l=np.clip(l,0,1); return np.where(l<=0.0031308,12.92*l,1.055*l**(1/2.4)-0.055)*255
def med(k,x0,y0,x1,y1): return np.median(I[k][y0:y1,x0:x1].reshape(-1,3),0)[::-1]   # RGB
# --- screens (photo 7)
for n,q,W,H in [('disp_main',[(886,804),(1180,804),(1180,1010),(886,1010)],600,440),('disp_cam',[(1262,866),(1462,866),(1462,986),(1262,986)],500,300),
                ('disp_right',[(1622,762),(1890,834),(1866,948),(1616,878)],520,300),('disp_tabL',[(10,440),(145,398),(222,836),(36,882)],300,520),
                ('disp_tabR',[(1800,392),(1990,356),(1990,770),(1760,752)],300,520)]:
    cv2.imwrite(f'tex34m/{n}.png',warp('7',q,W,H))
ct=warp('7',[(520,790),(1530,790),(1960,1130),(300,1130)],1000,560); hm=np.zeros(ct.shape[:2],np.uint8)
hm[470:,:200]=1; hm[440:,800:]=1                       # the driver's hands at the bottom corners
cv2.imwrite('tex34m/console_top.png',cv2.inpaint(ct,hm,9,cv2.INPAINT_TELEA))
# --- floor, wainscot, leather (photo 8), grown into tiles
fl=warp('8',[(573,693),(760,693),(807,851),(527,851)],240,420); cv2.imwrite('g/ex_floor.png',fl)
cv2.imwrite('tex34m/floor.png',np.clip(synth((1024,1024),cv2.rotate(fl,cv2.ROTATE_90_CLOCKWISE).astype(np.float32),block=60,seed=2),0,255).astype(np.uint8))
lam=I['8'][605:675,20:230].astype(np.float32); cv2.imwrite('g/ex_lam.png',lam.astype(np.uint8))
cv2.imwrite('tex34m/wainscot.png',np.clip(synth((512,512),lam,block=40,seed=4),0,255).astype(np.uint8))
lea=I['8'][560:720,270:390].astype(np.float32); cv2.imwrite('g/ex_lea.png',lea.astype(np.uint8))
cv2.imwrite('tex34m/leather.png',np.clip(synth((512,512),lea,block=40,seed=5),0,255).astype(np.uint8))
# --- decals from photo 13 (front dash faces, sign) and photo 11 (logos): white lettering on red, cut square-on
cv2.imwrite('tex34m/dash_side.png',warp('13',[(514,521),(602,518),(600,691),(514,686)],380,740))
cv2.imwrite('tex34m/sign.png',warp('13',[(286,148),(511,148),(511,186),(286,186)],1000,170))
cv2.imwrite('tex34m/signtab.png',warp('13',[(362,104),(432,104),(432,146),(362,146)],300,180))
cv2.imwrite('tex34m/logo_ibb.png',warp('11',[(485,630),(625,655),(622,725),(482,700)],420,200))
cv2.imwrite('tex34m/logo_iett.png',warp('11',[(220,575),(290,588),(288,625),(218,612)],280,150))
# --- colours (RGB 0-255) of lit surfaces; albedo by the white hood = 0.80
C={'red':med('13',330,600,360,640),'white':med('13',290,215,450,232),'maroon':med('13',184,280,191,440),
   'black':med('9',600,500,620,560),'roofgrey':med('15',60,22,110,30),'battery':med('15',60,18,110,24),
   'ceiling':med('8',820,60,900,90),'ribwood':med('8',505,40,520,60),'endwood':med('8',780,540,800,620),'glassdark':med('9',740,360,750,380)}
s=0.80/lin(C['white']).mean()
A={k:[float(x) for x in np.clip(lin(v)*s,0.003,0.9)] for k,v in C.items()}
json.dump({'srgb':{k:[float(x) for x in v] for k,v in C.items()},'albedo':A},open('tex34m/colors.json','w'),indent=1)
for k in C: print(k,np.round(C[k]),np.round(A[k],3))
cv2.imwrite('tex34m/logo_nostalji.png',cv2.resize(I['18'][543:642,357:413],(160,310),interpolation=cv2.INTER_CUBIC))
cv2.imwrite('tex34m/logo_iett18.png',cv2.resize(I['18'][562:622,788:893],(330,180),interpolation=cv2.INTER_CUBIC))
# --- white lettering as RGBA decals (alpha from whiteness: low saturation, bright), so they sit on the one paint
for n in ('logo_ibb','logo_iett','logo_nostalji','logo_iett18'):
    im=cv2.imread(f'tex34m/{n}.png').astype(np.float32); mn=im.min(-1); mx=im.max(-1)
    a=np.clip((mn-70)/(150-70),0,1)*np.clip(1-(mx-mn-60)/80,0,1)
    a=cv2.GaussianBlur(a,(0,0),0.7)
    H,W=a.shape
    if n=='signtab':
        yy,xx=np.mgrid[0:H,0:W]; a*=(((xx/W-0.5)/0.30)**2+((yy/H-0.62)/0.33)**2<1)
    if n=='sign': a[int(0.78*H):]=0; a[:int(0.06*H)]=0; a[:, :int(0.02*W)]=0; a[:, -int(0.02*W):]=0
    if n=='dash_side': a[:int(0.07*H)]=0; a[-int(0.05*H):]=0; a[:, :int(0.07*W)]=0; a[:, -int(0.09*W):]=0
    if n=='dash_side': a[:, :int(0.05*a.shape[1])]=0; a[:, -int(0.04*a.shape[1]):]=0   # the face's own lining strips are geometry
    out=np.dstack([np.full(im.shape[:2],235,np.uint8)]*3+[(a*255).astype(np.uint8)])
    cv2.imwrite(f'tex34m/{n}_a.png',out)
mar=med('12',1070,496,1281,512); print('maroon (photo 12 sill strip)',np.round(mar))
J=json.load(open('tex34m/colors.json')); J['srgb']['maroon']=[float(x) for x in mar]; json.dump(J,open('tex34m/colors.json','w'),indent=1)
