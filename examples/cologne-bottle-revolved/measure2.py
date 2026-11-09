"""Body right edge (dark plastic edge line), left edge (gradient), base lower outline (saturation jump),
collar and cap straight edges from the GrabCut mask. writes obs.json and obs_vis.jpg"""
import cv2,numpy as np,json
im=cv2.imread('photo.jpg'); g=cv2.GaussianBlur(im.astype(np.float32).mean(2),(0,0),1.0)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); S=cv2.GaussianBlur(hsv[...,1].astype(np.float32),(0,0),1.5)
sil=cv2.imread('mask_photo.png',0)>0
vis=im.copy(); obs={}
# left edge: strongest positive gradient (dark table/wall -> bright label) in x 595..630
L=[]
for v in range(950,1545,2):
    w=np.diff(g[v,590:640]); i=np.argmax(w); L.append((590+i+0.5,v))
# right edge: darkest column (the plastic's edge line) in x 930..960
Rr=[]
for v in range(950,1545,2):
    w=g[v,928:962]; i=np.argmin(w); Rr.append((928+i,v))
# base lower outline: last row (scanning down from 1590) where S < table level
Bs=[]
for u in range(615,935,3):
    col=S[1560:1720,u]; tab=np.median(S[1700:1720,u]); 
    low=np.where(col<tab-14)[0]
    if len(low): Bs.append((u,1560+low[-1]+0.5))
# cap and collar edges from the mask
Cap=[];Col=[]
for v in range(475,690,3):
    xs=np.where(sil[v])[0]; Cap+= [(xs[0]-0.5,v,0),(xs[-1]+0.5,v,1)]
for v in range(715,855,3):
    xs=np.where(sil[v])[0]; Col+= [(xs[0]-0.5,v,0),(xs[-1]+0.5,v,1)]
for nm,pts in (('left',L),('right',Rr)):
    pts=np.array(pts,float); keep=np.ones(len(pts),bool)
    for _ in range(3):
        p=np.polyfit(pts[keep,1],pts[keep,0],1); e=pts[:,0]-np.polyval(p,pts[:,1]); keep=np.abs(e)<max(2*np.std(e[keep]),1.0)
    print('%s: x=%.4f*y+%.1f  x(960)=%.1f x(1540)=%.1f  std %.2f  kept %d/%d'%(nm,p[0],p[1],np.polyval(p,960),np.polyval(p,1540),np.std(e[keep]),keep.sum(),len(pts)))
    obs[nm]=pts[keep].tolist()
for nm,pts in (('cap',Cap),('collar',Col)):
    pts=np.array(pts,float)
    for s in (0,1):
        q=pts[pts[:,2]==s]; p=np.polyfit(q[:,1],q[:,0],1); e=q[:,0]-np.polyval(p,q[:,1])
        print('%s side %d: x(%d)=%.1f x(%d)=%.1f std %.2f'%(nm,s,q[0,1],np.polyval(p,q[0,1]),q[-1,1],np.polyval(p,q[-1,1]),np.std(e)))
    obs[nm]=pts.tolist()
Bs=np.array(Bs,float); obs['base']=Bs.tolist()
print('base outline rows by x:',[(int(u),int(v)) for u,v in Bs[::8]])
for nm,c in (('left',(255,0,0)),('right',(255,0,0)),('base',(0,255,0)),('cap',(0,255,255)),('collar',(0,255,255))):
    for p in obs[nm]: cv2.circle(vis,(int(round(p[0])),int(round(p[1]))),1,c,-1)
json.dump(obs,open('obs.json','w'))
cv2.imwrite('obs_vis.jpg',vis[430:1700,560:1020])
