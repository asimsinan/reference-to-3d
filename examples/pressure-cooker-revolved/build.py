"""Blender: the pressure cooker from one photo. Lathe the pot and lid from their profiles, add the handles
(handles.json), put the photo on with folded-angle UVs, render the photo-camera comparison and a few views,
and with --final save a tidy .blend and a .glb.

usage: Blender -b -P build.py -- OUTDIR [--final]
       (run from the working folder: reads wall.json, handles.json, tex_*.png written by profile.py / prep.py)
env FOLD_A: the half-angle round the axis that takes the photo's pixels as they are (default 72 deg)."""
import bpy, bmesh, json, math, sys, os
from mathutils import Vector, Euler
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from cam import *
argv=sys.argv[sys.argv.index('--')+1:]; OUT=os.path.abspath(argv[0]); FINAL='--final' in argv
os.makedirs(OUT,exist_ok=True)
WD=os.getcwd()
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
wall=json.load(open(f'{WD}/wall.json'))
def rw(z): return wall['a']+wall['b']*z
SEG=160   # 360/160 = 2.25 deg a segment; FOLD_A on a segment boundary keeps the seam on vertices
# ---------- profiles (z, r) bottom to top, closed at the axis. Measured on the photo through cam.py ----------
# the wall from profile.py; the base corner, rim and lid read off zoomed grids (rows -> z at the side points,
# front points' rows as the check); the lid's flange r from its silhouette ends, its dome from the side rows
body=[(0,0),(0,0.100),(0.0015,0.109),(0.004,0.1145),(0.008,0.1175),(0.014,0.1195)]
body+=[(z,rw(z)) for z in [0.022+i*0.01 for i in range(18)]]
body+=[(0.196,rw(0.196)),(0.1985,rw(0.196)+0.0018),(0.2005,rw(0.196)+0.0012),(0.2010,0.128),(0.2010,0)]
lid=[(0.197,0),(0.197,0.119),(0.1985,0.1205),(0.2150,0.1205),(0.2160,0.140),(0.2165,0.1455),(0.2180,0.1468),
     (0.2210,0.1468),(0.2222,0.1450),(0.2240,0.1370),(0.2262,0.1290),(0.2290,0.1225),(0.2318,0.1080),
     (0.2340,0.0850),(0.2354,0.0550),(0.2360,0.0250),(0.2361,0)]
