"""Side photo points -> 3D through cam2: the handset's outline on its left-flank plane (y = YF), the grille and
hook buttons on the pocket floor. Writes handset_profile.json. Also writes side_match.jpg (side photo gain-matched
to the front photo's lit beige)."""
from geom import *
import cv2
YF=-60.0
def on_yplane(u,v,y=YF): return cam2.hit_plane(u,v,[0,y,0],[0,1,0])
pts={'top':[(280,592),(400,595),(500,603),(600,615),(700,635),(800,655),(900,672),(1000,705),(1060,725),(1100,745)],
     'back':[(221,630),(221,700)],'front':[(1138,800),(1138,870)],
     'arch':[(440,692),(520,705),(600,720),(680,742),(740,760)],'ear_in_bot':[(470,790)],'mouth_in_bot':[(800,870)],
     'seam':[(225,648),(500,672),(800,735),(1000,790)]}
prof={}
for k,v in pts.items():
    P=np.array([on_yplane(u,vv) for u,vv in v]); prof[k]=P.tolist()
    print(k, ' '.join('(%.0f,%.1f)'%(p[0],p[2]) for p in P))
# pocket floor plane: the top plane lowered 6 mm (perpendicular), rises to the back
nv=np.array([np.sin(AL),0,np.cos(AL)]); P0=np.array([0,0,ztop(0)-6/np.cos(AL)])
for k,(u,v) in {'grille_bl':(500,745),'grille_fl':(540,810),'grille_fr':(820,820),'hook_a':(625,722),'hook_b':(680,748),'rim_mid':(600,815)}.items():
    P=cam2.hit_plane(u,v,P0,nv); print('%-10s x %.1f y %.1f z %.1f'%(k,*P))
json.dump(prof,open('handset_profile.json','w'),indent=1)
a=cv2.imread('ref.jpg').astype(np.float32); b=cv2.imread('side.jpg').astype(np.float32)
ta=a[1350:1430,1000:1080].reshape(-1,3).mean(0)          # lit top beige, front photo
tb=b[850:905,700:900].reshape(-1,3).mean(0)              # lit left wall, side photo (between rim and band)
print('front top bgr',ta.round(1),' side wall bgr',tb.round(1),' gain',(ta/tb).round(3))
cv2.imwrite('side_match.jpg',np.clip(b*(ta/tb)*0.9,0,255).astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,95])   # a little darker: the wall faces the studio key light too
