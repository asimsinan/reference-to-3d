# Detailed props -> scene2.json. Parts: box, tube (p0,p1,r), cylx (door along -X), cone (open/closed), quad (8 verts)
from geo import *
import math
S=json.load(open('scene.json')); R=S['room']; cam=np.array([0,0,R['h']]); Yb=R['Yb']; Xr=R['Xr']
O={o['name']:o for o in S['objs']}
G=[]   # groups: dict(name, parts, mat)
def grp(name,mat='props'): g=dict(name=name,parts=[],mat=mat); G.append(g); return g['parts']
def box(P,x0,x1,y0,y1,z0,z1): P.append(dict(k='box',b=[x0,x1,y0,y1,z0,z1]))
def tube(P,a,b,r,seg=8): P.append(dict(k='tube',a=list(map(float,a)),b=list(map(float,b)),r=r,seg=seg))
def cone(P,x,y,z0,z1,r0,r1,seg=32,top=True,bottom=True,inner=0): P.append(dict(k='cone',c=[x,y],z=[z0,z1],r=[r0,r1],seg=seg,top=top,bottom=bottom,inner=inner))
def door(P,xf,y,z,r,out): # chrome ring + domed glass, protruding towards -X from the face at xf
    P.append(dict(k='cylx',x0=xf,x1=xf-out*0.6,y=y,z=z,r=r,seg=40))
    P.append(dict(k='cylx',x0=xf-out*0.6,x1=xf-out,y=y,z=z,r=r*0.74,seg=40))
D=json.load(open('doors.json'))
# --- washers: separate units with gaps, each with its door
P=grp('Washers')
edges=[3.78,2.982,2.149,1.316,0.483,-0.35,-1.183]
dz=float(np.mean([d['z'] for d in D[6:]])); dr={0:D[6]['r'],1:D[7]['r']}
for i in range(len(edges)-1):
    y1,y0=edges[i],edges[i+1]; box(P,1.60,Xr,y0+0.004,y1-0.004,0,1.347)
    box(P,1.62,Xr,y0+0.004,y1-0.004,1.347,1.36)  # top lid lip
    if i==0 or i>=3: door(P,1.60,(y0+y1)/2+0.018,D[6]['z'],D[6]['r'],0.075)   # units beyond the photo copy W4
    else: door(P,1.60,(y0+y1)/2,dz,D[7]['r'],0.075)
box(P,1.62,Xr,-1.183,3.78,0,0.05)  # plinth
# --- dryers: three stacks of two, doors
P=grp('Dryers')
box(P,1.81,Xr,3.90,Yb,0,2.16)
for d in D[:6]: door(P,1.81,d['y'],d['z'],d['r'],0.05)
# --- table: top, apron, legs
P=grp('Table'); x0,x1,y0,y1,Zt=0.27,0.98,4.24,5.66,0.798
box(P,x0,x1,y0,y1,Zt-0.035,Zt)
for a in [(x0+.02,x0+.045,y0+.02,y1-.02),(x1-.045,x1-.02,y0+.02,y1-.02),(x0+.02,x1-.02,y0+.02,y0+.045),(x0+.02,x1-.02,y1-.045,y1-.02)]:
    box(P,a[0],a[1],a[2],a[3],Zt-0.10,Zt-0.035)
for lx,ly in [(x0+.04,y0+.04),(x1-.04,y0+.04),(x0+.04,y1-.04),(x1-.04,y1-.04)]: box(P,lx-.018,lx+.018,ly-.018,ly+.018,0,Zt-0.035)
# --- wire cart
P=grp('Cart'); cx0,cx1,cy0,cy1=0.495,1.052,3.742,4.170; zt,zm,zb=0.737,0.595,0.41
C=[(cx0,cy0),(cx1,cy0),(cx1,cy1),(cx0,cy1)]
for (x,y) in C:
    tube(P,(x,y,0.075),(x,y,zt),0.009)
    P.append(dict(k='cylx',x0=x+0.012,x1=x-0.012,y=y,z=0.04,r=0.038,seg=16))   # caster wheel
    box(P,x-0.012,x+0.012,y-0.012,y+0.012,0.07,0.09)
for z,r in [(zt,0.006),(zm,0.004),(zb,0.006),(0.13,0.006)]:
    for i in range(4): tube(P,(*C[i],z),(*C[(i+1)%4],z),r)
def bars(a,b,n):
    for t in np.linspace(0,1,n)[1:-1]:
        x=a[0]+(b[0]-a[0])*t; y=a[1]+(b[1]-a[1])*t; tube(P,(x,y,zb),(x,y,zt),0.0028,6)
nx=int((cx1-cx0)/0.035); ny=int((cy1-cy0)/0.035)
bars(C[0],C[1],nx); bars(C[3],C[2],nx); bars(C[0],C[3],ny); bars(C[1],C[2],ny)
for t in np.linspace(0,1,ny)[1:-1]:
    y=cy0+(cy1-cy0)*t; tube(P,(cx0,y,zb),(cx1,y,zb),0.0028,6)
