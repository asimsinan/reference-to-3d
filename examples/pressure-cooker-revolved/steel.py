"""Blender: the real-material version. Opens build.py's .blend and replaces the photo's baked light with materials
that react to the scene: polished stainless body (logo as a dark satin print), satin lid, matte base, black plastic
handles (the photo's details kept, darkened). Renders a white product studio with Cycles, saves .blend and .glb.

usage: Blender -b OUT/pressure_cooker.blend -P steel.py -- STEELDIR
       (run from the working folder: reads steel_basecolor.png, steel_roughness.png, tex_handle_dark.png from
       pbr_maps.py)

Lessons in here:
- A mirror-polished lid in an HDRI with dark areas (Blender's studio.exr: black curtains) renders black. A product
  look wants a bright world and a few black cards seen only in reflections (visible_camera off): those draw the
  vertical dark bands that read as "steel" on a cylinder. The lid satin (roughness 0.16), the body polished (0.08).
- Black plastic at roughness 0.38 in a bright studio looks grey; 0.5 and specular 0.3.
- The viewport: Material Preview with the scene's white world shows flat grey steel (nothing to reflect); use a
  built-in HDRI there (interior.exr) and keep the cards hidden in the viewport (eye), visible in renders.
- Adjustments are in the images (pbr_maps.py), not in Gamma/Mix nodes: the glTF exporter drops those."""
import bpy, bmesh, math, sys, os
from mathutils import Vector
OUT=os.path.abspath(sys.argv[sys.argv.index('--')+1]); os.makedirs(OUT,exist_ok=True)
WD=os.getcwd(); sc=bpy.context.scene; M=bpy.data.materials
def img(n,noncolor=False):
    im=bpy.data.images.load(f'{WD}/{n}')
    if noncolor: im.colorspace_settings.name='Non-Color'
    return im
def reset(m):
    nt=m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out=nt.nodes.new('ShaderNodeOutputMaterial'); out.location=(500,0)
    b=nt.nodes.new('ShaderNodeBsdfPrincipled'); b.location=(150,0); nt.links.new(b.outputs[0],out.inputs[0])
    return nt,b
def tex(nt,b,image,inp,y,uvmap='photo'):
    uv=nt.nodes.new('ShaderNodeUVMap'); uv.uv_map=uvmap; uv.location=(-600,y)
    t=nt.nodes.new('ShaderNodeTexImage'); t.image=image; t.interpolation='Cubic'; t.extension='EXTEND'; t.location=(-300,y)
    nt.links.new(uv.outputs[0],t.inputs[0]); nt.links.new(t.outputs[0],b.inputs[inp])
def steel(m,rough=0.08,col=(0.72,0.72,0.73),logo=False):
    nt,b=reset(m); b.inputs['Metallic'].default_value=1.0
    if logo:
        tex(nt,b,img('steel_basecolor.png'),'Base Color',150); tex(nt,b,img('steel_roughness.png',True),'Roughness',-150)
    else:
        b.inputs['Base Color'].default_value=(*col,1); b.inputs['Roughness'].default_value=rough
def plastic(m,image=None):
    nt,b=reset(m); b.inputs['Roughness'].default_value=0.5; b.inputs['Specular IOR Level'].default_value=0.3
    if image: tex(nt,b,image,'Base Color',0)
    else: b.inputs['Base Color'].default_value=(0.03,0.032,0.038,1)
steel(M['steel_photo_front'],logo=True); steel(M['steel_photo_back'])
steel(M['steel_bottom'],rough=0.3,col=(0.62,0.62,0.63))
plastic(M['handle_photo'],img('tex_handle_dark.png')); plastic(M['handle_plastic'])
lidm=M.new('stainless_lid'); lidm.use_nodes=True; steel(lidm,rough=0.16)
lo=bpy.data.objects['lid']
for i,ms in enumerate(lo.data.materials):
    if ms and ms.name in ('steel_photo_front','steel_photo_back'): lo.data.materials[i]=lidm
for old,new in [('steel_photo_front','stainless_front_logo'),('steel_photo_back','stainless'),
                ('steel_bottom','stainless_base'),('handle_photo','handle_plastic_detail')]: M[old].name=new
for im in list(bpy.data.images):
    if im.users==0: bpy.data.images.remove(im)
# white product studio: bright world, light floor, black cards seen only in reflections
w=sc.world; nt=w.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
bg=nt.nodes.new('ShaderNodeBackground'); bg.inputs[0].default_value=(0.92,0.92,0.94,1)
nt.links.new(bg.outputs[0],nt.nodes.new('ShaderNodeOutputWorld').inputs[0])
fl=M['floor'].node_tree.nodes['Principled BSDF']; fl.inputs['Base Color'].default_value=(0.8,0.8,0.8,1); fl.inputs['Roughness'].default_value=0.7
blk=M.new('card_black'); blk.use_nodes=True; _,b2=reset(blk); b2.inputs['Base Color'].default_value=(0.005,0.005,0.005,1)
studio=bpy.data.collections['studio']; cards=[]
for nm,(y,x,wd) in {'card_left':(-0.55,0.35,0.25),'card_right':(0.6,0.2,0.18),'card_back':(0.05,-1.0,0.5)}.items():
    me=bpy.data.meshes.new(nm); bm=bmesh.new(); bmesh.ops.create_grid(bm,x_segments=1,y_segments=1,size=0.5); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(nm,me); studio.objects.link(o); me.materials.append(blk)
    o.scale=(wd*2,1.6,1); o.location=(x,y,0.4)
    o.rotation_euler=(Vector((0,0,0.4))-o.location).to_track_quat('Z','Y').to_euler()
    o.visible_camera=False; o.visible_shadow=False; o.visible_diffuse=False; o.visible_volume_scatter=False
    cards.append(o)
for n,e in [('key',12),('fill',4),('rim',8)]: bpy.data.objects[n].data.energy=e
sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'
sc.render.engine='CYCLES'; sc.cycles.samples=96; sc.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='METAL'; prefs.get_devices()
    sc.cycles.device='GPU'
except Exception as ex: print('CPU render:',ex)
sc.render.film_transparent=False
photo_cam=sc.camera
def shot(name,az,el,dist=1.15,lens=50,res=900):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector((0,0.04,0.12))
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=sc.render.resolution_y=res; sc.render.filepath=f'{OUT}/steel_{name}.png'
    bpy.ops.render.render(write_still=True); bpy.data.objects.remove(c); bpy.data.cameras.remove(cd)
sc.camera=photo_cam; sc.render.resolution_x=sc.render.resolution_y=554; sc.render.filepath=f'{OUT}/steel_photo_view.png'
bpy.ops.render.render(write_still=True)
shot('q_front_left',40,22); shot('q_rear_right',-140,25); shot('top',0,70)
shot('handle_close',60,25,dist=0.55); shot('logo_close',5,8,dist=0.35)
sc.camera=photo_cam; sc.render.resolution_x=sc.render.resolution_y=1080; sc.cycles.samples=128
for o in cards: o.hide_set(True)   # in renders only, not in the way in the viewport
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type=='VIEW_3D':
                sp.shading.type='MATERIAL'; sp.shading.use_scene_world=False; sp.shading.use_scene_lights=True
                sp.shading.studio_light='interior.exr'; sp.shading.studiolight_intensity=1.3
model=[o for o in bpy.data.collections['pressure_cooker'].objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in model: o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['pot_body']
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/pressure_cooker_steel.blend')
bpy.ops.export_scene.gltf(filepath=f'{OUT}/pressure_cooker_steel.glb',use_selection=True,export_format='GLB')
