"""Blender: build the rotary phone from geom.py + params.json + cam.json, render photo-camera and beauty shots, save .blend/.glb
Blender -b -P build.py -- --out DIR --shots front,side,rear,q1 [--res 1000] [--samples 96] [--blend f] [--glb f]"""
import bpy,bmesh,sys,os,json,math
import numpy as np
from mathutils import Matrix,Vector
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
import geom
A=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
def arg(k,d=None): return A[A.index(k)+1] if k in A else d
OUT=arg('--out','r');SHOTS=[s for s in arg('--shots','').split(',') if s];RES=int(arg('--res','1000'));SAMPLES=int(arg('--samples','96'))
p=geom.load();J=json.load(open(os.path.join(HERE,'cam.json')));G=J['geom'];TX=json.load(open(os.path.join(HERE,'tex.json')))
MM=0.001
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene
col_model=bpy.data.collections.new('telefon');S.collection.children.link(col_model)
col_studio=bpy.data.collections.new('studio');S.collection.children.link(col_studio)
root=bpy.data.objects.new('Telefon',None);col_model.objects.link(root)
def srgb2lin(c): c=np.asarray(c,float)/255;return np.where(c<0.04045,c/12.92,((c+0.055)/1.055)**2.4)
# ---------- materials
M=json.load(open(os.path.join(HERE,'mat.json'))) if os.path.exists(os.path.join(HERE,'mat.json')) else {}
RED=M.get('red',[0.16,0.008,0.014]);ROUGH=M.get('rough',0.18)
def principled(name,base,rough=0.5,metal=0.0,trans=0.0,ior=1.5,spec=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=(*base,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    b.inputs['Transmission Weight'].default_value=trans;b.inputs['IOR'].default_value=ior
    return m
def teximg(name,arr,colorspace='sRGB'):
    """arr HxWx3 or HxW float 0..1 (top row first)"""
    arr=np.asarray(arr,np.float32)
    if arr.ndim==2: arr=np.repeat(arr[...,None],3,2)
    h,w=arr.shape[:2];im=bpy.data.images.new(name,w,h,alpha=False);px=np.ones((h,w,4),np.float32);px[...,:3]=arr[::-1]
    im.pixels.foreach_set(px.ravel());im.colorspace_settings.name=colorspace
    os.makedirs(os.path.join(HERE,'gen'),exist_ok=True);im.filepath_raw=os.path.join(HERE,'gen',name+'.png');im.file_format='PNG';im.save();im.pack();return im
def loadpx(fn):
    im=bpy.data.images.load(os.path.join(HERE,fn));w,h=im.size;a=np.empty(w*h*4,np.float32);im.pixels.foreach_get(a)
    a=a.reshape(h,w,4)[::-1,:,:3];bpy.data.images.remove(im);return a      # display-referred values as stored (sRGB 0..1)
def texmat(name,img,rough,bump=None,bump_strength=0.3):
    m=principled(name,(1,1,1),rough);nt=m.node_tree;b=nt.nodes['Principled BSDF']
    t=nt.nodes.new('ShaderNodeTexImage');t.image=img;t.extension='EXTEND';nt.links.new(t.outputs['Color'],b.inputs['Base Color'])
    return m
m_red=principled('kirmizi_plastik',RED,ROUGH)
m_clear=principled('seffaf_plastik',(1,1,1),0.06,trans=1.0,ior=1.49)
m_metal=principled('metal',(0.55,0.57,0.58),0.38,metal=1.0)
m_foot=principled('ayak_lastik',M.get('foot',[0.035,0.02,0.016]),0.6)
m_dark=principled('ic_karanlik',(0.01,0.004,0.004),0.7)
m_cordred=principled('kordon',M.get('cord',RED),0.3)
def loadimg(fn):
    im=bpy.data.images.load(os.path.join(HERE,'gen',fn));im.pack();return im
m_ring=texmat('kadran_halkasi',loadimg('kadran_albedo.png'),ROUGH)
m_card=texmat('kart',loadimg('kart_albedo.png'),0.55)
# ---------- helpers
def mk(name,V,F,mat,smooth=True,parent=root):
    me=bpy.data.meshes.new(name);me.from_pydata([tuple(v) for v in np.asarray(V)*MM],[],[tuple(int(i) for i in f) for f in F]);me.update()
    o=bpy.data.objects.new(name,me);col_model.objects.link(o);o.parent=parent
    if mat: me.materials.append(mat)
    if smooth:
        for poly in me.polygons: poly.use_smooth=True
    return o
def act(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def apply_mod(o,m):
    act(o);bpy.ops.object.modifier_apply(modifier=m.name)
def boolean(o,cutter,op='DIFFERENCE'):
    m=o.modifiers.new('b','BOOLEAN');m.operation=op;m.object=cutter;m.solver='EXACT';apply_mod(o,m)
    bpy.data.objects.remove(cutter)
def bevel(o,w,seg=2,angle=35):
    m=o.modifiers.new('bev','BEVEL');m.width=w*MM;m.segments=seg;m.limit_method='ANGLE';m.angle_limit=math.radians(angle);apply_mod(o,m)
    for poly in o.data.polygons: poly.use_smooth=True
def smooth_by_angle(o,deg=40):
    act(o)
    try: bpy.ops.object.shade_auto_smooth(angle=math.radians(deg))
    except Exception as e: bpy.ops.object.shade_smooth()
def recalc(o):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
C,n,u,v=geom.dial_frame(p)
def dial_pt(r,phi,h): return C+h*n+r*(np.sin(phi)*v+np.cos(phi)*u)
def lathe(name,prof,mat,nseg=160,uvsize=None,closed_axis=True):
    th=np.linspace(0,2*np.pi,nseg,endpoint=False);V=[];F=[]
    for (r,h) in prof: V+=[dial_pt(r,t,h) for t in th]
    m=len(prof)
    for i in range(m-1):
        for j in range(nseg):
            a=i*nseg+j;b=i*nseg+(j+1)%nseg;F.append((a,b,b+nseg,a+nseg))
    o=mk(name,V,F,mat);recalc(o)
    if uvsize:
        uvl=o.data.uv_layers.new(name='UVMap');Ci=np.array(C)
        for poly in o.data.polygons:
            for li in poly.loop_indices:
                P=np.array(o.data.vertices[o.data.loops[li].vertex_index].co)/MM-Ci
                uvl.data[li].uv=(float(P@v)/uvsize+0.5,float(P@u)/uvsize+0.5)
    return o
def cylinder(name,c,axis,r,h,mat,nseg=48,r2=None):
    V,F=geom.cyl(c,axis,r,h,nseg,r2);o=mk(name,V,F,mat);recalc(o);return o
def boxobj(name,c,h,mat,taper=1.0,rot=None):
    V,F=geom.box(c,h);V=np.array(V);c=np.array(c,float)
    top=V[:,2]>c[2];V[top,0]=c[0]+(V[top,0]-c[0])*taper
    o=mk(name,V,F,mat,smooth=False);recalc(o);return o
# ---------- body
V,F=geom.body(p,300);body=mk('govde',V,F,m_red);recalc(body)
# rear line-cord slot
cut=boxobj('cut',(p['xb']+2,49.5,p['z0']+8),(8,4.3,10),None);boolean(body,cut)
m_slot=texmat('kablo_yuvasi',loadimg('slot.png'),0.6)
zs0,zs1=p['z0']+1.0,p['z0']+17.0;xs_=p['xb']+5.5
slot_in=mk('kablo_yuvasi_ic',[(xs_,53.8,zs1),(xs_,45.2,zs1),(xs_,45.2,zs0),(xs_,53.8,zs0)],[(0,1,2,3)],m_slot,smooth=False)
uvl=slot_in.data.uv_layers.new(name='UVMap')
for li,uv in zip(range(4),[(0,1),(1,1),(1,0),(0,0)]): uvl.data[li].uv=uv
# logo plate on the rear deck, between the rear prongs (embossed lettering as a normal map from the rear photo)
m_logo=principled('logo_plaka',RED,ROUGH);nt=m_logo.node_tree;ti=nt.nodes.new('ShaderNodeTexImage');ti.image=loadimg('logo_normal.png');ti.image.colorspace_settings.name='Non-Color'
nmn=nt.nodes.new('ShaderNodeNormalMap');nmn.inputs['Strength'].default_value=0.45;nt.links.new(ti.outputs['Color'],nmn.inputs['Color']);nt.links.new(nmn.outputs['Normal'],nt.nodes['Principled BSDF'].inputs['Normal'])
def dk(x,y,h=0.35): return (x-h*p['sr']/np.hypot(1,p['sr']),y,p['zr0']+p['sr']*x+h/np.hypot(1,p['sr']))
xa,xb_,ya,yb=-65.8,-76.0,18.6,-19.2
logo=mk('logo_plaka',[dk(xa,ya),dk(xa,yb),dk(xb_,yb),dk(xb_,ya),dk(xa,ya,-1),dk(xa,yb,-1),dk(xb_,yb,-1),dk(xb_,ya,-1)],[(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],m_logo,smooth=False);recalc(logo)
uvl=logo.data.uv_layers.new(name='UVMap');UVc={0:(0,1),1:(1,1),2:(1,0),3:(0,0),4:(0,1),5:(1,1),6:(1,0),7:(0,0)}
for poly in logo.data.polygons:
    for li in poly.loop_indices: uvl.data[li].uv=UVc[logo.data.loops[li].vertex_index]
smooth_by_angle(body,50)
# ---------- cradle prongs + bar
zf=float(geom.top_profile(p,np.array([p['xe']]))[0]);zr=float(geom.top_profile(p,np.array([p['xer']]))[0])
for nm,x,zb,th in (('on',p['xe'],zf-6,p['pt']),('arka',p['xer'],zr-6,p['pt'])):
    for sg in (1,-1):
        o=boxobj('kulak_%s_%s'%(nm,'sol' if sg>0 else 'sag'),(x,sg*p['ye'],(p['ze']+zb)/2),(th/2+2.0,p['we'],(p['ze']-zb)/2),m_red,taper=(th-1.5)/(th+4.0));bevel(o,3.0,5,60)
bar=boxobj('catal_cubugu',(p['hx'],0,103.5),(4.0,30.5,3.5),m_clear);bevel(bar,1.0,3,60)
# ---------- dial
dd=p['dial_drop'];Rn=p['Rn'];hw=p['hw']
ring=lathe('kadran_halkasi',[(Rn-2.0,-dd-0.5),(Rn-2.0,-2.4),(Rn,-2.2),(Rn,-0.8),(Rn-0.8,0),(40.3,0),(39.5,-0.8),(39.5,-5.0),(0.01,-5.0)],m_ring,uvsize=120.)
smooth_by_angle(ring,35)
wt=2.3
wheel=lathe('parmak_carki',[(0.01,hw-wt),(37.2,hw-wt),(38.1,hw-wt+0.9),(38.1,hw+wt-0.9),(37.2,hw+wt),(0.01,hw+wt)],m_clear)
for k in range(10):
    c=cylinder('c',dial_pt(27.0,G['phi%d'%k],hw-4),n,6.7,8,None,40);boolean(wheel,c)
bevel(wheel,1.7,1,40)
hub=lathe('kart_kapagi',[(0.01,hw+wt-0.2),(21.5,hw+wt-0.2),(21.5,hw+wt+2.0),(20.3,hw+wt+3.4),(0.01,hw+wt+3.6)],m_clear);smooth_by_angle(hub,35)
for o in (wheel,hub,bar): o.visible_shadow=False
card_o=lathe('numara_karti',[(0.01,hw+wt+1.3),(18.6,hw+wt+1.3)],m_card,uvsize=44.,nseg=96)
# finger stop
ph=math.radians(98);rad=np.sin(ph)*v+np.cos(ph)*u;tan=np.cross(n,rad)
def stop_pt(r,h,s): return C+r*rad+h*n+s*tan
Vs=[];prof=[(51,-1.0,2.6),(51,hw+wt+2.2,2.6),(47,hw+wt+3.4,2.6),(36,hw+wt+3.0,2.0),(27.5,hw+wt+2.6,1.0)]
for (r,h,w) in prof:
    for (dh,ds) in ((0,-w),(0,w),(-0.9,w),(-0.9,-w)): Vs.append(stop_pt(r,h+dh,ds) if r<50 or h>0 else stop_pt(r+ (0.9 if dh<0 else 0),h,ds))
Fs=[];
for i in range(len(prof)-1):
    for j in range(4): a=i*4+j;b=i*4+(j+1)%4;Fs.append((a,b,b+4,a+4))
Fs+=[(0,1,2,3),(19,18,17,16)]
stop=mk('parmak_durdurucu',Vs,Fs,m_metal,smooth=False);recalc(stop)
# ---------- handset
V,F=geom.handset(p,48);hs=mk('ahize',V,F,m_red);recalc(hs)
# ---------- feet
for i,(sx,sy) in enumerate([(1,1),(1,-1),(-1,1),(-1,-1)]):
    f=cylinder('ayak_%d'%i,(sx*p['L']/2,sy*p['yf'],0),(0,0,1),p['rf'],p['z0']+1.5,m_foot,32);bevel(f,1.2,2,60)
# ---------- coiled cord
def catmull(P,n=40):
    P=np.array(P,float);Q=np.vstack([2*P[0]-P[1],P,2*P[-1]-P[-2]]);out=[]
    for i in range(1,len(Q)-2):
        for t in np.linspace(0,1,n,endpoint=False):
            a,b,c,d=Q[i-1],Q[i],Q[i+1],Q[i+2];out.append(0.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t**3))
    out.append(P[-1]);return np.array(out)
CORD=M.get('cord_path',[(-47,-112,84),(-47,-124,80),(-50,-128,60),(-46,-124,32),(-30,-116,10),(5,-108,6),(45,-104,6),(72,-98,6),(80,-86,6),(66,-79,6),(35,-80,6),(5,-79,7),(-12,-74,10),(-16,-69,12)])
cp=catmull(CORD);s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(cp,axis=0),axis=1))]
Ltot=s[-1];lead=12.;pitch=3.9;rc_=3.7;ns=int(Ltot/pitch*18)
ss=np.linspace(0,Ltot,ns);cc=np.stack([np.interp(ss,s,cp[:,i]) for i in range(3)],1)
T=np.gradient(cc,axis=0);T/=np.linalg.norm(T,axis=1)[:,None]
N=np.zeros_like(T);N0=np.cross(T[0],[0,0,1.]);N0/=np.linalg.norm(N0);N[0]=N0
for i in range(1,ns):
    q=N[i-1]-T[i]*(N[i-1]@T[i]);N[i]=q/np.linalg.norm(q)
