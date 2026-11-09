"""Blender: the mug from one photo. usage: Blender -b -P build.py -- OUTDIR [--body-mask] [--final]
--body-mask: lathed body only, render its silhouette from the photo camera (OUTDIR/body_mask.png) and stop."""
import bpy, bmesh, json, math, sys, os
import numpy as np
from mathutils import Vector, Euler
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import cam as C
from geom import profile, P
argv=sys.argv[sys.argv.index('--')+1:]; OUT=os.path.abspath(argv[0]); os.makedirs(OUT,exist_ok=True)
BODYMASK='--body-mask' in argv; FINAL='--final' in argv
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
SEG=180
prof=profile()
def lathe(name,prof):
    me=bpy.data.meshes.new(name); bm=bmesh.new(); rings=[]
    for z,r,_ in prof:
        if r==0: rings.append([bm.verts.new((0,0,z))]); continue
        rings.append([bm.verts.new((r*math.cos(2*math.pi*i/SEG),r*math.sin(2*math.pi*i/SEG),z)) for i in range(SEG)])
    tags=[]
    for k,(a,b) in enumerate(zip(rings[:-1],rings[1:])):
        tg=prof[k+1][2] if prof[k][2]!=prof[k+1][2] and prof[k+1][2] in ('lip','floor') else prof[k][2]
        for i in range(SEG):
            j=(i+1)%SEG
            if len(a)==1: bm.faces.new((a[0],b[i],b[j]))
            elif len(b)==1: bm.faces.new((a[i],a[j],b[0]))
            else: bm.faces.new((a[i],a[j],b[j],b[i]))
            tags.append(tg)
    bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); sc.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth=True
    return ob,tags
BODY,TAGS=lathe('mug_body',prof)
# normals: profile goes outside-up then inside-down, so faces built a->b with i->j point outward; check one
me=BODY.data; me.update()
# ---------- camera ----------
camd=bpy.data.cameras.new('photo_cam'); cam=bpy.data.objects.new('photo_cam',camd); sc.collection.objects.link(cam)
cam.location=(P['D'],P['YC'],P['HC']); cam.rotation_euler=(math.pi/2-P['TH'],0,math.pi/2)
camd.sensor_fit='HORIZONTAL'; camd.sensor_width=36; camd.lens=P['F']/C.W*36
camd.shift_x=-(C.CX-C.W/2)/C.W; camd.shift_y=(C.CY-C.H/2)/C.W; camd.clip_start=0.02; camd.clip_end=20
sc.camera=cam; sc.render.resolution_x=C.W; sc.render.resolution_y=C.H
eng=bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys()
sc.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in eng else 'BLENDER_EEVEE'
sc.view_settings.view_transform='Standard'
world=bpy.data.worlds.new('world'); sc.world=world; world.use_nodes=True; BG=world.node_tree.nodes['Background']
def render(path,transparent=True):
    sc.render.film_transparent=transparent; sc.render.filepath=path; bpy.ops.render.render(write_still=True)
def emis(name,col):
    m=bpy.data.materials.new(name); m.use_nodes=True; n=m.node_tree.nodes
    for x in list(n): n.remove(x)
    e=n.new('ShaderNodeEmission'); e.inputs[0].default_value=(*col,1); o=n.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(e.outputs[0],o.inputs[0]); return m
if BODYMASK:
    BODY.data.materials.append(emis('white',(1,1,1))); BG.inputs[1].default_value=0
    sc.render.image_settings.color_mode='RGBA'; render(f'{OUT}/body_mask.png'); sys.exit(0)
WD=os.getcwd()
# ---------- materials: photo as base colour + emission (it carries its own light) ----------
def img(n): return bpy.data.images.load(f'{WD}/{n}')
def mat(name,image=None,color=None,rough=0.25,emit=0.6):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; n=nt.nodes; L=nt.links
    for x in list(n): n.remove(x)
    out=n.new('ShaderNodeOutputMaterial'); out.location=(600,0)
    b=n.new('ShaderNodeBsdfPrincipled'); b.location=(200,0)
    b.inputs['Roughness'].default_value=rough; b.inputs['Specular IOR Level'].default_value=0.4
    b.inputs['Coat Weight'].default_value=0.0
    if image:
        t=n.new('ShaderNodeTexImage'); t.image=image; t.location=(-300,0); t.extension='EXTEND'
        L.new(t.outputs[0],b.inputs['Base Color']); L.new(t.outputs[0],b.inputs['Emission Color'])
    else:
        b.inputs['Base Color'].default_value=(*color,1); b.inputs['Emission Color'].default_value=(*color,1)
    b.inputs['Emission Strength'].default_value=emit
    L.new(b.outputs[0],out.inputs[0]); return m
