import bpy, sys, os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); os.chdir(HERE)
import geom
FR=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['r4']
geom.clear(); obs=geom.build_all()
sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.light='STUDIO'; sc.display.shading.color_type='SINGLE'
sc.display.shading.show_cavity=True; sc.render.film_transparent=True
for k in FR:
    geom.set_camera(k); sc.render.filepath=os.path.abspath('out/clay_%s.png'%k); bpy.ops.render.render(write_still=True)
