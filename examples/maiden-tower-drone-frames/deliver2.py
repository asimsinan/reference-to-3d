# blender -b out/final_work.blend -P deliver2.py : tidy scene, scale to metres (doors 2.1 m), pack, save .blend; export .glb
import bpy, os
from mathutils import Vector
S = 1.05                                   # model units -> metres: both doors read on r1 are 2.0 units high, doors ~2.1 m
for o in [o for o in bpy.data.objects if o.type == 'CAMERA']: bpy.data.objects.remove(o)
sc = bpy.context.scene; sc.view_settings.exposure = 0
cm = bpy.data.collections.new('Kiz Kulesi'); cs = bpy.data.collections.new('Sahne (gunes, deniz)')
sc.collection.children.link(cm); sc.collection.children.link(cs)
root = bpy.data.objects.new('KizKulesi', None); cm.objects.link(root); root.empty_display_size = 5
for o in list(bpy.data.objects):
    if o is root: continue
    for c in list(o.users_collection): c.objects.unlink(o)
    if o.type == 'MESH' and o.name != 'sea':
        cm.objects.link(o); o.parent = root
    else:
        cs.objects.link(o)
root.scale = (S, S, S)
sea = bpy.data.objects['sea']; sea.scale = (S, S, S)
sun = bpy.data.objects.get('Sun')
if sun: sun.location = sun.location * S
# a camera for F12 renders, framed like photo r5
cd = bpy.data.cameras.new('Kamera'); co = bpy.data.objects.new('Kamera', cd); cs.objects.link(co); sc.camera = co
co.location = Vector((-14, -95, 42)) * S; d = Vector((0, -2, 8)) * S - co.location; co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); cd.lens = 50; cd.clip_end = 5000
sc.render.resolution_x = 1920; sc.render.resolution_y = 1280; sc.cycles.samples = 128
# viewport: material preview, framed on the tower
for scr in bpy.data.screens:
    for a in scr.areas:
        if a.type == 'VIEW_3D':
            for sp in a.spaces:
                if sp.type == 'VIEW_3D':
                    sp.shading.type = 'MATERIAL'; sp.clip_end = 5000
                    r3 = sp.region_3d; r3.view_location = Vector((0, -3, 9)) * S; r3.view_distance = 95 * S
                    r3.view_rotation = (Vector((0.9, -2.2, 1.1))).to_track_quat('Z', 'Y')
for o in bpy.context.selected_objects: o.select_set(False)
root.select_set(True); bpy.context.view_layer.objects.active = root
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('out/kiz_kulesi.blend'))
for o in bpy.data.objects: o.select_set(o.name in cm.all_objects.keys())
bpy.ops.export_scene.gltf(filepath=os.path.abspath('out/kiz_kulesi.glb'), use_selection=True, export_yup=True)
print('saved')
