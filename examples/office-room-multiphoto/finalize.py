"""Finish the built room: a camera at the door, viewport framing, packed .blend and a glTF for the walk viewer.
  Blender -b oda_build.blend -P finalize.py -- OUT.blend OUT.glb
"""
import math, os, sys
import bpy
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
sc = bpy.context.scene
cd = bpy.data.cameras.new('Kamera'); cd.lens = 16; cd.clip_start = 0.02
cam = bpy.data.objects.new('Kamera koridordan', cd); bpy.data.collections['Lights'].objects.link(cam)
eye, at = Vector((0.95, 6.95, 1.6)), Vector((0.75, 0.0, 1.0))
fwd = (at - eye).normalized(); right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd)
cam.matrix_world = Matrix.Translation(eye) @ Matrix((right, up, -fwd)).transposed().to_4x4()
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
for o in bpy.data.objects: o.select_set(False)
bpy.data.objects['Oda'].select_set(True); bpy.context.view_layer.objects.active = bpy.data.objects['Oda']
for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type == 'VIEW_3D':
            for sp in area.spaces:
                if sp.type == 'VIEW_3D':
                    sp.shading.type = 'MATERIAL'; sp.shading.use_scene_lights = True; sp.shading.use_scene_world = True
                    sp.overlay.show_overlays = True; sp.overlay.show_extras = False
                    sp.region_3d.view_perspective = 'CAMERA'; sp.lock_camera = False
                    sp.clip_start = 0.02
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=argv[0], compress=True)
# glTF: meshes only (the viewer lights the room itself); modifiers applied
for c in ('Lights',):
    bpy.data.collections[c].hide_render = False
bpy.ops.export_scene.gltf(filepath=argv[1], export_format='GLB', use_selection=False, export_apply=True,
                          export_lights=False, export_cameras=False, export_image_format='AUTO', export_jpeg_quality=88)
print('done', argv)
