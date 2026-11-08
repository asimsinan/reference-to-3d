from geo import *
import cv2
S=json.load(open('scene.json')); R=S['room']; cam=np.array([0,0,R['h']])
ref=cv2.imread('ref.png')[:,:,::-1].astype(np.float32)/255; plate=cv2.imread('plate.png')[:,:,::-1].astype(np.float32)/255
def lin(c): c=np.asarray(c); return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
T={}
def reg(img,y0,y1,x0,x1): return np.median(img[y0:y1,x0:x1].reshape(-1,3),0)
T['Floor']=reg(ref,800,1000,700,1100); T['Ceiling']=reg(ref,20,120,600,1000)
T['Wall_left_windows']=reg(ref,300,700,100,450); T['Wall_right']=reg(plate,150,440,1560,1700)
T['Wall_back']=reg(ref,350,500,620,760); T['Wall_front']=T['Wall_back']
from hulls import corners
for o in S['objs']:
    P=corners(o)[0]; Q=np.array([proj(p,cam) for p in P]).astype(np.float32)
    m=np.zeros(ref.shape[:2],np.uint8); cv2.fillPoly(m,[cv2.convexHull(Q).astype(np.int32)],1)
    T[o['name']]=np.median(ref[m>0],0) if m.sum()>20 else np.array([.3,.3,.3])
json.dump({k:[float(x) for x in lin(v)] for k,v in T.items()},open('tones.json','w'),indent=0)
print({k:np.round(v*255).astype(int).tolist() for k,v in T.items() if not k.startswith(('Table_leg','Cart_w','Bench_leg'))})
