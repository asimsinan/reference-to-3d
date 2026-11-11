import bpy, os, sys
from math import radians, cos, sin
from mathutils import Vector
os.chdir(os.path.dirname(bpy.data.filepath)+'/..')
pre=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'x'
sc=bpy.context.scene; sc.render.resolution_x=800; sc.render.resolution_y=900; sc.view_settings.exposure=0; sc.cycles.samples=64
cd=bpy.data.cameras.new('tv'); cam=bpy.data.objects.new('tv',cd); sc.collection.objects.link(cam); sc.camera=cam; cd.lens=50; cd.clip_end=3000
for th in (100,160,220,280):
    t=radians(th); cam.location=Vector((42*cos(t),42*sin(t),22)); cam.rotation_euler=(Vector((0,0,11))-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=os.path.abspath('out/tv_%s_%d.png'%(pre,th)); bpy.ops.render.render(write_still=True)
