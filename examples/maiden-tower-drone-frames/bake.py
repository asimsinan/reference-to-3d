# blender -b -P bake.py : world position + normal per texel for every part (EXR), depth from every photo camera
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); os.chdir(os.path.dirname(os.path.abspath(__file__)))
import geom
SIZE = {'terrace': 2048, 'fort': 2048, 'shaft': 1024, 'quay': 1024, 'rocks': 2048, 'annex': 1024, 'annex_roof': 1024, 'merlons': 1024,
        'room': 1024, 'dome': 1024, 'parapet': 2048, 'court': 512, 'corbel': 512, 'balcony': 512, 'beacon': 512, 'cornice': 512, 'sea': 64}
SKIP = ('flag', 'balcony_rail', 'ubalcony_rail', 'beacon_cage', 'sea', 'boulders')
def ensure_uv(o):
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.01); bpy.ops.object.mode_set(mode='OBJECT')
def bake_attr(o, attr, size, path):
    m = bpy.data.materials.new('bk'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    geo = nt.nodes.new('ShaderNodeNewGeometry'); em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(geo.outputs['Position' if attr == 'P' else 'True Normal'], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
    img = bpy.data.images.new(o.name + attr, size, size, float_buffer=True, alpha=True)
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img; nt.nodes.active = tn
    o.data.materials.clear(); o.data.materials.append(m)
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    img.generated_color = (0, 0, 0, 0); img.colorspace_settings.name = 'Non-Color'
    bpy.ops.object.bake(type='EMIT', margin=2, use_clear=True)
    img.filepath_raw = path; img.file_format = 'OPEN_EXR'; img.save()
geom.clear(); obs = geom.build_all()
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 1; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = False
os.makedirs('bake', exist_ok=True); names = []
for o in obs:
    if o.name in SKIP: continue
    ensure_uv(o); sz = SIZE.get(o.name, 256)
    bake_attr(o, 'P', sz, os.path.abspath('bake/%s_P.exr' % o.name)); bake_attr(o, 'N', sz, os.path.abspath('bake/%s_N.exr' % o.name)); names.append(o.name)
open('bake/names.txt', 'w').write('\n'.join(names))
m = bpy.data.materials.new('depth'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
geo = nt.nodes.new('ShaderNodeNewGeometry'); vt = nt.nodes.new('ShaderNodeVectorTransform'); vt.vector_type = 'POINT'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
sep = nt.nodes.new('ShaderNodeSeparateXYZ'); neg = nt.nodes.new('ShaderNodeMath'); neg.operation = 'ABSOLUTE'
em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(geo.outputs['Position'], vt.inputs[0]); nt.links.new(vt.outputs[0], sep.inputs[0]); nt.links.new(sep.outputs['Z'], neg.inputs[0]); nt.links.new(neg.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
for o in obs:
    o.data.materials.clear(); o.data.materials.append(m)
    if o.name in ('flag',): o.hide_render = True
sc.cycles.pixel_filter_type = 'BOX'; sc.cycles.filter_width = 0.01; sc.render.film_transparent = True; sc.view_settings.view_transform = 'Raw'
sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
for i in range(1, 7):
    geom.set_camera('r%d' % i); sc.render.filepath = os.path.abspath('bake/depth_r%d.exr' % i); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('bake/geom.blend'))
