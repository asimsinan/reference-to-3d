"""Blender/Cycles: the cologne bottle in real materials. usage: Blender -b -P real.py -- OUTDIR [--photo-only] [--final]
Double-walled clear PET body with the label printed on its outer wall (cylindrical UV; label_albedo_m/trans/rough.png),
liquid inside, dip tube, black ribbed collar, smoked translucent cap with an actuator inside. Head coaxial.
The photo view: the photo projected onto a backdrop and a ground plane through the camera, so the glass refracts the
photo's own room. EXPO env: world/light strength multiplier (set by measuring against the photo)."""
import bpy, bmesh, json, math, sys, os
import numpy as np
from mathutils import Vector, Matrix, Euler
WD=os.getcwd(); sys.path.insert(0,WD)
import cam as C
P=C.P; Q=json.load(open(f'{WD}/pbr_info.json'))
argv=sys.argv[sys.argv.index('--')+1:]; OUT=os.path.abspath(argv[0]); os.makedirs(OUT,exist_ok=True)
PHOTO_ONLY='--photo-only' in argv; FINAL='--final' in argv; EXPO=float(os.environ.get('EXPO','1.0'))
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
R,rb,rf,h=P['R'],P['rb'],P['rf'],P['h']; rs=0.0015; rn=0.0105; T=0.0006; ZF=0.0045
rc0,rc1,zc0,zc1=P['rc0'],P['rc1'],P['zc0'],P['zc1']; rk0,rk1,zk1,KF=P['rk0'],P['rk1'],P['zk1'],P['KF']
Z_LIQ=0.072
rout=lambda z: rb+(R-rb)*z/h
def body_profile():
    rg=rb-rf; pts=[(0.0025,0.0,'under'),(0.0025,rg-0.003,'under'),(0.0,rg,'under')]
    for t in np.linspace(0,math.pi/2,9)[1:]: pts.append((rf-rf*math.cos(t), rg+rf*math.sin(t),'out'))
    for z in np.linspace(rf,h-rs,40)[1:]: pts.append((z,rout(z),'out'))
    for t in np.linspace(0,math.pi/2,7)[1:]: pts.append((h-rs+rs*math.sin(t), R-rs+rs*math.cos(t),'out'))
    zn=zc0+0.003
    pts+=[(h,rn,'top'),(zn,rn,'neck'),(zn,rn-T,'neck'),(h+T,rn-T,'in'),(h-T,R-rs-T,'in')]
    for z in np.linspace(h-rs-T,ZF+0.002,36): pts.append((z,rout(z)-T,'in'))
    for t in np.linspace(0,math.pi/2,6)[1:]: pts.append((ZF+0.002-0.002*math.sin(t), rout(ZF)-T-0.002+0.002*math.cos(t),'in'))
    pts+=[(ZF,rg-0.003,'in'),(ZF+0.002,0.0,'in')]
    return pts
def liquid_profile():
    e=0.00005; pts=[(ZF+0.002+e,0.0,'liq'),(ZF+e,rb-rf-0.003,'liq')]
    for z in np.linspace(ZF+e,Z_LIQ,30): pts.append((z,rout(z)-T+e,'liq'))
    pts.append((Z_LIQ,0.0,'liq')); return pts
def tube_profile(): return [(0.006,0.0,'t'),(0.006,0.0016,'t'),(zc1,0.0016,'t'),(zc1,0.0,'t')]
def collar_profile():
    pts=[(zc0,0.0,'cunder'),(zc0,rc0*0.8,'cunder'),(zc0,rc0,'col')]
    for z in np.linspace(zc0,zc1,12)[1:]: pts.append((z,rc0+(rc1-rc0)*(z-zc0)/(zc1-zc0),'col'))
    pts+=[(zc1,rk0+0.0004,'coltop'),(zc1,0.0,'coltop')]; return pts
def cap_profile():
    z0=zc1-0.0008; w=0.001; pts=[(z0,rk0-w,'k'),(z0,rk0,'k')]
    for z in np.linspace(z0,zk1-KF,16)[1:]: pts.append((z,rk0+(rk1-rk0)*(z-zc1)/(zk1-zc1),'k'))
    for t in np.linspace(0,math.pi/2,7)[1:]: pts.append((zk1-KF+KF*math.sin(t), rk1-KF+KF*math.cos(t),'k'))
    pts.append((zk1,0.0,'k')); pts.append((zk1-w,0.0,'k'))
    for t in np.linspace(math.pi/2,0,5)[1:]: pts.append((zk1-w-KF+KF*math.sin(t), rk1-w-KF+KF*math.cos(t),'k'))
    for z in np.linspace(zk1-KF-w,z0+0.0005,10)[1:]: pts.append((z,rk0-w+(rk1-rk0)*(z-zc1)/(zk1-zc1),'k'))
    return pts