ha,hb=(0.417,3.9,0.933),(0.499,3.9,0.886)          # handle posts' tops, from the photo's two posts
for (x,y,z) in (ha,hb): tube(P,(x,y,zm),(x,y,z),0.008)
tube(P,ha,hb,0.008)
for z in (zt,zm): tube(P,(ha[0],3.9,z),(cx0,3.9,z),0.006)
box(P,0.53,0.95,3.80,4.12,0.412,0.45)               # the washing lying in the basket
# --- bench: slats from the measured profile, end frames
P=grp('Bench'); ys0,ys1=0.2,O['Bench_seat']['b'][3]
sx=lambda t: -0.80+t*(-0.415+0.80)
for a,b in [(0.085,0.21),(0.24,0.365),(0.395,0.52),(0.55,0.68),(0.705,0.84),(0.86,0.985)]:
    box(P,sx(a),sx(b),ys0,ys1,0.415,0.445)
bk=lambda t: (-0.80+t*(-0.052),0.40+t*0.424)
PB=grp('Bench_back')
for a,b in [(0.13,0.24),(0.325,0.435),(0.50,0.625),(0.69,0.82),(0.88,1.0)]:
    (xa,za),(xb,zb_)=bk(a),bk(b); th=0.022
    PB.append(dict(k='quad',v=[[xa,ys0,za],[xa,ys1,za],[xa-th,ys0,za],[xa-th,ys1,za],[xb,ys0,zb_],[xb,ys1,zb_],[xb-th,ys0,zb_],[xb-th,ys1,zb_]]))
for ly in (ys1-0.06,1.25,0.28):
    box(P,sx(0.92),sx(0.98),ly-.02,ly+.02,0,0.415)      # front leg
    box(P,-0.80,-0.76,ly-.02,ly+.02,0,0.415)              # back leg
    box(P,-0.80,sx(0.98),ly-.02,ly+.02,0.37,0.415)        # seat rail
    tube(PB,(-0.79,ly,0.40),(-0.835,ly,0.83),0.016)       # back support
# book and card on the seat (pixel corners on the seat plane)
def flat(name,pix,th):
    Q=[hit(*p,2,0.445,cam) for p in pix]; xs=[q[0] for q in Q]; ys=[q[1] for q in Q]
    box(grp(name),min(xs),max(xs),min(ys),max(ys),0.445,0.445+th)
flat('Book',[(548,785),(640,778),(636,800),(542,806)],0.025)
flat('Card',[(572,840),(604,836),(606,853),(574,857)],0.006)
# --- bucket: open, with inside and a handle
P=grp('Bucket'); bx,by=1.13,3.0
cone(P,bx,by,0,0.34,0.12,0.15,40,top=False,inner=0.006)
box_r=0.15
for t in np.linspace(0,math.pi,13)[:-1]:
    t2=t+math.pi/12; tube(P,(bx+box_r*math.cos(t),by,0.34+0.12*math.sin(t)),(bx+box_r*math.cos(t2),by,0.34+0.12*math.sin(t2)),0.004,6)
# --- stools: seat, 4 splayed legs, foot ring
for nm in ('Stool_L','Stool_R'):
    s=O[nm+'_seat']; x,y=s['c']; zt=s['z'][1]; P=grp(nm)
    cone(P,x,y,zt-0.045,zt,0.15,0.15,32)
    for k in range(4):
        a=math.pi/4+k*math.pi/2; tube(P,(x+0.09*math.cos(a),y+0.09*math.sin(a),zt-0.045),(x+0.13*math.cos(a),y+0.13*math.sin(a),0),0.011)
    ring=[(x+0.118*math.cos(t),y+0.118*math.sin(t),0.12) for t in np.linspace(0,2*math.pi,17)]
    for a,b in zip(ring[:-1],ring[1:]): tube(P,a,b,0.006,6)
# --- the rest as before (single boxes)
for nm in ('Cabinet','SideTable','SideTable_leg0','SideTable_leg1','Basket','AC','Light_near','Light_far'):
    box(grp(nm),*O[nm]['b'])
for nm,yc in (('Light_mid',2.51),('Light_front',0.565)):
    b=O['Light_near']['b']; c0=(b[2]+b[3])/2; box(grp(nm),b[0],b[1],b[2]-c0+yc,b[3]-c0+yc,b[4],b[5])
# plant: a card facing the camera through the pot, cut out by alpha
pot=hit(785,590,2,O['Cabinet']['b'][5],cam)
Pp=np.array([pot[0],pot[1]+0.12,0.78]); n=cam-Pp; n/=np.linalg.norm(n)
V=[]
for px,py in [(738,503),(842,503),(842,627),(738,627)]:
    r=ray(px,py); t=np.dot(Pp-cam,n)/np.dot(r,n); V.append((cam+t*r).tolist())
G.append(dict(name='Plant',mat='plant',parts=[dict(k='poly',v=V)]))
json.dump(dict(room=dict(R,Xr=Xr,Yf=-1.183),groups=G),open('scene2.json','w'))
print(len(G),'groups', sum(len(g['parts']) for g in G),'parts')
