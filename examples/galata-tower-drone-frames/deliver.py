# blender -b out/final_work.blend -P deliver.py -- [photo] : tidy, metres, pack -> galata_kulesi.blend / .glb
import bpy, os, sys, json
from mathutils import Vector
HERE=os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath),'..')); os.chdir(HERE)
P=json.load(open('params.json')); s=P['s']; zg=P['zg']
PHOTO='photo' in sys.argv
for o in [o for o in bpy.data.objects if o.type=='CAMERA']: bpy.data.objects.remove(o)
if PHOTO:
    names=open('bake/names.txt').read().split()
    for o in bpy.data.objects:
        if o.type!='MESH' or o.name=='ground': continue
        m=bpy.data.materials.new('foto_'+o.name); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
        em=nt.nodes.new('ShaderNodeEmission'); out=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0],out.inputs[0])
        if o.name in names:
            t=nt.nodes.new('ShaderNodeTexImage'); t.image=bpy.data.images.load(os.path.abspath('tex/%s_photo.png'%o.name)); nt.links.new(t.outputs[0],em.inputs[0])
        else: em.inputs[0].default_value=(0.004,0.004,0.004,1)
        o.data.materials.clear(); o.data.materials.append(m)
root=bpy.data.objects.new('GalataKulesi',None); bpy.context.scene.collection.objects.link(root)
tower=bpy.data.collections.new('Galata Kulesi'); env=bpy.data.collections.new('Ortam'); bpy.context.scene.collection.children.link(tower); bpy.context.scene.collection.children.link(env)
for o in list(bpy.data.objects):
    if o.type=='MESH' and o.name!='ground':
        for c in o.users_collection: c.objects.unlink(o)
        tower.objects.link(o); o.parent=root
for c in root.users_collection: c.objects.unlink(root)
tower.objects.link(root)
root.scale=(s,s,s); root.location=(0,0,-zg*s)
g=bpy.data.objects.get('ground')
if g:
    for c in g.users_collection: c.objects.unlink(g)
    env.objects.link(g); g.location=(0,0,0); g.scale=(0.25*s,0.25*s,1); g.visible_camera=True
    g.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.2,0.17,0.16,1)
for o in [o for o in bpy.data.objects if o.type=='LIGHT']:
    for c in o.users_collection: c.objects.unlink(o)
    env.objects.link(o)
bpy.context.view_layer.update()
# camera for F12 + viewport framing
cd=bpy.data.cameras.new('Kamera'); cam=bpy.data.objects.new('Kamera',cd); env.objects.link(cam); bpy.context.scene.camera=cam
cam.location=Vector((95,-55,45)); cam.rotation_euler=(Vector((0,0,30))-cam.location).to_track_quat('-Z','Y').to_euler(); cd.lens=45; cd.clip_end=2000
sc=bpy.context.scene; sc.render.resolution_x=1080; sc.render.resolution_y=1620; sc.view_settings.exposure=0
for x in bpy.context.selected_objects: x.select_set(False)
root.select_set(True); bpy.context.view_layer.objects.active=root
for scr in bpy.data.screens:
    for a in scr.areas:
        if a.type=='VIEW_3D':
            for sp in a.spaces:
                if sp.type=='VIEW_3D':
                    sp.shading.type='MATERIAL'; r=sp.region_3d; r.view_location=Vector((0,0,32)); r.view_distance=110
                    from mathutils import Euler; r.view_rotation=Euler((1.25,0,0.9)).to_quaternion(); sp.clip_end=5000
name='galata_kulesi_foto' if PHOTO else 'galata_kulesi'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('deliver/%s.blend'%name))
if not PHOTO:
    if g: g.hide_set(True); g.select_set(False)
    for o in env.objects: o.select_set(False)
    for o in tower.objects: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath('deliver/%s.glb'%name),use_selection=True,export_apply=True)
print('delivered',name)
