"""Blender: the vase in real materials. usage: Blender -b -P real.py -- OUTDIR [--photo-only] [--no-render]
glazed porcelain with the lighting-free checker albedo (albedo.py) on cylindrical UVs, gold rim bead and foot band
(metallic), unglazed foot ring, plain glaze inside. env EXPO (AgX exposure), KEY (W), WORLD, SPP"""
import bpy, bmesh, json, math, sys, os
import numpy as np
from mathutils import Vector, Euler
WD=os.getcwd(); sys.path.insert(0,WD)
import cam as C
from geom import profile, P, h, GOLD_BAND, GOLD_RIM_Z
argv=sys.argv[sys.argv.index('--')+1:]; OUT=os.path.abspath(argv[0]); os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
SEG=192; prof=profile()
me=bpy.data.meshes.new('vazo'); bm=bmesh.new(); rings=[]
for z,r,_ in prof:
    if r==0: rings.append([bm.verts.new((0,0,z))]); continue
    rings.append([bm.verts.new((r*math.cos(2*math.pi*i/SEG-math.pi),r*math.sin(2*math.pi*i/SEG-math.pi),z)) for i in range(SEG)])
tags=[]; ring_i=[]
for k,(a,b) in enumerate(zip(rings[:-1],rings[1:])):
    tg=prof[k+1][2] if prof[k][2]!=prof[k+1][2] and prof[k+1][2] in ('lip','floor') else prof[k][2]
    for i in range(SEG):
        j=(i+1)%SEG
        if len(a)==1: bm.faces.new((a[0],b[i],b[j]))
        elif len(b)==1: bm.faces.new((a[i],a[j],b[0]))
        else: bm.faces.new((a[i],a[j],b[j],b[i]))
        tags.append(tg); ring_i.append(i)
bm.to_mesh(me); bm.free()
BODY=bpy.data.objects.new('Vazo',me); 
for p in me.polygons: p.use_smooth=True
HH=cv2h=None
import struct
def srgb2lin(c): c=np.asarray(c,float)/255.0; return tuple(np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4))
alb=bpy.data.images.load(f'{WD}/alb_cyl.png'); HPX=alb.size[1]
def principled(name,base=None,image=None,rough=0.06,metal=0.0,ior=1.5,coat=0.0):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; n=nt.nodes; L=nt.links
    for x in list(n): n.remove(x)
    o=n.new('ShaderNodeOutputMaterial'); o.location=(400,0); b=n.new('ShaderNodeBsdfPrincipled')
    b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal; b.inputs['IOR'].default_value=ior
    b.inputs['Coat Weight'].default_value=coat
    if image:
        t=n.new('ShaderNodeTexImage'); t.image=image; t.location=(-350,0); t.interpolation='Cubic'
        L.new(t.outputs[0],b.inputs['Base Color'])
    else: b.inputs['Base Color'].default_value=(*base,1)
    L.new(b.outputs[0],o.inputs[0]); return m
ai=json.load(open(f'{WD}/alb_info.json')); white=srgb2lin(ai['white_bgr'][::-1])
M=[principled('porselen_sir',image=alb,rough=0.06),
   principled('altin_yaldiz',base=(0.72,0.40,0.10),rough=0.2,metal=1.0),
   principled('porselen_ic',base=white,rough=0.08),
   principled('sirsiz_taban',base=srgb2lin((214,205,192)),rough=0.7)]
for m in M: me.materials.append(m)
uvl=me.uv_layers.new(name='UVMap')
for p,tg,ri in zip(me.polygons,tags,ring_i):
    zc=p.center.z
    if tg=='under': p.material_index=3
    elif tg in ('in','floor'): p.material_index=2
    elif tg in ('lip','lipin') or (tg=='out' and (zc>GOLD_RIM_Z or GOLD_BAND[0]<zc<GOLD_BAND[1])): p.material_index=1
    else: p.material_index=0
    for li in p.loop_indices:
        vi=me.loops[li].vertex_index; co=me.vertices[vi].co
        if math.hypot(co.x,co.y)<1e-9: u=(ri+0.5)/SEG
        else:
            u=(math.atan2(co.y,co.x)+math.pi)/(2*math.pi)
            if u<(ri-0.5)/SEG: u+=1.0
            if u>(ri+1.5)/SEG: u-=1.0
        v=1-((h-co.z)/0.00025)/HPX
        uvl.data[li].uv=(u,v)
