"""Measure the horizontal circles' ellipses on the bottle (label top, yellow band top, label bottom, collar bottom,
cap top, base) and the body's straight edges. Prints fitted ellipses; writes edges_vis.jpg"""
import cv2,numpy as np
im=cv2.imread('photo.jpg').astype(np.float32); H,W=im.shape[:2]
B,G,R=im[...,0],im[...,1],im[...,2]
yel=(R+G)/2-B          # yellowness
gray=(R+G+B)/3
sil=cv2.imread('mask_photo.png',0)>0
vis=cv2.imread('photo.jpg')
def col_edge(chan,x0,x1,y0,y1,sign,blur=3):
    """for each column, the row of the strongest gradient (sign +1: chan increases downward) in rows y0..y1"""
    c=cv2.GaussianBlur(chan,(0,0),blur); pts=[]
    for x in range(x0,x1):
        col=c[y0:y1,x]; d=np.diff(col)*sign; i=np.argmax(d)
        if d[i]>2: pts.append((x,y0+i+0.5))
    return np.array(pts,float)
def fit(pts,name,iters=4):
    keep=np.ones(len(pts),bool)
    for _ in range(iters):
        if keep.sum()<6: break
        e=cv2.fitEllipse(pts[keep].astype(np.float32))
        (cx,cy),(w,h),ang=e
        # distance of each point to ellipse ~ via sampled polygon
        poly=cv2.ellipse2Poly((int(round(cx)),int(round(cy))),(int(round(w/2)),int(round(h/2))),int(round(ang)),0,360,2).astype(float)
        d=np.sqrt(((pts[:,None,:]-poly[None])**2).sum(2)).min(1)
        keep=d<max(2.5*np.median(d[keep]),1.5)
    a,b=max(w,h)/2,min(w,h)/2
    print('%-12s n=%3d/%3d centre (%.1f,%.1f) a %.1f b %.1f b/a %.3f ang %.1f  rows: sides %.1f.. front/back %.1f'%(name,keep.sum(),len(pts),cx,cy,a,b,b/a,ang,cy,cy+b))
    cv2.polylines(vis,[poly.astype(np.int32)],True,(0,0,255),1)
    for p in pts[keep]: cv2.circle(vis,(int(p[0]),int(p[1])),1,(0,255,0),-1)
    return dict(cx=cx,cy=cy,a=a,b=b,pts=pts[keep].tolist())
out={}
out['label_top']=fit(col_edge(yel,640,925,975,1030,+1),'label_top')
out['band_top']=fit(col_edge(yel,640,925,1370,1425,+1),'band_top')
out['label_bot']=fit(col_edge(yel,640,920,1515,1580,-1),'label_bot')
out['collar_bot']=fit(col_edge(gray,690,900,845,900,+1),'collar_bot')
# cap top and base from the mask contour
pts=[]
for x in range(735,885):
    ys=np.where(sil[:,x])[0]; pts.append((x,ys[0]-0.5))
out['cap_top']=fit(np.array(pts,float),'cap_top')
pts=[]
for x in range(620,930):
    ys=np.where(sil[:,x])[0]; pts.append((x,ys[-1]+0.5))
out['base']=fit(np.array(pts,float),'base')
# body straight edges from the mask, rows 1050..1500
L=[];Rr=[]
for v in range(1050,1500,2):
    xs=np.where(sil[v])[0]; L.append((v,xs[0]-0.5)); Rr.append((v,xs[-1]+0.5))
for nm,pts in (('left',L),('right',Rr)):
    pts=np.array(pts,float); keep=np.ones(len(pts),bool)
    for _ in range(3):
        p=np.polyfit(pts[keep,0],pts[keep,1],1); e=pts[:,1]-np.polyval(p,pts[:,0]); keep=np.abs(e)<max(2*np.std(e[keep]),1.0)
    print('%s edge: x = %.4f*y + %.1f  (x at y=900: %.1f, y=1540: %.1f) resid std %.2f n %d'%(nm,p[0],p[1],np.polyval(p,900),np.polyval(p,1540),np.std(e[keep]),keep.sum()))
    out[nm]=p.tolist()
    cv2.line(vis,(int(np.polyval(p,870)),870),(int(np.polyval(p,1560)),1560),(255,0,0),1)
import json; json.dump(out,open('edges.json','w'))
cv2.imwrite('edges_vis.jpg',vis[430:1600,560:1020])
