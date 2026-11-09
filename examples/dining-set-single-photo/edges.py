"""Sample edge points with brightness steps. Usage: edges.py  -> prints samples per edge spec in SPECS."""
import cv2, numpy as np, json, sys
lab=cv2.GaussianBlur(cv2.cvtColor(cv2.imread('ref.jpg'),cv2.COLOR_BGR2LAB).astype(np.float32),(3,3),0)
gx=sum(np.abs(cv2.Sobel(lab[...,i],cv2.CV_32F,1,0)) for i in range(3)); gy=sum(np.abs(cv2.Sobel(lab[...,i],cv2.CV_32F,0,1)) for i in range(3))
def scan(kind, s, a, b, sense):
    line = gy[a:b, s] if kind=='h' else gx[s, a:b]
    k=int(np.argmax(line))
    # subpixel parabola
    if 0<k<len(line)-1:
        l,c_,r=line[k-1],line[k],line[k+1]; dk=0.5*(l-r)/(l-2*c_+r) if (l-2*c_+r)!=0 else 0
    else: dk=0
    return a+k+dk, line[k] if 0<k<len(line)-1 else -1
def run(name, kind, along, center_fn, half, sense):
    out=[]
    for s in along:
        c=center_fn(s); a,b=int(c-half),int(c+half)
        k,st=scan(kind,s,a,b,sense)
        out.append((s,k,st) if kind=='h' else (k,s,st))
    return out
if __name__=='__main__':
    specs=json.load(open(sys.argv[1]))
    res={}
    for nm,sp in specs.items():
        x0,y0,x1,y1=sp['p0']+sp['p1']
        if sp['kind']=='h':
            f=lambda x:y0+(y1-y0)*(x-x0)/(x1-x0); along=range(int(min(x0,x1)),int(max(x0,x1))+1,sp.get('step',8))
        else:
            f=lambda y:x0+(x1-x0)*(y-y0)/(y1-y0); along=range(int(min(y0,y1)),int(max(y0,y1))+1,sp.get('step',8))
        along=[s for s in along if not any(lo<=s<=hi for lo,hi in sp.get('skip',[]))]
        pts=run(nm,sp['kind'],along,f,sp.get('half',8),sp['sense'])
        P=np.array(pts)
        if sp['kind']=='h': m,c=np.polyfit(P[:,0],P[:,1],1); r=P[:,1]-(m*P[:,0]+c)
        else: m,c=np.polyfit(P[:,1],P[:,0],1); r=P[:,0]-(m*P[:,1]+c)
        print(f"{nm}: n={len(P)} slope {m:.4f} rms {np.sqrt((r**2).mean()):.2f} maxres {np.abs(r).max():.1f} minstep {P[:,2].min():.1f}")
        print('   ', ' '.join(f"({p[0]:.0f},{p[1]:.1f})" for p in P))
        res[nm]=P[:,:2].tolist()
    json.dump(res,open(sys.argv[2],'w'),indent=0)