def srgb2lin(c): c=np.asarray(c)/255.0; return tuple(np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4))
info=json.load(open(f'{WD}/tex_info.json'))
M_FRONT=mat('glaze_photo',img('tex_body.png')); M_BACK=mat('glaze_photo_back',img('tex_back.png'))
M_IN=mat('glaze_inside_photo',img('tex_inside.png'))
M_INPLAIN=mat('glaze_inside',color=srgb2lin(info['inside_rgb']))
M_UNDER=mat('unglazed_foot',color=srgb2lin(info['under_rgb']),rough=0.7,emit=0.3)
M_HANDLE=mat('handle_photo',img('tex_handle.png'))
M_HSIDE=mat('handle_glaze',color=srgb2lin(info['handle_side_rgb']))
MATS=[M_FRONT,M_BACK,M_IN,M_INPLAIN,M_UNDER]
for m in MATS: me.materials.append(m)
# ---------- UVs ----------
# the handle's side (+Y, phi>0) folds at 50 deg: beyond it the photo's body carries the handle's reflection
A_POS=math.radians(float(os.environ.get('FOLD_POS','50'))); A_NEG=math.radians(float(os.environ.get('FOLD_NEG','72')))
def fold(phi):
    A=A_POS if phi>0 else A_NEG
    if abs(phi)<=A: return phi
    return math.copysign(A*(math.pi-abs(phi))/(math.pi-A),phi)
Cc=np.array([P['D'],P['YC'],P['HC']]); RI_RIM=None
from geom import ro, thick, T_RIM
h=P['h']; ri_top=ro(h-0.0025)-T_RIM
def visible_inside(co):
    # inside point seen through the opening: the segment to the camera crosses the rim plane inside the inner circle
    q=np.array(co); d=Cc-q
    if q[2]>=h-0.0005: return True
    t=(h-q[2])/d[2]; x=q+t*d; return math.hypot(x[0],x[1])<ri_top-0.0005
uvl=me.uv_layers.new(name='photo')
verts=np.array([v.co[:] for v in me.vertices])
for p,tg in zip(me.polygons,TAGS):
    cs=[me.vertices[me.loops[li].vertex_index].co for li in p.loop_indices]
    if tg in ('under','foot'):
        p.material_index=4 if tg=='under' else 0
    if tg in ('in','floor'):
        # the photo sees the far half's top band through the opening; the near half takes the far half's mirror
        # (phi -> pi - phi, same height). Whatever falls outside the opening reads the plain inside colour.
        p.material_index=2
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co; x=co.x if co.x<0 else -co.x
            u,v=C.proj([x,co.y,co.z]); uvl.data[li].uv=(u/C.W,1-v/C.H)
        continue
    if tg in ('out','lip','foot'):
        c=p.center; ph_=math.atan2(c.y,c.x); p.material_index=1 if abs(ph_)>(A_POS if ph_>0 else A_NEG)+1e-4 else 0
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            rho=math.hypot(co.x,co.y); f=fold(math.atan2(co.y,co.x))
            u,v=C.proj([rho*math.cos(f),rho*math.sin(f),co.z]); uvl.data[li].uv=(u/C.W,1-v/C.H)
# ---------- handle ----------
d=json.load(open(f'{WD}/handle.json'))
hme=bpy.data.meshes.new('handle'); hme.from_pydata(d['v'],[],d['f']); hme.update()
HAND=bpy.data.objects.new('mug_handle',hme); sc.collection.objects.link(HAND)
bm=bmesh.new(); bm.from_mesh(hme); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(hme); bm.free()
for p in hme.polygons: p.use_smooth=True
hme.materials.append(M_HANDLE); hme.materials.append(M_HSIDE)
uvh=hme.uv_layers.new(name='photo')
for p in hme.polygons:
    c=np.array(p.center); n=np.array(p.normal); tocam=Cc-c; tocam/=np.linalg.norm(tocam)
    # the photo sees this face: its own pixel; otherwise the mirror (x -> -x) if that faces the camera better
    mir=bool(np.array([-n[0],n[1],n[2]])@tocam > n@tocam); p.material_index=0
    for li in p.loop_indices:
        co=hme.vertices[hme.loops[li].vertex_index].co
        u,v=C.proj([-co.x if mir else co.x,co.y,co.z]); uvh.data[li].uv=(u/C.W,1-v/C.H)
