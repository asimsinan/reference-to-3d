"""Side photo (side.jpg, 1200x1600): the left wall's edges as image lines -> slines.json."""
import cv2, numpy as np, json
img=cv2.imread('side.jpg'); g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32); g=cv2.GaussianBlur(g,(0,0),1.5)
def step(kind,a,b,s,sense):
    a,b=int(a),int(b); line=g[a:b,s] if kind=='h' else g[s,a:b]; d=np.diff(line)
    k=(np.argmin(d) if sense=='dark' else np.argmax(d))+a+0.5
    return (s,k) if kind=='h' else (k,s)
def fit(pts):
    pts=np.array(pts,float); c=pts.mean(0); d=np.linalg.svd(pts-c)[2][0]; n=np.array([-d[1],d[0]]); cc=-n@c
    return [float(n[0]),float(n[1]),float(cc)], pts@n+cc, pts
out={}
def add(name,pts):
    L,res,p=fit(pts); print(f'{name:12s} {np.round(p,1).tolist()}\n{"":12s} res {np.round(res,1).tolist()}'); out[name]={'line':L,'pts':p.tolist()}
yc=lambda x: 765+0.31*(x-150)                       # the band's top, roughly
cols=[200,300,400,500,600,700,800,900,1000]
bt=[step('h',yc(x)-25,yc(x)+25,x,'dark') for x in cols]; add('band_top',bt)
bb=[step('h',p[1]+4,p[1]+40,x,'light') for p,x in zip(bt,cols)]; add('band_bot',bb)
hl=lambda x: 92-(x-150)/850*67
fl=[step('h',p[1]+4,p[1]+hl(x)+30,x,'dark') for p,x in zip(bb,cols)]; add('floor',fl)
ro=lambda x: -65-(x-150)/850*65
rim=[step('h',yc(x)+ro(x)-30,yc(x)+ro(x)+25,x,'light') for x in cols]; add('rim',rim)
add('front_corner',[step('v',1080,1180,y,'dark') for y in (930,960,990,1020)])
add('back_corner',[step('v',110,200,y,'light') for y in (715,735,790,820)])
# The automatic scans above caught the coiled cord and the table's seam on the floor and rim lines, and the
# corners are rounded: keep only the clean samples, the corners read on a grid (this photo's numbers).
def refit(k,pts):
    out[k]['pts']=[list(map(float,p)) for p in pts]; out[k]['line'],_,_=fit(pts)
refit('floor',[p for p in out['floor']['pts'] if p[0] not in (200,600)])
refit('rim',[p for p in out['rim']['pts'] if p[0] in (200,300,400,800,1000)])
refit('front_corner',[[1126,940],[1132,980],[1134,1020],[1130,1060]]); refit('back_corner',[[152,715],[151,740],[151,790],[150,840]])
json.dump(out,open('slines.json','w'),indent=1)
vis=img.copy()
for nm,e in out.items():
    for x,y in e['pts']: cv2.circle(vis,(int(x),int(y)),5,(0,0,255),2)
    a,b,c=e['line']
    if abs(b)>abs(a): xs=np.array([100,1200.]); ys=-(a*xs+c)/b
    else: ys=np.array([550,1150.]); xs=-(b*ys+c)/a
    cv2.line(vis,(int(xs[0]),int(ys[0])),(int(xs[1]),int(ys[1])),(0,255,0),1)
cv2.imwrite('slines_vis.jpg',vis[540:1120,100:1200])