def actuator_profile():
    ra=0.006; pts=[(zc1,0.0,'a'),(zc1,ra,'a'),(zk1-0.006,ra,'a'),(zk1-0.005,ra-0.001,'a'),(zk1-0.005,0.0028,'a'),(zk1-0.0035,0.0028,'a'),(zk1-0.0035,0.0,'a')]
    return pts
def lathe(name,prof,SEG,ribs=None,close=True):
    me=bpy.data.meshes.new(name); bm=bmesh.new(); rings=[]
    for z,r,tg in prof:
        if r==0: rings.append([bm.verts.new((0,0,z))]); continue
        ring=[]
        for i in range(SEG):
            ph=2*math.pi*i/SEG; rr=r
            if ribs and tg==ribs[0]: rr=r+ribs[2]*math.cos(ribs[1]*ph)
            ring.append(bm.verts.new((rr*math.cos(ph),rr*math.sin(ph),z)))
        rings.append(ring)
    tags=[]
    pairs=list(zip(rings[:-1],rings[1:]))+([(rings[-1],rings[0])] if close and len(rings[-1])>1 and len(rings[0])>1 else [])
    ptags=[prof[k][2] for k in range(len(pairs))]
    for k,(a,b) in enumerate(pairs):
        tg=ptags[k]
        if len(a)==1 and len(b)==1: continue
        for i in range(SEG):
            j=(i+1)%SEG
            if len(a)==1: bm.faces.new((a[0],b[i],b[j]))
            elif len(b)==1: bm.faces.new((a[i],a[j],b[0]))
            else: bm.faces.new((a[i],a[j],b[j],b[i]))
            tags.append(tg)
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-7)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); sc.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth=True
    return ob,tags
BODY,TB=lathe('sise_govde',body_profile(),180,close=False)
LIQ,_=lathe('sise_sivi',liquid_profile(),180,close=False)
TUBE,_=lathe('sise_boru',tube_profile(),32,close=False)
COL,TC=lathe('sise_bilezik',collar_profile(),192,ribs=('col',48,0.00035),close=False)
CAP,TK=lathe('sise_kapak',cap_profile(),128,close=False)
ACT,_=lathe('sise_puskurtucu',actuator_profile(),64,close=False)
OBJS=[BODY,LIQ,TUBE,COL,CAP,ACT]
# ---------- materials ----------
def img(n,noncolor=False):
    im=bpy.data.images.load(f'{WD}/{n}')
    if noncolor: im.colorspace_settings.name='Non-Color'
    return im
def principled(name,**kw):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; n=nt.nodes
    for x in list(n): n.remove(x)
    out=n.new('ShaderNodeOutputMaterial'); out.location=(600,0); b=n.new('ShaderNodeBsdfPrincipled'); b.location=(200,0)
    for k,v in kw.items(): b.inputs[k].default_value=v
    nt.links.new(b.outputs[0],out.inputs[0]); return m,b,nt
def texmat(name):
    m,b,nt=principled(name,**{'Transmission Weight':1.0,'IOR':1.57,'Roughness':0.03,'Specular IOR Level':0.5})
    for inp,fn,nc,loc in (('Base Color','label_albedo_m.png',False,(-400,300)),('Transmission Weight','label_trans.png',True,(-400,0)),('Roughness','label_rough.png',True,(-400,-300))):
        t=nt.nodes.new('ShaderNodeTexImage'); t.image=img(fn,nc); t.location=loc; t.extension='REPEAT'
        nt.links.new(t.outputs[0],b.inputs[inp])
    return m
M_PETL=texmat('pet_etiket')
M_PET,_,_=principled('pet_seffaf',**{'Base Color':(1,1,1,1),'Transmission Weight':1.0,'IOR':1.57,'Roughness':0.03,'Specular IOR Level':0.5})
M_LIQ,_,_=principled('kolonya_sivi',**{'Base Color':(0.98,0.99,1.0,1),'Transmission Weight':1.0,'IOR':1.36,'Roughness':0.0,'Specular IOR Level':0.5})
M_TUBE,_,_=principled('boru',**{'Base Color':(0.9,0.9,0.9,1),'Transmission Weight':0.5,'IOR':1.5,'Roughness':0.35})
M_BLACK,_,_=principled('siyah_plastik',**{'Base Color':(0.008,0.008,0.008,1),'Roughness':0.5,'Specular IOR Level':0.5})
M_CAP,_,_=principled('fume_kapak',**{'Base Color':(0.10,0.10,0.11,1),'Transmission Weight':0.7,'IOR':1.5,'Roughness':0.10,'Specular IOR Level':0.5})
M_ACT,_,_=principled('puskurtucu',**{'Base Color':(0.05,0.05,0.05,1),'Roughness':0.5})
def set_mats(ob,tags,rule):
    me=ob.data; mats=list(dict.fromkeys(rule.values()))
    for m in mats: me.materials.append(m)
    for p,tg in zip(me.polygons,tags): p.material_index=mats.index(rule.get(tg,mats[0]))
