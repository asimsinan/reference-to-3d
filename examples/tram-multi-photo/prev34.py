# quick solid previews of tram 34 geometry: blender -b -P prev34.py
import bpy, sys, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
import geom34
obs = geom34.build_all(interior=True)
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'RANDOM'
sc.display.shading.show_cavity = True; sc.render.resolution_x, sc.render.resolution_y = 900, 600
cd = bpy.data.cameras.new('c'); co = bpy.data.objects.new('c', cd); sc.collection.objects.link(co); sc.camera = co
V = {'back2': ((-9, -2.5, 2.2), (-2, 0, 1.6), 30), 'side': ((0, -14, 1.8), (-0.2, 0, 1.6), 30), 'ext': ((9, 7, 3.5), (0, 0, 1.6), 30), 'roof': ((-8, 6, 9), (0, 0, 2.5), 35), 'saloon': ((1.65, 0.0, 1.75), (-2, 0, 1.45), 16), 'cab': ((2.3, 0.0, 1.95), (3.6, 0, 1.2), 18), 'back': ((-10, -6, 2.5), (-0.4, 0, 1.6), 30)}
for n, (p, t, lens) in V.items():
    if os.environ.get('VV') and n not in os.environ['VV'].split(','): continue
    co.location = p; co.rotation_euler = (Vector(t) - Vector(p)).to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens
    sc.render.filepath = os.path.abspath('out/p34_%s.png' % n); bpy.ops.render.render(write_still=True)
print('PREV OK', len(obs))