# weld seam-free: lathe already shares verts; UV seam handled per loop
colM=bpy.data.collections.new('vazo'); colS=bpy.data.collections.new('studyo')
sc.collection.children.link(colM); sc.collection.children.link(colS); colM.objects.link(BODY)
# --- photo camera ---
camd=bpy.data.cameras.new('foto_kamera'); cam=bpy.data.objects.new('foto_kamera',camd); colS.objects.link(cam)
cam.location=(P['D'],P['YC'],P['HC']); cam.rotation_euler=(math.pi/2-P['TH'],0,math.pi/2)
camd.sensor_fit='HORIZONTAL'; camd.sensor_width=36; camd.lens=P['F']/C.W*36
camd.shift_x=-(C.CX-C.W/2)/C.W; camd.shift_y=(C.CY-C.H/2)/C.W; camd.clip_start=0.02; camd.clip_end=30; camd.display_size=0.04
sc.camera=cam
# --- floor: pale satin table top ---
fme=bpy.data.meshes.new('masa'); b2=bmesh.new(); bmesh.ops.create_circle(b2,cap_ends=True,segments=96,radius=0.45)
b2.to_mesh(fme); b2.free(); floor=bpy.data.objects.new('masa',fme); colS.objects.link(floor)
floor.data.materials.append(principled('masa',base=srgb2lin((120,112,104)),rough=0.45))
tme=bpy.data.meshes.new('ayna_tepsi'); b3=bmesh.new(); bmesh.ops.create_circle(b3,cap_ends=True,segments=96,radius=0.2)
b3.to_mesh(tme); b3.free(); tray=bpy.data.objects.new('ayna_tepsi',tme); tray.location.z=-0.0005; floor.location.z=-0.001; colS.objects.link(tray)
tray.data.materials.append(principled('ayna',base=srgb2lin((205,205,203)),rough=0.03,metal=1.0))
# --- world + lights ---
w=bpy.data.worlds.new('dunya'); sc.world=w; w.use_nodes=True; nt=w.node_tree; n=nt.nodes
for x in list(n): n.remove(x)
env=n.new('ShaderNodeTexEnvironment'); env.image=bpy.data.images.load(os.path.join(bpy.utils.system_resource('DATAFILES'),'studiolights','world','interior.exr'))
mp=n.new('ShaderNodeMapping'); tc=n.new('ShaderNodeTexCoord'); mp.inputs['Rotation'].default_value=(0,0,math.radians(200))
bg=n.new('ShaderNodeBackground'); bg.inputs[1].default_value=float(os.environ.get('WORLD','0.8')); o=n.new('ShaderNodeOutputWorld')
nt.links.new(tc.outputs['Generated'],mp.inputs[0]); nt.links.new(mp.outputs[0],env.inputs[0]); nt.links.new(env.outputs[0],bg.inputs[0]); nt.links.new(bg.outputs[0],o.inputs[0])
def light(name,loc,energy,size,tgt=(0,0,0.15)):
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.size=size; ld.shape='DISK'
    ob=bpy.data.objects.new(name,ld); ob.location=loc; colS.objects.link(ob)
    ob.rotation_euler=(Vector(tgt)-ob.location).to_track_quat('-Z','Y').to_euler(); return ob
KEY=float(os.environ.get('KEY','60'))
light('anahtar',(0.75,0.55,0.75),KEY,0.6); light('dolgu',(0.7,-0.8,0.4),KEY*0.35,0.8); light('arka',(-0.8,-0.2,0.9),KEY*0.6,0.6)
sc.render.engine='CYCLES'; sc.cycles.samples=int(os.environ.get('SPP','128')); sc.cycles.use_denoising=True
try:
    bpy.context.preferences.addons['cycles'].preferences.compute_device_type='METAL'; bpy.context.preferences.addons['cycles'].preferences.get_devices(); sc.cycles.device='GPU'
except Exception as e: print('gpu',e)
sc.view_settings.view_transform='AgX'; sc.view_settings.look=os.environ.get('LOOK','AgX - Medium High Contrast')
sc.view_settings.exposure=float(os.environ.get('EXPO','0.0'))
def rend(path,res):
    sc.render.resolution_x,sc.render.resolution_y=res; sc.render.filepath=path; bpy.ops.render.render(write_still=True)
if '--photo-only' in argv or '--no-render' not in argv:
    sc.camera=cam; rend(f'{OUT}/r_photo_cam.png',(600,900))
if '--photo-only' in argv: sys.exit(0)
def shot(name,az,el,dist=0.95,lens=50,res=900,t=(0,0,0.15)):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector(t)
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    rend(f'{OUT}/r_{name}.png',(res,res)); bpy.data.objects.remove(c); bpy.data.cameras.remove(cd)
if '--no-render' not in argv:
    shot('on',0,12); shot('yan',90,12); shot('arka',180,12); shot('ust',30,60)
    shot('ayak_yakin',30,15,dist=0.32,t=(0,0,0.04)); shot('agiz_yakin',-30,35,dist=0.3,t=(0,0,0.28))
sc.camera=cam; sc.render.resolution_x=600; sc.render.resolution_y=900
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type=='VIEW_3D':
                sp.shading.type='MATERIAL'; sp.shading.use_scene_world=False; sp.shading.studio_light='interior.exr'
                sp.overlay.show_extras=False; sp.clip_start=0.002
                r3=sp.region_3d; r3.view_perspective='PERSP'; r3.view_location=(0,0,0.15); r3.view_distance=0.8
                r3.view_rotation=Euler((math.radians(75),0,math.radians(100))).to_quaternion()
bpy.ops.object.select_all(action='DESELECT'); BODY.select_set(True); bpy.context.view_layer.objects.active=BODY
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/vazo.blend')
bpy.ops.export_scene.gltf(filepath=f'{OUT}/vazo.glb',use_selection=True,export_format='GLB')