B=np.cross(T,N);ramp=np.clip(np.minimum(ss-lead,Ltot-lead-ss)/8,0,1);ang=2*np.pi*ss/pitch
hel=cc+(rc_*ramp)[:,None]*(np.cos(ang)[:,None]*N+np.sin(ang)[:,None]*B)
cu=bpy.data.curves.new('kordon','CURVE');cu.dimensions='3D';sp=cu.splines.new('POLY');sp.points.add(ns-1)
sp.points.foreach_set('co',np.c_[hel*MM,np.ones(ns)].ravel());cu.bevel_depth=1.9*MM;cu.bevel_resolution=2;cu.use_fill_caps=True
cord=bpy.data.objects.new('kordon',cu);col_model.objects.link(cord);cord.parent=root;cu.materials.append(m_cordred)
act(cord);bpy.ops.object.convert(target='MESH');cord=bpy.context.view_layer.objects.active
for poly in cord.data.polygons: poly.use_smooth=True
# ---------- cameras
def photo_cam(vn):
    c=J['cams'][vn];import cv2  # noqa
def add_cam(name,pos,Rrows,f_px,W=1500,H=2000):
    cd=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,cd);col_studio.objects.link(o)
    Rw=np.array(Rrows).T@np.diag([1,-1,-1]);Mx=Matrix.Identity(4)
    for i in range(3):
        for j in range(3): Mx[i][j]=Rw[i,j]
        Mx[i][3]=pos[i]*MM
    o.matrix_world=Mx;cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=f_px*36/W;cd.clip_start=0.01;cd.clip_end=50;cd.display_size=0.03
    return o
