"""Lighting-free 360 deg checker albedo from the unwrapped photo (unwrap.png: phi -90..90 at 0.25 deg/px, z from h down
at 0.25 mm/px). 10 columns of 36 deg, a boundary at phi=+11.25 (measured). Each row's two central cells (left A,
right B of that boundary) are the sources: glints inpainted, the photo's shading divided out (cell blurred / its
median), each cell set to its type's median; target columns alternate between the source and its mirror.
writes alb_cyl.png (u: phi -180..180, v: z h..0), gold_mask_cyl.png, alb_info.json"""
import numpy as np, cv2, json
from geom import h
U=cv2.imread('unwrap.png').astype(np.float32); HH=U.shape[0]
X=lambda phi: int(round((phi+90)/0.25))
# rows (unwrap y) and each row's central boundaries [left of A, A|B, right of B] (measured, this photo)
ROWS=[(0,23,'gold'),(23,353,(269,392,564)),(353,407,(248,406,536)),(407,536,(250,403,546)),(536,686,(249,407,546)),
      (686,810,(252,406,557)),(810,924,(258,407,543)),(924,1017,(270,403,572)),(1017,1080,(270,407,543)),
      (1080,1118,'gold'),(1124,HH,(280,402,540))]
cells=[]
for y0,y1,b in ROWS:
    if b=='gold': cells.append(None); continue
    A=U[y0:y1,b[0]+3:b[1]-3].copy(); B=U[y0:y1,b[1]+3:b[2]-3].copy(); cells.append([A,B])
def lum(c): return c.mean(2)
# type of each source: brighter median = white
med=lambda c: np.median(c.reshape(-1,3),0)
types=[]
for c in cells:
    if c is None: types.append(None); continue
    la,lb=lum(c[0]).mean(),lum(c[1]).mean(); types.append(('w','g') if la>lb else ('g','w'))
print('types',types)
def clean(c):
    m=med(c); L=lum(c); Lm=np.median(L)
    base=cv2.GaussianBlur(L,(0,0),25)
    glint=(L>base+4)|(L>Lm+8)
    glint=cv2.dilate(glint.astype(np.uint8),np.ones((7,7),np.uint8))
    c8=np.clip(c,0,255).astype(np.uint8); c8=cv2.inpaint(c8,glint*255,6,cv2.INPAINT_TELEA); c=c8.astype(np.float32)
    c=cv2.medianBlur(c.astype(np.uint8),5).astype(np.float32)
    sh=cv2.GaussianBlur(c,(0,0),18)
    return c/np.maximum(sh,1)*med(c)[None,None]
clean_cells=[None if c is None else [clean(c[0]),clean(c[1])] for c in cells]
allw=np.concatenate([cc[i].reshape(-1,3) for cc,t in zip(clean_cells,types) if cc for i in (0,1) if t[i]=='w'])
allg=np.concatenate([cc[i].reshape(-1,3) for cc,t in zip(clean_cells,types) if cc for i in (0,1) if t[i]=='g'])
MW,MG=np.median(allw,0),np.median(allg,0)
WHITE=np.array([210,227,246],np.float32)   # BGR: cream glaze albedo
GREY=WHITE*(MG/MW)**2.6
print('photo white',MW[::-1],'grey',MG[::-1],'-> albedo grey',GREY[::-1])
WPX=1440; out=np.zeros((HH,WPX,3),np.float32); gold=np.zeros((HH,WPX),np.uint8)
prev_end=None
col_px=lambda phi: int(round((phi+180)/360*WPX))%WPX
for (y0,y1,b),cc,t in zip(ROWS,clean_cells,types):
    if cc is None:
        out[y0:y1]=WHITE; gold[y0:y1]=255; continue
    if prev_end is not None and y0>prev_end: out[prev_end:y0]=WHITE
    prev_end=y1
    for i in range(cc[0].shape[0]): pass
    rng=np.random.default_rng(y0)
    norm=[np.minimum(cc[k]/med(cc[k])[None,None]*GREY[None,None],WHITE[None,None]) if t[k]=='g'
          else WHITE[None,None]+cv2.GaussianBlur(rng.normal(0,1.2,cc[k].shape[:2]).astype(np.float32),(0,0),2)[...,None] for k in (0,1)]
    for k in range(-5,5):
        src=norm[0 if k%2 else 1]
        if (k//2)%2: src=src[:,::-1]
        w=int(round(36/360*WPX)); x0=col_px(11.25+36*k)
        tile=cv2.resize(src,(w,y1-y0),interpolation=cv2.INTER_AREA)
        xs=(np.arange(w)+x0)%WPX; out[y0:y1,xs]=tile
# soften seams between tiles a little across columns
out=np.clip(out,0,255).astype(np.uint8)
cv2.imwrite('alb_cyl.png',out); cv2.imwrite('gold_mask_cyl.png',gold)
json.dump(dict(white_bgr=WHITE.tolist(),grey_bgr=GREY.tolist()),open('alb_info.json','w'))
