# blender -b out/final_work.blend -P novel.py : close-ups from viewpoints no photo has -> out/nv_*.png, g/novel.jpg
import bpy, os, json, math
from mathutils import Vector
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sc = bpy.context.scene; sc.render.resolution_x = 1200; sc.render.resolution_y = 800; sc.cycles.samples = 64; sc.view_settings.exposure = 0
for o in [o for o in bpy.data.objects if o.type == 'CAMERA']: bpy.data.objects.remove(o)
cd = bpy.data.cameras.new('nv'); co = bpy.data.objects.new('nv', cd); sc.collection.objects.link(co); sc.camera = co; cd.clip_end = 3000
SH = {'quay_level': ((24, -10, 1.6), (0, 0, 6), 24), 'west_low': ((-34, 2, 3), (-8, -3, 4), 28), 'dome_close': ((9, -9, 23), (0, 0, 19.5), 30),
      'top_down': ((0.5, -3, 75), (0, -3, 0), 32), 'annex_porch': ((-4, 22, 4), (-4, 7, 2.5), 30), 'south_east': ((30, -40, 14), (0, -6, 6), 30)}
os.makedirs('out', exist_ok=True)
for n, (pos, tgt, lens) in SH.items():
    co.location = pos; d = Vector(tgt) - Vector(pos); co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens
    sc.render.filepath = os.path.abspath('out/nv_%s.png' % n); bpy.ops.render.render(write_still=True)