def rodrigues(rv):
    rv=np.array(rv,float);th=np.linalg.norm(rv);k=rv/th;K=np.array([[0,-k[2],k[1]],[k[2],0,-k[0]],[-k[1],k[0],0]])
    return np.eye(3)+np.sin(th)*K+(1-np.cos(th))*K@K
def lookat_rows(P,Tg):
    P=np.array(P,float);z=np.array(Tg,float)-P;z/=np.linalg.norm(z);x=np.cross(z,[0,0,1.]);x/=np.linalg.norm(x);y=np.cross(z,x);return np.stack([x,y,z])
CAMS={}
for vn in ('front','side','rear'):
    c=J['cams'][vn];CAMS[vn]=add_cam('foto_'+vn,c['pos'],rodrigues(c['rv']),c['f'])
BEAUTY={'q1':((420,-330,300),(0,0,55),1900),'q2':((-380,-360,260),(0,0,55),1900),'q3':((330,380,220),(0,0,55),1900),'top':((1,0,750),(0,0,50),2300),
        'dial':((230,-60,230),(60,0,70),2600),'cradle':((-250,-150,260),(-45,0,95),2600),'sideL':((0,600,90),(0,0,60),2600),'low':((330,-300,60),(0,0,55),1900)}
for k,(P,Tg,f) in BEAUTY.items(): CAMS[k]=add_cam('cam_'+k,P,lookat_rows(P,Tg),f)
# ---------- studio: ground, world, lights
bpy.ops.mesh.primitive_plane_add(size=3);ground=bpy.context.active_object;ground.name='zemin'
for c in ground.users_collection: c.objects.unlink(ground)
col_studio.objects.link(ground)
m_ground=principled('zemin',M.get('table',[0.62,0.56,0.46]),0.35);ground.data.materials.append(m_ground)
w=bpy.data.worlds.new('w');S.world=w;w.use_nodes=True;bg=w.node_tree.nodes['Background'];bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=M.get('world',0.16)
def area(name,loc,target,size,energy,color=(1,1,1)):
    l=bpy.data.lights.new(name,'AREA');l.shape='RECTANGLE';l.size=size[0];l.size_y=size[1];l.energy=energy;l.color=color
    o=bpy.data.objects.new(name,l);col_studio.objects.link(o);o.location=loc
    d=Vector(target)-Vector(loc);o.rotation_euler=d.to_track_quat('-Z','Y').to_euler();return o
