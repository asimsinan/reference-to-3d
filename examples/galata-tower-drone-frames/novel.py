# blender -b out/final_work.blend -P novel.py : viewpoints no frame has -> out/nv_*.png
import bpy, os
from math import radians, cos, sin
from mathutils import Vector
os.chdir(os.path.dirname(bpy.data.filepath)+'/..')
import json; P=json.load(open('params.json'))
sc=bpy.context.scene; sc.render.resolution_x=900; sc.render.resolution_y=1200; sc.view_settings.exposure=0; sc.cycles.samples=96
cd=bpy.data.cameras.new('nv'); cam=bpy.data.objects.new('nv',cd); sc.collection.objects.link(cam); sc.camera=cam
def shot(name,pos,target,lens=35):
    cd.lens=lens; cd.shift_x=cd.shift_y=0; cd.sensor_fit='AUTO'; cam.location=Vector(pos)
    cam.rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler(); cd.clip_end=3000
    sc.render.filepath=os.path.abspath('out/nv_%s.png'%name); bpy.ops.render.render(write_still=True)
zg=P['zg']
def at(th,d,h): t=radians(th); return (d*cos(t),d*sin(t),h)
shot('back',at(180,120,40),(0,0,-6),50)
shot('side',at(95,120,35),(0,0,-6),50)
shot('ground',at(-20,32,zg+1.7),(0,0,5),24)
shot('balcony',at(-30,22,10),(0,0,9),35)
shot('top',at(10,25,60),(0,0,20),35)
