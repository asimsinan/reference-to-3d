"""Showcase renders from kupa_porselen.blend with a transparent film (the HDRI lights, the camera does not see it).
usage: Blender -b porselen/kupa_porselen.blend -P showcase_renders.py -- OUTDIR"""
import bpy, math, os, sys
from mathutils import Vector
OUT=os.path.abspath(sys.argv[sys.argv.index('--')+1]); os.makedirs(OUT,exist_ok=True)
sc=bpy.context.scene; sc.render.film_transparent=True; sc.cycles.samples=256
sc.render.image_settings.color_mode='RGBA'
cam=bpy.data.objects['photo_cam']; sc.camera=cam; sc.render.resolution_x=1060; sc.render.resolution_y=1414
cam.data.shift_x=30/1060; cam.data.shift_y=-292.5/1060   # the photo crop x 250-1310, y 586-1999: principal point left of and above its centre
cam.data.lens=cam.data.lens*1500/1060
sc.render.filepath=f'{OUT}/s_photo_cam.png'; bpy.ops.render.render(write_still=True)
def shot(name,az,el,dist,t=(0,0.008,0.058)):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=50
    a=math.radians(az); e=math.radians(el); t=Vector(t)
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=900; sc.render.resolution_y=1200; sc.render.filepath=f'{OUT}/s_{name}.png'
    bpy.ops.render.render(write_still=True)
if '--photo-only' not in sys.argv:
    shot('rear_left',-135,18,0.36); shot('handle_side',95,15,0.36); shot('top',15,62,0.36)