LIGHTS=[]
def rig(az_deg):
    """a large window on the az side, 25 deg up; dim world as fill"""
    for o in LIGHTS: bpy.data.objects.remove(o)
    LIGHTS.clear();a=math.radians(az_deg);e=math.radians(M.get('win_el',25));D=2.4
    LIGHTS.append(area('pencere',(D*math.cos(a)*math.cos(e),D*math.sin(a)*math.cos(e),D*math.sin(e)),(0,0,0.05),(2.2,1.4),M.get('window',260),(0.93,0.96,1.0)))
    b=a+math.radians(150)
    LIGHTS.append(area('dolgu',(D*math.cos(b)*0.8,D*math.sin(b)*0.8,1.3),(0,0,0.05),(1.5,1.5),M.get('fill',60),(1,0.97,0.93)))
S.render.engine='CYCLES';S.cycles.samples=SAMPLES;S.cycles.use_denoising=True
try:
    pr=bpy.context.preferences.addons['cycles'].preferences;pr.compute_device_type='METAL';pr.get_devices()
    for d in pr.devices: d.use=True
    S.cycles.device='GPU'
except Exception as e: print('gpu',e)
S.view_settings.view_transform='Standard';S.view_settings.look='None';S.render.film_transparent=True
S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGBA'
AZ={'front':180,'rear':0,'side':M.get('side_az',190)}
os.makedirs(OUT,exist_ok=True)
for sh in SHOTS:
    photo=sh in AZ
    S.camera=CAMS[sh];S.render.resolution_x=int(RES*0.75);S.render.resolution_y=RES;S.render.resolution_percentage=100
    rig(AZ.get(sh,M.get('beauty_az',200)));ground.is_shadow_catcher=photo;ground.scale=(1,1,1) if photo else (4,4,1);S.view_settings.exposure=M.get('exp_'+sh,0.0)
    S.render.filepath=os.path.join(OUT,sh+'.png');bpy.ops.render.render(write_still=True)
    if '--ids' in A and photo:
        pass
if arg('--blend') or arg('--glb'):
    rig(M.get('beauty_az',200));ground.is_shadow_catcher=False;ground.scale=(0.2,0.2,1);S.view_settings.exposure=0
    for k in list(BEAUTY): bpy.data.objects.remove(CAMS[k])
    S.camera=CAMS['front'];S.render.resolution_x=1500;S.render.resolution_y=2000
    if arg('--glb'):
        bpy.ops.object.select_all(action='DESELECT')
        for o in col_model.objects: o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.abspath(arg('--glb')),use_selection=True,export_apply=True,export_yup=True)
    if arg('--blend'):
        for vn in ('front','side','rear'): CAMS[vn].hide_viewport=True
        bpy.ops.object.select_all(action='DESELECT')
        from mathutils import Quaternion,Euler
        for scr in bpy.data.screens:
            for ar in scr.areas:
                if ar.type=='VIEW_3D':
                    sp=ar.spaces[0];sp.shading.type='MATERIAL';sp.overlay.show_extras=False
                    r3=sp.region_3d;r3.view_perspective='PERSP';r3.view_location=(0,0,0.06);r3.view_distance=0.75
                    r3.view_rotation=Euler((math.radians(65),0,math.radians(125))).to_quaternion()
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(arg('--blend')))