set_mats(BODY,TB,{'out':M_PETL,'top':M_PET,'neck':M_PET,'in':M_PET,'under':M_PET})
LIQ.data.materials.append(M_LIQ); TUBE.data.materials.append(M_TUBE); COL.data.materials.append(M_BLACK); CAP.data.materials.append(M_CAP); ACT.data.materials.append(M_ACT)
# cylindrical UVs on the body: u=(phi+pi)/2pi (front at 0.5), v=z/h
uvl=BODY.data.uv_layers.new(name='label'); me=BODY.data
for p in me.polygons:
    cph=math.atan2(p.center.y,p.center.x)
    for li in p.loop_indices:
        co=me.vertices[me.loops[li].vertex_index].co; ph=math.atan2(co.y,co.x)
        if cph>2.5 and ph<-2.5: ph+=2*math.pi          # seam at the back
        if cph<-2.5 and ph>2.5: ph-=2*math.pi
        uvl.data[li].uv=((ph+math.pi)/(2*math.pi), co.z/h)
# ---------- camera (the photo's) ----------
camd=bpy.data.cameras.new('photo_cam'); cam=bpy.data.objects.new('photo_cam',camd); sc.collection.objects.link(cam)
f,r,up=C.axes(P['TH'],P['PSI']); Cc=Vector((P['D'],P['YC'],P['HC']))
cam.matrix_world=Matrix(((r[0],up[0],-f[0],Cc.x),(r[1],up[1],-f[1],Cc.y),(r[2],up[2],-f[2],Cc.z),(0,0,0,1)))
camd.sensor_fit='HORIZONTAL'; camd.sensor_width=36; camd.lens=P['F']/C.W*36
camd.shift_x=-(P['CX']-C.W/2)/C.W; camd.shift_y=(P['CY']-C.H/2)/C.W; camd.clip_start=0.02; camd.clip_end=20
sc.camera=cam; sc.render.resolution_x=C.W; sc.render.resolution_y=C.H
# ---------- render settings: Cycles ----------
sc.render.engine='CYCLES'; sc.cycles.samples=int(os.environ.get('SAMPLES','96')); sc.cycles.use_denoising=True
sc.cycles.max_bounces=12; sc.cycles.transmission_bounces=12; sc.cycles.transparent_max_bounces=12; sc.cycles.glossy_bounces=6
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='METAL'; prefs.get_devices()
    for d in prefs.devices: d.use=True
    sc.cycles.device='GPU'; print('Cycles on METAL')
except Exception as e: print('GPU not available:',e)
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'; sc.view_settings.exposure=0.0
world=bpy.data.worlds.new('world'); sc.world=world; world.use_nodes=True; wn=world.node_tree.nodes; BG=wn['Background']
env=wn.new('ShaderNodeTexEnvironment'); env.image=bpy.data.images.load('/Applications/Blender.app/Contents/Resources/5.2/datafiles/studiolights/world/interior.exr')
world.node_tree.links.new(env.outputs[0],BG.inputs[0]); BG.inputs[1].default_value=0.9*EXPO
def area(name,loc,energy,size,target=(0,0,0.07)):
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy*EXPO; ld.size=size
    o=bpy.data.objects.new(name,ld); o.location=loc; sc.collection.objects.link(o)
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler(); return o
LIGHTS=[area('key',(0.35,-0.45,0.55),14,0.5),area('fill',(0.45,0.4,0.3),4,0.6),area('rim',(-0.4,0.15,0.5),5,0.4)]
LIGHTS[0].data.color=(1.0,0.96,0.88)
# ---------- the photo as backdrop + ground, projected through the camera ----------
def plane(name,verts,mat):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],[(0,1,2,3)]); me.update()
    o=bpy.data.objects.new(name,me); sc.collection.objects.link(o); me.materials.append(mat); return o
def photo_mat(name):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; n=nt.nodes
    for x in list(n): n.remove(x)
    out=n.new('ShaderNodeOutputMaterial'); e=n.new('ShaderNodeEmission'); t=n.new('ShaderNodeTexImage'); t.image=img('photo_clean.jpg')
    tc=n.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Window'],t.inputs[0])
    nt.links.new(t.outputs[0],e.inputs[0]); nt.links.new(e.outputs[0],out.inputs[0]); e.inputs[1].default_value=1.0; return m
