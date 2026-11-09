# Blender: tidy the built scene (from build.py) and save a packed .blend; optionally export the aircraft as .glb.
# blender -b -P build.py -- final|match x  (with NORENDER=1 DELIVER=path.blend [GLB=path.glb])
import bpy, os, math
from mathutils import Vector
def tidy_and_save(blend, glb=None, name='ucak_737'):
    sc = bpy.context.scene; cam = sc.objects.get('photo_cam')
    for o in [o for o in sc.objects if o.type == 'CAMERA' and o != cam]: bpy.data.objects.remove(o)
    mc = bpy.data.collections.new(name); sc.collection.children.link(mc)
    st = bpy.data.collections.new('studio'); sc.collection.children.link(st)
    root = bpy.data.objects.new(name, None); root.empty_display_size = 2; mc.objects.link(root)
    for o in list(sc.objects):
        if o is root: continue
        tgt = st if (o.type in ('LIGHT', 'CAMERA') or o.name == 'ground') else mc
        for c in list(o.users_collection): c.objects.unlink(o)
        tgt.objects.link(o)
        if tgt is mc and o is not root: o.parent = root
    if cam: cam.data.display_size = 1.0; sc.camera = cam
    for o in sc.objects: o.select_set(False)
    root.select_set(True); bpy.context.view_layer.objects.active = root
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type != 'VIEW_3D': continue
            sp = area.spaces[0]; sp.clip_start = 0.05; sp.clip_end = 3000
            sp.overlay.show_extras = False; sp.shading.type = 'MATERIAL'
            r3 = sp.region_3d; r3.view_location = (0, 0, 4); r3.view_distance = 55; r3.view_perspective = 'PERSP'
            r3.view_rotation = (Vector((48, 42, 18)) - Vector((0, 0, 4))).to_track_quat('Z', 'Y')
    old = bpy.data.collections.get('Collection')
    if old and not old.objects: bpy.data.collections.remove(old)
    for i in bpy.data.images:
        if i.source == 'FILE': i.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
    if glb:
        for o in [o for o in sc.objects if o.type in ('LIGHT', 'CAMERA') or o.name == 'ground']: bpy.data.objects.remove(o)
        bpy.ops.export_scene.gltf(filepath=os.path.abspath(glb), export_format='GLB', export_cameras=False, export_apply=True)
