"""Blender: export only the laptop (collection MacBook_Pro_14) of the saved .blend to .glb.
Run: Blender model.blend -b -P export_glb.py -- out.glb"""
import bpy, sys, os
out = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
for o in bpy.context.scene.objects:
    o.select_set(False)
for o in bpy.data.collections["MacBook_Pro_14"].all_objects:
    o.hide_set(False); o.select_set(True)
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_cameras=False,
                          export_lights=False, export_apply=True, export_yup=True)
print("EXPORTED", out, os.path.getsize(out))
