# blender -b -P idr.py : object-ID renders from every photo camera -> id/rN.png (R = 8*index), names in id/names.txt; saves bake/geom.blend
import bpy, sys, os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); os.chdir(HERE)
import geom
geom.clear(); obs=geom.build_all()
os.makedirs('id',exist_ok=True); os.makedirs('bake',exist_ok=True)
open('id/names.txt','w').write('\n'.join(o.name for o in obs))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('bake/geom.blend'))
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=1; sc.cycles.use_denoising=False
sc.cycles.pixel_filter_type='BOX'; sc.cycles.filter_width=0.01; sc.render.film_transparent=True; sc.view_settings.view_transform='Standard'
for i,o in enumerate(obs):
    m=bpy.data.materials.new('id%d'%i); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
    em=nt.nodes.new('ShaderNodeEmission'); out=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0],out.inputs[0])
    v=8*(i+1)/255.0; em.inputs[0].default_value=(v,0.5,0.5,1); o.data.materials.clear(); o.data.materials.append(m)
sc.view_settings.view_transform='Raw'
for k in ['r1','r2','r3','r4']:
    geom.set_camera(k); sc.render.filepath=os.path.abspath('id/%s.png'%k); bpy.ops.render.render(write_still=True)
