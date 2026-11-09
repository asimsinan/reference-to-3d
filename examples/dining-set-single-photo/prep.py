"""All measured parameters -> scene.json (metres, world frame of cam.json) for the Blender build."""
from geom import *
import json
from scipy.optimize import least_squares
CU=json.load(open('cush.json')); TR=json.load(open('tray.json')); SP=json.load(open('splay.json')); MI=json.load(open('misc.json'))
AP=json.load(open('apron.json'))
S={'cam':dict(R=R.tolist(),C=CAM.tolist(),f=F,cx=CX,cy=CY,w=1000,h=1000)}
# ---- table
S['table']=dict(L=L,W=W,T=T,H=H,rc=0.055,seam_y=-0.008,seam_gap=0.0012,
    legs=[[sx*C_['bx'],sy*C_['by']] for sx,sy in ((-1,1),(-1,-1),(1,-1),(1,1))],leg_r_top=0.028,leg_r_bot=0.026,
    apron_zb=0.644,short_apron_x=L/2-0.017,short_apron_half=0.214,long_apron_y=W/2-0.019,long_apron_half=C_['bx']-0.0275,apron_t=0.02,
    slots=[[-0.43,-1],[0.43,-1],[-0.43,1],[0.43,1]])
# ---- seats: frame centre (cushion centre + leg-frame offset), yaw, cushion and tray, legs (top in seat frame, feet on the floor)
zb=TR['zb']; TW=TR['TW']
FEET={'S1':[(598,903),(795,953),(846,830),(683,793)],'S2':[(700,776),(856,815),(904,728),None],'bench':[(95,766),(225,802),(451,623),(338,607)]}
SIG=[(-1,1),(-1,-1),(1,-1),(1,1)]
seats={}
for nm,kind in (('S1','stool'),('S2','stool'),('bench','bench')):
    cx,cy,th,a,b,rc,zr,zt=CU[nm]; sp=SP[kind]
    c,s=np.cos(th),np.sin(th); W_=lambda x,y: [cx+c*x-s*y, cy+s*x+c*y]
    off=sp['off'][nm]; legs=[]
    for i,(sx,sy) in enumerate(SIG):
        top=W_(sx*sp['ux']+off[0],sy*sp['uy']+off[1])+[zb]
        if FEET[nm][i] is not None:
            u,v=FEET[nm][i]; foot=hit_z(u,v-2,0.0)[:2].tolist()
        else:
            foot=W_(sx*sp['fx']+off[0],sy*sp['fy']+off[1])
        legs.append(dict(top=top,foot=foot+[0.0]))
    seats[nm]=dict(cx=cx,cy=cy,th=th,a=a,b=b,rc=rc,zr=zr,zt=zt,tray_zb=zb,tray_zt=TR['zrt'],TW=TW,
                   leg_r_top=0.0225 if kind=='stool' else 0.020,leg_r_bot=0.0095 if kind=='stool' else 0.010,legs=legs)
S['seats']=seats
# ---- tabletop objects
ZC=H+0.007   # coaster top
def cyl(base, top, z0=H, r0=(0.03,0.035,0.06)):
    def res(p):
        X,Y,rb,rt,h=p; c=np.array([X,Y,z0]); v=CAM-c; v[2]=0; v/=np.linalg.norm(v); side=np.cross([0,0,1],v); out=[]
        for dz,r,(l,rr,vv) in ((0,rb,base),(h,rt,top)):
            q=proj(np.array([c+[0,0,dz]+r*side, c+[0,0,dz]-r*side, c+[0,0,dz]+r*v])); out+=[min(q[:2,0])-l, max(q[:2,0])-rr, q[2,1]-vv]
        return np.array(out)
    P0=hit_z((base[0]+base[1])/2,base[2],z0); r=least_squares(res,[P0[0],P0[1],*r0]); return r.x.tolist()
O={}
O['cup1']=dict(zip('X Y rb rt h'.split(),cyl((362,387,376),(355,391,341.5),ZC)))
O['cup2']=dict(zip('X Y rb rt h'.split(),cyl((545,575,397.5),(540.5,580,362),ZC)))
for k in ('cup1','cup2'): O[k]['z']=ZC
# the cups stand on their coasters: each coaster's main disc is centred under its cup (the photo: same image x; depth is
# the uncertain direction, ~1 cm per pixel here, and the cup's base edge is the sharper reading)
O['coaster1']=dict(zip('X Y z'.split(),hit_z(373,379,ZC).tolist())); O['coaster2']=dict(zip('X Y z'.split(),hit_z(553,398.5,ZC).tolist()))
O['candle']=dict(zip('X Y rb rt h'.split(),cyl((621.5,659,333),(621.5,659,305))))
O['plate']=dict(zip('X Y rb rt h'.split(),cyl((503,590,356),(493,601,350),H,(0.08,0.1,0.015))))
# muffins sit on the plate's floor (~7 mm above the table): their dome tops at y 319/318, centres x 531/573.5, ~33 px wide
for k,(u,vt,wpx) in {'muffin1':(531.5,319,33),'muffin2':(573.5,318,33)}.items():
    def res(p):
        X,Y=p; c=np.array([X,Y,H+0.007+0.056]); q=proj(c[None])[0]; return [q[0]-u, q[1]-vt]
    r=least_squares(res,[0.15,0.05]); X,Y=r.x; dep=(np.array([X,Y,H+0.04])-CAM)@R[2]
    O[k]=dict(X=X,Y=Y,z=H+0.007,r=wpx/2*dep/F)
u,v,rp=594.5,304.0,24.5
def rs(p):
    d,Rr=p; o,dd=ray(u,v); Cc=o+d*dd; return [Cc[2]-(H+Rr), Rr*F/((Cc-CAM)@R[2])-rp]
s=least_squares(rs,[2.8,0.05]); o,dd=ray(u,v); Cs=o+s.x[0]*dd; O['sphere']=dict(X=Cs[0],Y=Cs[1],R=s.x[1])
o,dd=ray(629,296); P=o+(3.1/(dd@R[2]))*dd; O['pot']=dict(X=P[0],Y=P[1],h=P[2]-H,r=15*3.1/F)
O['plant_top']=float(H+O['pot']['h']+41*3.1/F)
# the camera's left in the world (a cup's handle seen on the image's left), and away from the camera
O['img_left']=(-R[0][:2]/np.linalg.norm(R[0][:2])).tolist(); O['img_away']=(R[2][:2]/np.linalg.norm(R[2][:2])).tolist()
for k,c in (('coaster1','cup1'),('coaster2','cup2')):
    cu=np.array([O[c]['X'],O[c]['Y']]); co=np.array([O[k]['X'],O[k]['Y']]); d=co-cu
    O[k]['X'],O[k]['Y']=(cu+0.6*d).tolist(); O[c]['X'],O[c]['Y']=(cu+0.2*d).tolist(); O[k]['R0']=0.046
S['objects']=O
json.dump(S,open('scene.json','w'),indent=1)
for k,v in O.items(): print(k, {a:(round(b,4) if isinstance(b,float) else b) for a,b in v.items()} if isinstance(v,dict) else v)
for k,v in seats.items(): print(k,'feet',[np.round(l['foot'][:2],3).tolist() for l in v['legs']])
# the napkin: the white paper right of the second muffin (image 593,338) on the plate's floor
S['objects']['napkin']=hit_z(593,339,H+0.009)[:2].tolist()
json.dump(S,open('scene.json','w'),indent=1); print('napkin',S['objects']['napkin'])