PM=photo_mat('fotograf')
BACK=plane('fon',[(-3.0,-4,-3),(-3.0,4,-3),(-3.0,4,4),(-3.0,-4,4)],PM)
GROUND=plane('zemin_foto',[(1.0,-4,0),(1.0,4,0),(-3.0,4,0),(-3.0,-4,0)],PM)
for o in (BACK,GROUND):
    uv=o.data.uv_layers.new(name='cam')
    for p in o.data.polygons:
        for li in p.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co; u,v=C.proj(np.array([co[:]],float))[0]
            uv.data[li].uv=(u/C.W,1-v/C.H)
    o.visible_shadow=False
def render(path,transparent=False):
    sc.render.film_transparent=transparent; sc.render.image_settings.color_mode='RGBA' if transparent else 'RGB'
    sc.render.filepath=path; bpy.ops.render.render(write_still=True)
# photo view: photo backdrop on, HDRI off (the photo's room lights it: keep lamps + a dim world)
BG.inputs[1].default_value=0.35*EXPO
render(f'{OUT}/photo_view.png')
if PHOTO_ONLY: sys.exit(0)
# ---------- studio for the other views ----------
BACK.hide_render=True; GROUND.hide_render=True; BG.inputs[1].default_value=0.9*EXPO
def srgb2lin(c): c=np.asarray(c)/255.0; return tuple(np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4))
mt,_,_=principled('masa',**{'Base Color':(*srgb2lin((196,176,146)),1),'Roughness':0.55})
fme=bpy.data.meshes.new('masa'); bm=bmesh.new(); bmesh.ops.create_grid(bm,x_segments=1,y_segments=1,size=0.6); bm.to_mesh(fme); bm.free()
FLOOR=bpy.data.objects.new('masa',fme); sc.collection.objects.link(FLOOR); fme.materials.append(mt)
wm,_,_=principled('duvar',**{'Base Color':(0.45,0.46,0.48,1),'Roughness':0.8})
WALL=plane('duvar',[(-0.5,-0.8,0),(-0.5,0.8,0),(-0.5,0.8,1.0),(-0.5,-0.8,1.0)],wm)
def shot(name,az,el,dist=0.36,lens=85,res=900,target=(0,0,0.068)):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector(target)
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=sc.render.resolution_y=res; render(f'{OUT}/view_{name}.png')
    bpy.data.objects.remove(c); bpy.data.cameras.remove(cd)
for nm,az,el,kw in (('front',0,8,{}),('q_front_right',45,18,{}),('side',90,10,{}),('q_rear',-135,22,{}),('rear',180,8,{}),('top',30,65,{}),
                    ('close_label',15,5,dict(dist=0.2,target=(0,0,0.045))),('close_cap',40,20,dict(dist=0.15,target=(0,0,0.115))),
                    ('close_shoulder',-60,15,dict(dist=0.15,target=(0,0,0.085))),('close_base',120,12,dict(dist=0.16,target=(0,0,0.012)))):
    shot(nm,az,el,**kw)
sc.camera=cam; sc.render.resolution_x=C.W; sc.render.resolution_y=C.H
if FINAL:
    colM=bpy.data.collections.new('kolonya'); colS=bpy.data.collections.new('studio'); colP=bpy.data.collections.new('fotograf_fonu')
    for c_ in (colM,colS,colP): sc.collection.children.link(c_)
    root=bpy.data.objects.new('Kolonya',None); colM.objects.link(root)
    for o in OBJS: sc.collection.objects.unlink(o); colM.objects.link(o); o.parent=root
    for o in LIGHTS+[FLOOR,WALL,cam]: sc.collection.objects.unlink(o); colS.objects.link(o)
    for o in (BACK,GROUND): sc.collection.objects.unlink(o); colP.objects.link(o); o.hide_viewport=True
    camd.display_size=0.02
    for scr in bpy.data.screens:
        for ar in scr.areas:
            for sp in ar.spaces:
                if sp.type=='VIEW_3D':
                    sp.shading.type='MATERIAL'; sp.overlay.show_extras=False; sp.clip_start=0.001
                    r3=sp.region_3d; r3.view_perspective='PERSP'; r3.view_location=(0,0,0.07); r3.view_distance=0.38
                    r3.view_rotation=Euler((math.radians(78),0,math.radians(60))).to_quaternion()
    bpy.ops.object.select_all(action='DESELECT')
    for o in OBJS: o.select_set(True)
    bpy.context.view_layer.objects.active=BODY
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/kolonya_gercek.blend')
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/kolonya_gercek.glb',use_selection=True,export_format='GLB')
print('verts:',{o.name:len(o.data.vertices) for o in OBJS})
