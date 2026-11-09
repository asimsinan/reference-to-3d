"""Measure the body's straight edges in the photo as image lines (brightness steps along scans), -> lines.json."""
import cv2, numpy as np, json
img=cv2.imread('ref.jpg'); g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)
g=cv2.GaussianBlur(g,(0,0),1.5)
def scan(kind,rng,at,sense):
    a,b=rng; pts=[]
    for s in at:
        line=g[a:b,s] if kind=='h' else g[s,a:b]
        d=np.diff(line)
        k=(np.argmin(d) if sense=='dark' else np.argmax(d))+a+0.5
        pts.append((s,k) if kind=='h' else (k,s))
    return np.array(pts,float)
def fit(pts):
    c=pts.mean(0); u,s,vt=np.linalg.svd(pts-c); d=vt[0]; n=np.array([-d[1],d[0]])
    cc=-n@c; res=(pts@n+cc)
    return [float(n[0]),float(n[1]),float(cc)], res
out={}
def add(name,kind,rng,at,sense,pts=None):
    p=scan(kind,rng,at,sense) if pts is None else np.array(pts,float); L,res=fit(p)
    print(f'{name:14s} samples {np.round(p,1).tolist()}\n{"":14s} residuals {np.round(res,1).tolist()}')
    out[name]={'line':L,'pts':p.tolist()}
cols=[560,620,700,800,900,1000,1060]
add('band_top','h',(1480,1530),cols,'dark')
add('band_bot','h',(1500,1545),cols,'light')
add('front_top','h',(1455,1505),cols,'dark')      # top surface (lit) -> front face (darker)
add('floor','h',(1530,1565),cols,'dark')          # bottom lip -> table
add('right_edge','v',(1000,1200),[980,1040,1100,1160,1220,1280,1340,1400],'dark')
add('left_edge',None,None,None,None,pts=[(298,1430),(300,1455),(305,1480)])   # by eye (grid_flc), only 50 px visible
add('back_edge',None,None,None,None,pts=[(700,858),(800,862),(900,866),(1000,870)])  # by eye (grid_back), low contrast
json.dump(out,open('lines.json','w'),indent=1)
vis=img.copy()
for nm,e in out.items():
    for x,y in e['pts']: cv2.circle(vis,(int(x),int(y)),6,(0,0,255),2)
    a,b,c=e['line']
    if abs(b)>abs(a): xs=np.array([200,1400.]); ys=-(a*xs+c)/b
    else: ys=np.array([700,1600.]); xs=-(b*ys+c)/a
    cv2.line(vis,(int(xs[0]),int(ys[0])),(int(xs[1]),int(ys[1])),(0,255,0),1)
cv2.imwrite('lines_vis.jpg',vis[700:1600,200:1300])
