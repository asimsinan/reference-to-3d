# blender -b out/final_work.blend -P backviews.py -- PREFIX : close views round the unseen side -> out/bv_PREFIX_<deg>.png
import bpy, os, sys
from math import radians, cos, sin
from mathutils import Vector
os.chdir(os.path.dirname(bpy.data.filepath)+'/..')
pre=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'x'
sc=bpy.context.scene; sc.render.resolution_x=600; sc.render.resolution_y=900; sc.view_settings.exposure=0; sc.cycles.samples=64
cd=bpy.data.cameras.new('bv'); cam=bpy.data.objects.new('bv',cd); sc.collection.objects.link(cam); sc.camera=cam; cd.lens=50; cd.clip_end=3000
for th in (60,100,140,180,220,260,300):
    t=radians(th); cam.location=Vector((55*cos(t),55*sin(t),-12)); cam.rotation_euler=(Vector((0,0,-14))-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=os.path.abspath('out/bv_%s_%d.png'%(pre,th)); bpy.ops.render.render(write_still=True)
