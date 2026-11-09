"""Blender: the vase from one photo, photo-projected. usage: Blender -b -P build.py -- OUTDIR"""
import bpy, bmesh, json, math, sys, os
import numpy as np
from mathutils import Vector, Euler
WD=os.getcwd(); sys.path.insert(0,WD)
import cam as C
from geom import profile, P, h
argv=sys.argv[sys.argv.index('--')+1:]; OUT=os.path.abspath(argv[0]); os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
SEG=192; prof=profile()
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
BODY,TAGS=lathe('vazo',prof); me=BODY.data
json.dump(TAGS,open(f'{WD}/tags.json','w'))
camd=bpy.data.cameras.new('photo_cam'); cam=bpy.data.objects.new('photo_cam',camd); sc.collection.objects.link(cam)
cam.location=(P['D'],P['YC'],P['HC']); cam.rotation_euler=(math.pi/2-P['TH'],0,math.pi/2)
camd.sensor_fit='HORIZONTAL'; camd.sensor_width=36; camd.lens=P['F']/C.W*36
camd.shift_x=-(C.CX-C.W/2)/C.W; camd.shift_y=(C.CY-C.H/2)/C.W; camd.clip_start=0.02; camd.clip_end=20
sc.camera=cam; sc.render.resolution_x=C.W; sc.render.resolution_y=C.H
sc.render.engine='BLENDER_EEVEE'; sc.view_settings.view_transform='Standard'
world=bpy.data.worlds.new('world'); sc.world=world; world.use_nodes=True; BG=world.node_tree.nodes['Background']
def render(path,transparent=True):
    sc.render.film_transparent=transparent; sc.render.filepath=path; bpy.ops.render.render(write_still=True)
def img(n): return bpy.data.images.load(f'{WD}/{n}')
def mat(name,image=None,color=None,rough=0.15,emit=0.6):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; n=nt.nodes; L=nt.links
    for x in list(n): n.remove(x)
    out=n.new('ShaderNodeOutputMaterial'); b=n.new('ShaderNodeBsdfPrincipled')
    b.inputs['Roughness'].default_value=rough; b.inputs['Specular IOR Level'].default_value=0.4
    if image:
        t=n.new('ShaderNodeTexImage'); t.image=image; t.extension='EXTEND'
        L.new(t.outputs[0],b.inputs['Base Color']); L.new(t.outputs[0],b.inputs['Emission Color'])
    else:
        b.inputs['Base Color'].default_value=(*color,1); b.inputs['Emission Color'].default_value=(*color,1)
    b.inputs['Emission Strength'].default_value=emit
    L.new(b.outputs[0],out.inputs[0]); return m
def srgb2lin(c): c=np.asarray(c)/255.0; return tuple(np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4))
info=json.load(open(f'{WD}/tex_info.json'))
for m in [mat('photo_body',img('tex_body.png')),mat('photo_inside',img('tex_inside.png')),
          mat('unglazed_base',color=srgb2lin(info['under_rgb']),rough=0.7,emit=0.3)]: me.materials.append(m)
A=math.radians(float(os.environ.get('FOLD','72')))
def fold(phi):
    if abs(phi)<=A: return phi
    return math.copysign(A*(math.pi-abs(phi))/(math.pi-A),phi)
uvl=me.uv_layers.new(name='photo')
for p,tg in zip(me.polygons,TAGS):
    if tg=='under':
        p.material_index=2
        for li in p.loop_indices: uvl.data[li].uv=(0.5,0.5)
        continue
    if tg in ('in','floor','lipin'):
        p.material_index=1
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co; x=co.x if co.x<0 else -co.x
            u,v=C.proj([x,co.y,co.z]); uvl.data[li].uv=(u/C.W,1-v/C.H)
        continue
    p.material_index=0
    for li in p.loop_indices:
        co=me.vertices[me.loops[li].vertex_index].co
        rho=math.hypot(co.x,co.y); f=fold(math.atan2(co.y,co.x))
        u,v=C.proj([rho*math.cos(f),rho*math.sin(f),co.z]); uvl.data[li].uv=(u/C.W,1-v/C.H)
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
            elif 'bc' in m: b.inputs['Base Color'].default_value=m['bc']
            b.inputs['Emission Strength'].default_value=0.6; b.inputs['Specular IOR Level'].default_value=0.4
BG.inputs[1].default_value=0.0
emission_only(True); render(f'{OUT}/photo_view.png')
BG.inputs[0].default_value=(0.55,0.55,0.57,1); BG.inputs[1].default_value=1.0
def light(name,loc,energy,size):
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.size=size
    o=bpy.data.objects.new(name,ld); o.location=loc; sc.collection.objects.link(o)
    o.rotation_euler=(Vector((0,0,0.15))-o.location).to_track_quat('-Z','Y').to_euler(); return o
LIGHTS=[light('key',(0.8,-0.7,0.9),0,0.8),light('fill',(0.6,0.9,0.5),0,1.0),light('rim',(-0.9,0.2,0.8),0,0.8)]
fme=bpy.data.meshes.new('floor'); bm=bmesh.new(); bmesh.ops.create_grid(bm,x_segments=1,y_segments=1,size=0.4)
bm.to_mesh(fme); bm.free(); floor=bpy.data.objects.new('zemin',fme); sc.collection.objects.link(floor)
floor.data.materials.append(mat('zemin',color=srgb2lin((120,120,120)),rough=0.5,emit=0.0))
def shot(name,az,el,dist=0.95,lens=50,res=800,t=(0,0,0.15)):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector(t)
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=sc.render.resolution_y=res; render(f'{OUT}/view_{name}.png',transparent=False)
    bpy.data.objects.remove(c); bpy.data.cameras.remove(cd)
shot('front',0,10); shot('side',90,10); shot('q_rear',-135,20); shot('rear',180,10); shot('top',20,65)
shot('foot_close',30,15,dist=0.35,t=(0,0,0.04)); shot('rim_close',-30,35,dist=0.35,t=(0,0,0.28))
emission_only(False)
sc.camera=cam; sc.render.resolution_x=C.W; sc.render.resolution_y=C.H
colM=bpy.data.collections.new('vazo'); colS=bpy.data.collections.new('studio')
sc.collection.children.link(colM); sc.collection.children.link(colS)
sc.collection.objects.unlink(BODY); colM.objects.link(BODY)
for o in LIGHTS+[floor,cam]: sc.collection.objects.unlink(o); colS.objects.link(o)
camd.display_size=0.03
bpy.ops.object.select_all(action='DESELECT'); BODY.select_set(True); bpy.context.view_layer.objects.active=BODY
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/vazo_foto_raw.blend')
