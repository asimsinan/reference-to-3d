# blender -b -P lightpass.py -- frames : linear light passes (sky, 16 soft suns) with the final materials -> lp/<frame>_<pass>.exr
import bpy, sys, os, json
from math import radians, cos, sin
from mathutils import Vector
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); os.chdir(HERE)
import geom, rig, final
FR=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['r2','r3','r4']
geom.clear(); obs=geom.build_all(); final.materials(obs); rig.gpu(); g=rig.light(HERE)
sc=bpy.context.scene; sc.cycles.samples=160; sc.cycles.use_denoising=False; sc.cycles.filter_width=1.0; sc.view_settings.view_transform='Raw'; sc.view_settings.exposure=0
sc.render.image_settings.file_format='OPEN_EXR'; sc.render.image_settings.color_depth='32'; sc.render.film_transparent=True
os.makedirs('lp',exist_ok=True)
w=sc.world; nt=w.node_tree; bgs=[n for n in nt.nodes if n.type=='BACKGROUND']
sd=bpy.data.lights.new('S','SUN'); so=bpy.data.objects.new('S',sd); sc.collection.objects.link(so); sd.angle=radians(25); sd.energy=3.0
SUNS=[(az,el) for el in (25,55) for az in range(0,360,45)]
json.dump(SUNS,open('lp/suns.json','w'))
for k in FR:
    geom.set_camera(k)
    for i,ae in enumerate([None]+SUNS):
        if ae is None:
            so.hide_render=True
            for b in bgs: b.inputs[1].default_value=1.0
        else:
            so.hide_render=False
            for b in bgs: b.inputs[1].default_value=0.0
            az,el=ae; d=Vector((cos(radians(az))*cos(radians(el)),sin(radians(az))*cos(radians(el)),sin(radians(el)))); so.rotation_euler=d.to_track_quat('Z','Y').to_euler()
        sc.render.filepath=os.path.abspath('lp/%s_%02d.exr'%(k,i)); bpy.ops.render.render(write_still=True)
