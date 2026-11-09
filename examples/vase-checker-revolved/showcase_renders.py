"""showcase renders from real/vazo.blend: the photo's camera (2x) and three views the photo does not show"""
import bpy, math, os, sys
from mathutils import Vector
OUT=os.path.abspath(sys.argv[sys.argv.index('--')+1]); os.makedirs(OUT,exist_ok=True)
sc=bpy.context.scene; sc.cycles.samples=256
sc.view_settings.look='AgX - Punchy'; sc.view_settings.exposure=0.6
sc.camera=bpy.data.objects['foto_kamera']; sc.render.resolution_x=1200; sc.render.resolution_y=1800
sc.render.filepath=f'{OUT}/s_photo_cam.png'; bpy.ops.render.render(write_still=True)
def shot(name,az,el,dist,t=(0,0,0.15)):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=50
    a=math.radians(az); e=math.radians(el); t=Vector(t)
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=900; sc.render.resolution_y=1200; sc.render.filepath=f'{OUT}/s_{name}.png'
    bpy.ops.render.render(write_still=True)
shot('three_quarter',50,15,0.62); shot('back',180,12,0.62); shot('top',20,62,0.62,t=(0,0,0.12))
