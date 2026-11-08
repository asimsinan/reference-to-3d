from geo import *
import cv2
R=json.load(open('room.json')); h=R['h']; cam=np.array([0,0,h]); Yb=R['Yb']; Hc=R['Hc']; Xl=R['Xl']; Xr=2.45
objs=[]
def box(name,x0,x1,y0,y1,z0,z1,kind='box'): objs.append(dict(name=name,kind=kind,b=[x0,x1,y0,y1,z0,z1]))
def cyl(name,x,y,z0,z1,r0,r1=None): objs.append(dict(name=name,kind='cyl',c=[x,y],z=[z0,z1],r=[r0,r1 if r1 else r0]))
# machines
box('Washers',1.60,Xr,-1.0,3.78,0,1.347)
box('Dryers',1.81,Xr,3.90,Yb,0,2.16)
# table
fl=hit(900,844,2,0,cam); fr=hit(1080,836,2,0,cam); Zt=0.798; yb=5.62
x0,x1=0.27,0.98; y0,y1=4.24,5.66
box('Table_top',x0,x1,y0,y1,Zt-0.04,Zt)
for i,(lx,ly) in enumerate([(x0+.04,y0+.04),(x1-.04,y0+.04),(x0+.04,y1-.04),(x1-.04,y1-.04)]):
    box(f'Table_leg{i}',lx-.02,lx+.02,ly-.02,ly+.02,0,Zt-0.04)
# cart
box('Cart',0.47,1.07,3.70,4.22,0.10,0.78)
for i,(lx,ly) in enumerate([(0.50,3.73),(1.05,3.75),(0.49,4.15),(1.05,4.19)]):
    box(f'Cart_wheel{i}',lx-.02,lx+.02,ly-.02,ly+.02,0,0.10)
# bench: seat, backrest (tilted, handled as kind 'tilt'), legs
bf=hit(656,945,2,0,cam)
sx1=bf[0]+0.02; sy1=bf[1]+0.04
box('Bench_seat',-0.80,sx1,0.2,sy1,0.40,0.445)
objs.append(dict(name='Bench_back',kind='tilt',y=[0.2,sy1],bottom=[-0.80,0.40],top=[-0.852,0.824],t=0.03))
for i,ly in enumerate([sy1-0.05,1.2]):
    box(f'Bench_leg{i}a',sx1-0.06,sx1-0.02,ly-0.02,ly+0.02,0,0.40)
    box(f'Bench_leg{i}b',-0.79,-0.75,ly-0.02,ly+0.02,0,0.40)
# bucket
bk=hit(1250,1005,2,0,cam); cyl('Bucket',1.13,3.0,0,0.34,0.12,0.15)
# back props
cf=hit(785,714,2,0,cam); cxa=hit(752,714,2,0,cam)[0]; cxb=hit(818,714,2,0,cam)[0]
ct=hit(785,592,1,cf[1],cam)[2]; print('cabinet',cf,cxa,cxb,ct)
box('Cabinet',cxa,cxb,cf[1],cf[1]+0.45,0,ct)
for nm,(fx,fy),(tx,ty) in [('Stool_L',(740,750),(739,647)),('Stool_R',(855,718),(857,630))]:
    p=hit(fx,fy,2,0,cam); y=p[1]+0.15; zt=hit(tx,ty,1,y,cam)[2]; print(nm,p,zt)
    cyl(nm+'_seat',float(p[0]),y,zt-0.05,zt,0.15)
    cyl(nm+'_leg',float(p[0]),y,0,zt-0.05,0.04)
sl=hit(627,730,2,0,cam); sr=hit(720,725,2,0,cam); st=hit(670,585,1,sl[1],cam)[2]; print('shelf',sl,sr,st)
box('SideTable',sl[0]-0.03,sr[0]+0.03,sl[1],Yb-0.02,st-0.04,st)
for i,lx in enumerate([sl[0],sr[0]]): box(f'SideTable_leg{i}',lx-.015,lx+.015,sl[1],sl[1]+.03,0,st-0.04)
bs=hit(670,585,1,sl[1]+0.05,cam); box('Basket',sl[0],sr[0],sl[1]+0.02,sl[1]+0.4,st,st+0.17)
# AC on back wall
a0=hit(762,343,1,Yb-0.22,cam); a1=hit(908,290,1,Yb-0.22,cam); print('ac',a0,a1)
box('AC',a0[0],a1[0],Yb-0.22,Yb,a0[2],a1[2])
# ceiling lights
for nm,(px,py),(lx,rx),zz in [('Light_near',(1035,183),(838,1240),0.09),('Light_far',(960,262),(830,1095),0.08)]:
    p=hit(px,py,2,Hc-zz,cam); xa=hit(lx,py,1,p[1],cam)[0]; xb=hit(rx,py,1,p[1],cam)[0]
    box(nm,xa,xb,p[1]-0.06,p[1]+0.10,Hc-zz,Hc); print(nm,p,xa,xb)
json.dump(dict(room=dict(h=h,Yb=Yb,Hc=Hc,Xl=Xl,Xr=Xr,Yf=-1.5),objs=objs),open('scene.json','w'),indent=1)
# ---- overlay & prop mask
def corners(o):
    if o['kind']=='box':
        x0,x1,y0,y1,z0,z1=o['b']; y0=max(y0,0.35)
        return [(x,y,z) for x in(x0,x1) for y in(y0,y1) for z in(z0,z1)],None
    if o['kind']=='cyl':
        a=np.linspace(0,2*np.pi,24,endpoint=False); P=[]
        for z,r in zip(o['z'],o['r']): P+= [(o['c'][0]+r*np.cos(t),o['c'][1]+r*np.sin(t),z) for t in a]
        return P,None
    if o['kind']=='tilt':
        y0=max(o['y'][0],0.35); P=[]
        for y in (y0,o['y'][1]):
            for (x,z) in (o['bottom'],o['top']): P+=[(x,y,z),(x-o['t'],y,z)]
        return P,None
im=cv2.imread('ref.png'); ov=im.copy(); mask=np.zeros((H,W),np.uint8)
for o in objs:
    P,_=corners(o); Q=np.array([proj(p,cam) for p in P]).astype(np.float32)
    hull=cv2.convexHull(Q).astype(np.int32)
    cv2.fillPoly(mask,[hull],255); cv2.polylines(ov,[hull],True,(0,255,255),2)
# room edges
for a,b in [((Xl,Yb,0),(Xr,Yb,0)),((Xl,Yb,Hc),(Xr,Yb,Hc)),((Xl,Yb,0),(Xl,Yb,Hc)),((Xr,Yb,0),(Xr,Yb,Hc)),((Xl,1,Hc),(Xl,Yb,Hc)),((Xr,1,Hc),(Xr,Yb,Hc)),((Xl,1,0),(Xl,Yb,0))]:
    p,q=proj(a,cam),proj(b,cam); cv2.line(ov,tuple(int(v) for v in p),tuple(int(v) for v in q),(255,0,255),2)
cv2.imwrite('overlay.png',ov); cv2.imwrite('propmask.png',mask)
