"""Room around the set, from the photo: wall lines (floor junctions, squared to 90 deg), curtain positions along the
window wall, wall and curtain colours, the floor's palette and plank direction -> env.json + tex/floor.png"""
from geom import *
import cv2, json
img=cv2.imread('ref.jpg').astype(np.float32)
def fl(p): return hit_z(*p,0.0)[:2]
R1=(fl((830,497)),fl((1000,553))); W1=(fl((0,607)),fl((467,533)))
def inter(l1,l2):
    (a,b),(c,d)=l1,l2; M=np.array([b-a,c-d]).T; t=np.linalg.solve(M,c-a); return a+t[0]*(b-a)
corner=inter(R1,W1)
d1=(R1[1]-R1[0]); d1/=np.linalg.norm(d1); d2=(W1[1]-W1[0]); d2/=np.linalg.norm(d2)
a1,a2=np.arctan2(d1[1],d1[0]),np.arctan2(d2[1],d2[0])
# square the corner: rotate both by half the deficit
diff=(a2-a1); defi=(np.pi/2-abs(((diff+np.pi)%(2*np.pi))-np.pi))/2
a1s=a1-np.sign(diff)*defi; a2s=a2+np.sign(diff)*defi
e_r=np.array([np.cos(a1s),np.sin(a1s)]); e_w=np.array([np.cos(a2s),np.sin(a2s)])
# walls run from the corner away: right wall toward -Y side (towards the camera's right), window wall toward +Y
if e_r@(R1[1]-corner)<0: e_r=-e_r
if e_w@(W1[0]-corner)<0: e_w=-e_w
print('corner',np.round(corner,3),'right wall dir',np.round(e_r,3),'window wall dir',np.round(e_w,3),'dot',round(float(e_r@e_w),4))
def along_wall(u,v,origin,e):
    n=np.array([-e[1],e[0],0.0]); P=hit_plane(u,v,n,[origin[0],origin[1],0]); return float((P[:2]-origin)@e), P
# curtain edges along the window wall (image rows 150..250 to stay on the wall)
cur={k:along_wall(x,200,corner,e_w)[0] for k,x in {'brown_r':615,'brown_l':485}.items()}
print('brown curtain along window wall from the corner: %.2f .. %.2f m'%(cur['brown_r'],cur['brown_l']))
# poster's left edge on the right wall (for reference)
col=lambda x0,y0,x1,y1: np.round(img[y0:y1,x0:x1].reshape(-1,3).mean(0)[::-1]).astype(int).tolist()
C={'wall':col(800,330,880,420),'wall_shade':col(690,350,720,420),'curtain_brown':col(520,60,600,240),'sheer':col(40,40,300,300),
   'skirting':col(940,520,990,535)}
print(C)
# floor palette from clean floor pixels (image), light divided out
fm=np.zeros((1000,1000),bool); fm[880:1000,0:150]=True; fm[700:860,290:480]=True; fm[880:1000,820:1000]=True; fm[600:700,560:680]=True
al=cv2.imread('r_id/photo.png',cv2.IMREAD_UNCHANGED)[...,3]>0; fm&=~cv2.dilate(al.astype(np.uint8),np.ones((15,15),np.uint8)).astype(bool)
lum=img.mean(2); low=cv2.GaussianBlur(lum,(0,0),40); dl=img*(lum.mean()/np.maximum(low,1))[...,None]
px=dl[fm]; px=px[(px.mean(1)>40)]
o=np.argsort(px.mean(1)); nb=256; pal=np.array([px[o[int(i*len(o)/nb):int((i+1)*len(o)/nb)]].mean(0) for i in range(nb)])
print('floor mean (RGB)',np.round(px.mean(0)[::-1]))
np.save('floor_pal.npy',pal)
json.dump({'corner':corner.tolist(),'e_r':e_r.tolist(),'e_w':e_w.tolist(),'curtain':cur,'colors':C,'plank_dir_deg':-21.0,'plank_w':0.205,'plank_l':1.22},open('env.json','w'),indent=1)
