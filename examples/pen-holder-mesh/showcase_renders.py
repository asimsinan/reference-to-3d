"""Showcase renders of the real-material model: the photo's camera (film transparent, to composite over the photo)
and three views on a transparent film. usage: Blender -b final/kalemlik_pbr.blend -P scripts/showcase_renders.py -- OUTDIR"""
import bpy, math, sys, os
from mathutils import Vector
OUT=os.path.abspath(sys.argv[sys.argv.index('--')+1]); os.makedirs(OUT,exist_ok=True); sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=128; sc.cycles.use_denoising=True
sc.render.film_transparent=True; sc.render.image_settings.color_mode='RGBA'
bpy.data.objects['table'].hide_render=False
cam=bpy.data.objects['photo_cam']; sc.camera=cam; sc.render.resolution_x=1500; sc.render.resolution_y=2000
sc.render.filepath=f'{OUT}/sc_photo_cam.png'; bpy.ops.render.render(write_still=True)
def shot(name,az,el,dist=0.36,lens=50,res=1000):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector((0,0,0.065))
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=sc.render.resolution_y=res; sc.render.filepath=f'{OUT}/sc_{name}.png'; bpy.ops.render.render(write_still=True)
shot('q_right',55,20); shot('q_rear',-130,25); shot('top',35,62)