def lathe(name,prof):
    me=bpy.data.meshes.new(name); bm=bmesh.new(); rings=[]
    for z,r in prof:
        if r==0: rings.append([bm.verts.new((0,0,z))]); continue
        rings.append([bm.verts.new((r*math.cos(2*math.pi*i/SEG),r*math.sin(2*math.pi*i/SEG),z)) for i in range(SEG)])
    for a,b in zip(rings[:-1],rings[1:]):
        for i in range(SEG):
            j=(i+1)%SEG
            if len(a)==1: bm.faces.new((b[j],b[i],a[0]))
            elif len(b)==1: bm.faces.new((b[0],a[j],a[i]))
            else: bm.faces.new((a[i],a[j],b[j],b[i]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); sc.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth=True
    return ob
# ---------- materials: the photo as base colour plus some emission (it carries its own light) ----------
def img(n): return bpy.data.images.load(f'{WD}/{n}')
def mat(name,image=None,color=None,metal=0.0,rough=0.45):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; n=nt.nodes; L=nt.links
    for x in list(n): n.remove(x)
    out=n.new('ShaderNodeOutputMaterial'); out.location=(600,0)
    b=n.new('ShaderNodeBsdfPrincipled'); b.location=(200,0)
    b.inputs['Metallic'].default_value=metal; b.inputs['Roughness'].default_value=rough
    b.inputs['Specular IOR Level'].default_value=0.25
    if image:
        t=n.new('ShaderNodeTexImage'); t.image=image; t.location=(-300,0); t.extension='EXTEND'
        L.new(t.outputs[0],b.inputs['Base Color']); L.new(t.outputs[0],b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value=0.6
    else:
        b.inputs['Base Color'].default_value=(*color,1)
    L.new(b.outputs[0],out.inputs[0]); return m
M_FRONT=mat('steel_photo_front',img('tex_front.png')); M_BACK=mat('steel_photo_back',img('tex_back.png'))
M_HANDLE=mat('handle_photo',img('tex_handle.png'),rough=0.55)
M_BOTTOM=mat('steel_bottom',color=(0.35,0.35,0.36),metal=1.0,rough=0.35)
M_PLASTIC=mat('handle_plastic',color=(0.045,0.047,0.055),rough=0.4)
# ---------- UVs: each vertex through the photo's camera ----------
# Revolved parts: the angle phi round the axis is folded. Within +-A the photo's pixels as they are; beyond, the back
# is the mirror of that part, stretched, reaching 0 (the photo's centre) at 180 so the seam closes. Mirroring x -> -x
# instead (A = 90) put the photo's silhouette-edge pixels, stretched many times, on the sides: streaky bands from
# three-quarter views. Outside +-A the logo-free plate, so the logo is not repeated (mirrored) on the back.
A=math.radians(float(os.environ.get('FOLD_A','72')))
def fold(phi):
    if abs(phi)<=A: return phi
    return math.copysign(A*(math.pi-abs(phi))/(math.pi-A),phi)
def uv_revolved(ob,front,back,bottom):
    me=ob.data
    for m in (front,back,bottom): me.materials.append(m)
    uvl=me.uv_layers.new(name='photo')
    for p in me.polygons:
        c=p.center
        p.material_index=2 if p.normal.z<-0.6 else (1 if abs(math.atan2(c.y,c.x))>A+1e-4 else 0)
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            rho=math.hypot(co.x,co.y); f=fold(math.atan2(co.y,co.x))
            u,v=proj(rho*math.cos(f),rho*math.sin(f),co.z); uvl.data[li].uv=(u/W,1-v/H)
def uv_handle(ob,photo,side):
    # faces towards +-X take the photo (the back mirrored: |x|); the rest, which the photo sees edge-on, plastic
    me=ob.data; me.materials.append(photo); me.materials.append(side)
    uvl=me.uv_layers.new(name='photo')
    for p in me.polygons:
        p.material_index=0 if abs(p.normal.x)>0.35 else 1
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            u,v=proj(abs(co.x),co.y,co.z); uvl.data[li].uv=(u/W,1-v/H)
B=lathe('pot_body',body); uv_revolved(B,M_FRONT,M_BACK,M_BOTTOM)
LID=lathe('lid',lid); uv_revolved(LID,M_FRONT,M_BACK,M_BOTTOM)
HO=[]
for k,name in {'right':'handle_main','left':'handle_helper','tab':'lid_tab'}.items():
    d=json.load(open(f'{WD}/handles.json'))[k]
    me=bpy.data.meshes.new(name); me.from_pydata(d['v'],[],d['f']); me.update()
    ob=bpy.data.objects.new(name,me); sc.collection.objects.link(ob)
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth=True
    uv_handle(ob,M_HANDLE,M_PLASTIC); HO.append(ob)
OBJS=[B,LID]+HO
# ---------- the photo's camera ----------
camd=bpy.data.cameras.new('photo_cam'); cam=bpy.data.objects.new('photo_cam',camd); sc.collection.objects.link(cam)
cam.location=(D,0,HC); cam.rotation_euler=(math.pi/2,0,math.pi/2)
camd.sensor_fit='HORIZONTAL'; camd.sensor_width=36; camd.lens=F/W*36
camd.shift_x,camd.shift_y=blender_shift(); camd.clip_start=0.05; camd.clip_end=20
sc.camera=cam; sc.render.resolution_x=W; sc.render.resolution_y=H
eng=bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys()
sc.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in eng else 'BLENDER_EEVEE'
sc.view_settings.view_transform='Standard'
world=bpy.data.worlds.new('world'); sc.world=world; world.use_nodes=True
BG=world.node_tree.nodes['Background']
def render(path,transparent=True):
    sc.render.film_transparent=transparent; sc.render.filepath=path; bpy.ops.render.render(write_still=True)
# comparison render: emission only (photo materials emit their texture, flat ones their colour), world black
def emission_only(on):
    for m in [M_FRONT,M_BACK,M_HANDLE]:
        b=m.node_tree.nodes['Principled BSDF']; t=m.node_tree.nodes['Image Texture']
        if on: m.node_tree.links.remove(b.inputs['Base Color'].links[0]); b.inputs['Base Color'].default_value=(0,0,0,1)
        else: m.node_tree.links.new(t.outputs[0],b.inputs['Base Color'])
        b.inputs['Emission Strength'].default_value=1.0 if on else 0.6
        b.inputs['Specular IOR Level'].default_value=0.0 if on else 0.25
    for m in [M_PLASTIC,M_BOTTOM]:
        b=m.node_tree.nodes['Principled BSDF']; b.inputs['Emission Color'].default_value=b.inputs['Base Color'].default_value
        b.inputs['Emission Strength'].default_value=1.0 if on else 0.0
        b.inputs['Specular IOR Level'].default_value=0.0 if on else 0.5
BG.inputs[1].default_value=0.0
emission_only(True); render(f'{OUT}/photo_view.png'); emission_only(False)
# ---------- lit scene for the other views ----------
BG.inputs[0].default_value=(0.5,0.5,0.52,1); BG.inputs[1].default_value=0.25
def light(name,loc,energy,size):
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.size=size
    o=bpy.data.objects.new(name,ld); o.location=loc; sc.collection.objects.link(o)
    o.rotation_euler=(Vector((0,0,0.12))-o.location).to_track_quat('-Z','Y').to_euler(); return o
LIGHTS=[light('key',(1.0,0.8,1.0),14,1.0),light('fill',(0.6,-1.2,0.6),6,1.2),light('rim',(-1.0,0.2,0.9),8,1.0)]
fme=bpy.data.meshes.new('floor'); bm=bmesh.new(); bmesh.ops.create_grid(bm,x_segments=1,y_segments=1,size=0.6)
bm.to_mesh(fme); bm.free(); floor=bpy.data.objects.new('floor',fme); sc.collection.objects.link(floor)
floor.data.materials.append(mat('floor',color=(0.30,0.30,0.31),rough=0.8))
def shot(name,az,el,dist=1.15,lens=50):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector((0,0.04,0.12))
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=sc.render.resolution_y=800; render(f'{OUT}/view_{name}.png',transparent=False)
    bpy.data.objects.remove(c); bpy.data.cameras.remove(cd)
shot('front',0,8); shot('q_front_left',40,22); shot('q_rear_right',-140,25); shot('top',0,70); shot('rear',180,10)
shot('handle_close',60,25,dist=0.55)
sc.camera=cam; sc.render.resolution_x=sc.render.resolution_y=W
if FINAL:
    for o in HO:   # marching-cubes handles are dense (150k vertices): thin them before saving
        md=o.modifiers.new('dec','DECIMATE'); md.ratio=0.12
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier='dec')
    colM=bpy.data.collections.new('pressure_cooker'); colS=bpy.data.collections.new('studio')
    sc.collection.children.link(colM); sc.collection.children.link(colS)
    root=bpy.data.objects.new('PressureCooker',None); colM.objects.link(root)
    for o in OBJS: sc.collection.objects.unlink(o); colM.objects.link(o); o.parent=root
    for o in LIGHTS+[floor,cam]: sc.collection.objects.unlink(o); colS.objects.link(o)
    camd.display_size=0.05
    for scr in bpy.data.screens:
        for ar in scr.areas:
            for sp in ar.spaces:
                if sp.type=='VIEW_3D':
                    sp.shading.type='MATERIAL'; sp.overlay.show_extras=False
                    r3=sp.region_3d; r3.view_perspective='PERSP'; r3.view_location=(0,0.04,0.12); r3.view_distance=0.95
                    r3.view_rotation=Euler((math.radians(70),0,math.radians(120))).to_quaternion()
    bpy.ops.object.select_all(action='DESELECT')
    for o in OBJS: o.select_set(True)
    bpy.context.view_layer.objects.active=B
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/pressure_cooker.blend')
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/pressure_cooker.glb',use_selection=True,export_format='GLB')