OBJS=[BODY,HAND]
# ---------- comparison render: emission only ----------
def emission_only(on):
    for m in bpy.data.materials:
        if not m.use_nodes or 'Principled BSDF' not in m.node_tree.nodes: continue
        b=m.node_tree.nodes['Principled BSDF']; t=m.node_tree.nodes.get('Image Texture')
        if on:
            m['bc']=list(b.inputs['Base Color'].default_value)
            if t and b.inputs['Base Color'].links: m.node_tree.links.remove(b.inputs['Base Color'].links[0])
            b.inputs['Base Color'].default_value=(0,0,0,1); b.inputs['Emission Strength'].default_value=1.0
            b.inputs['Specular IOR Level'].default_value=0.0
        else:
            if t: m.node_tree.links.new(t.outputs[0],b.inputs['Base Color'])
            else: b.inputs['Base Color'].default_value=m['bc']
            b.inputs['Emission Strength'].default_value=0.3 if m.name=='unglazed_foot' else 0.6
            b.inputs['Specular IOR Level'].default_value=0.4
BG.inputs[1].default_value=0.0
emission_only(True); render(f'{OUT}/photo_view.png'); emission_only(False)
# ---------- lit scene, other views ----------
BG.inputs[0].default_value=(0.55,0.55,0.57,1); BG.inputs[1].default_value=0.3
def light(name,loc,energy,size):
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.size=size
    o=bpy.data.objects.new(name,ld); o.location=loc; sc.collection.objects.link(o)
    o.rotation_euler=(Vector((0,0,0.06))-o.location).to_track_quat('-Z','Y').to_euler(); return o
LIGHTS=[light('key',(0.4,-0.35,0.45),5,0.4),light('fill',(0.3,0.5,0.3),2,0.5),light('rim',(-0.45,0.1,0.4),3,0.4)]
fme=bpy.data.meshes.new('floor'); bm=bmesh.new(); bmesh.ops.create_grid(bm,x_segments=1,y_segments=1,size=0.25)
bm.to_mesh(fme); bm.free(); floor=bpy.data.objects.new('table',fme); sc.collection.objects.link(floor)
floor.data.materials.append(mat('table',color=srgb2lin((174,154,129)),rough=0.6,emit=0.0))
def shot(name,az,el,dist=0.42,lens=50,res=900):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector((0,0.01,0.058))
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=sc.render.resolution_y=res; render(f'{OUT}/view_{name}.png',transparent=False)
    bpy.data.objects.remove(c); bpy.data.cameras.remove(cd)
shot('front',0,10); shot('q_front_right',50,20); shot('handle_side',90,12); shot('q_rear_left',-130,25)
shot('rear',180,10); shot('top',20,70); shot('handle_close',70,25,dist=0.2)
sc.camera=cam; sc.render.resolution_x=C.W; sc.render.resolution_y=C.H
if FINAL:
    colM=bpy.data.collections.new('mug'); colS=bpy.data.collections.new('studio')
    sc.collection.children.link(colM); sc.collection.children.link(colS)
    root=bpy.data.objects.new('Mug',None); colM.objects.link(root)
    for o in OBJS: sc.collection.objects.unlink(o); colM.objects.link(o); o.parent=root
    for o in LIGHTS+[floor,cam]: sc.collection.objects.unlink(o); colS.objects.link(o)
    camd.display_size=0.02
    for scr in bpy.data.screens:
        for ar in scr.areas:
            for sp in ar.spaces:
                if sp.type=='VIEW_3D':
                    sp.shading.type='MATERIAL'; sp.overlay.show_extras=False; sp.clip_start=0.001
                    r3=sp.region_3d; r3.view_perspective='PERSP'; r3.view_location=(0,0.01,0.058); r3.view_distance=0.32
                    r3.view_rotation=Euler((math.radians(72),0,math.radians(115))).to_quaternion()
    bpy.ops.object.select_all(action='DESELECT')
    for o in OBJS: o.select_set(True)
    bpy.context.view_layer.objects.active=BODY
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/kupa.blend')
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/kupa.glb',use_selection=True,export_format='GLB')
