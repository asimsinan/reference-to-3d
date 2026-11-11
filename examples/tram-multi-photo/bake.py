# blender -b -P bake.py : apply modifiers, smart-UV every part, bake world position/normal into UV space (EXR),
# render camera-space depth from every photo camera. -> bake/<obj>_P.exr, _N.exr, depth{k}.exr, bake/objs.json, bake/baked.blend
import bpy, sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
import geom, rig
V34 = bool(os.environ.get('V34'))
BK = os.environ.get('BK', 'bake')
if V34: import geom34
DENS = float(os.environ.get('DENS', '260'))
obs = geom34.build_all(interior=True) if V34 else geom.build_all()
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 1; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = False
def sel(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
info = {}
for o in obs:
    sel(o)
    for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    area = sum(p.area for p in o.data.polygons)
    n = int(min(4096, max(64, 2 ** round(math.log2(max(1e-6, math.sqrt(area) * DENS * 1.5))))))
    info[o.name] = {'size': n, 'area': area}
def bake_attr(o, attr, n, path):
    m = bpy.data.materials.new('bk'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    geo = nt.nodes.new('ShaderNodeNewGeometry'); em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(geo.outputs['Position' if attr == 'P' else 'Normal'], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
    img = bpy.data.images.new(o.name + attr, n, n, float_buffer=True, alpha=True)
    img.generated_color = (0, 0, 0, 0); img.colorspace_settings.name = 'Non-Color'
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img; nt.nodes.active = tn
    o.data.materials.clear(); o.data.materials.append(m); sel(o)
    bpy.ops.object.bake(type='EMIT', margin=2, use_clear=True)
    img.filepath_raw = path; img.file_format = 'OPEN_EXR'; img.save(); bpy.data.images.remove(img); bpy.data.materials.remove(m)
os.makedirs(BK, exist_ok=True)
for o in obs:
    n = info[o.name]['size']
    bake_attr(o, 'P', n, os.path.abspath(BK + '/%s_P.exr' % o.name)); bake_attr(o, 'N', n, os.path.abspath(BK + '/%s_N.exr' % o.name))
json.dump(info, open(BK + '/objs.json', 'w'), indent=0)
if os.environ.get('AO', '1') == '1':
    sc.cycles.samples = 24
    for o in obs:
        n = info[o.name]['size']
        m = bpy.data.materials.new('ao'); m.use_nodes = True; nt = m.node_tree
        img = bpy.data.images.new(o.name + 'AO', n, n, float_buffer=True, alpha=True); img.colorspace_settings.name = 'Non-Color'
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img; nt.nodes.active = tn
        o.data.materials.clear(); o.data.materials.append(m); sel(o)
        bpy.ops.object.bake(type='AO', margin=2, use_clear=True)
        img.filepath_raw = os.path.abspath(BK + '/%s_AO.exr' % o.name); img.file_format = 'OPEN_EXR'; img.save(); bpy.data.images.remove(img)
    sc.cycles.samples = 1
# depth per photo camera
m = bpy.data.materials.new('depth'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
geo = nt.nodes.new('ShaderNodeNewGeometry'); vt = nt.nodes.new('ShaderNodeVectorTransform'); vt.vector_type = 'POINT'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
sep = nt.nodes.new('ShaderNodeSeparateXYZ'); ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'
em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(geo.outputs['Position'], vt.inputs[0]); nt.links.new(vt.outputs[0], sep.inputs[0]); nt.links.new(sep.outputs['Z'], ab.inputs[0])
nt.links.new(ab.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
for o in obs: o.data.materials.clear(); o.data.materials.append(m)
sc.cycles.pixel_filter_type = 'BOX'; sc.cycles.filter_width = 0.01; sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.render.dither_intensity = 0
sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
for k in rig.J['cams']:
    rig.photo_camera(k); sc.render.filepath = os.path.abspath(BK + '/depth%s.exr' % k); bpy.ops.render.render(write_still=True)
for o in obs: o.data.materials.clear()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(BK + '/baked.blend'))
print('BAKED', len(obs))
