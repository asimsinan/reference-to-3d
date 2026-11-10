# blender -b bake/geom.blend -P idr.py : object-index render from each photo camera -> id/rN.png (R = index+1), id/names.txt
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); os.chdir(os.path.dirname(os.path.abspath(__file__)))
import geom
obs = sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 1; sc.cycles.device = 'CPU'
sc.cycles.pixel_filter_type = 'BOX'; sc.cycles.filter_width = 0.01; sc.cycles.use_denoising = False
sc.view_settings.view_transform = 'Raw'; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'; sc.render.film_transparent = True
for k, o in enumerate(obs):
    o.hide_render = False
    m = bpy.data.materials.new('id'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    v = (k + 1) * 8 / 255.0; em.inputs[0].default_value = (v, v, v, 1); nt.links.new(em.outputs[0], out.inputs[0])
    if o.name == 'sea':
        nt.nodes.clear(); h = nt.nodes.new('ShaderNodeHoldout'); out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(h.outputs[0], out.inputs[0])
    o.data.materials.clear(); o.data.materials.append(m)
for o in [o for o in bpy.data.objects if o.type == 'CAMERA']: bpy.data.objects.remove(o)
os.makedirs('id', exist_ok=True); open('id/names.txt', 'w').write('\n'.join(o.name for o in obs))
for i in range(1, 7):
    geom.set_camera('r%d' % i); sc.render.filepath = os.path.abspath('id/r%d.png' % i); bpy.ops.render.render(write_still=True)
