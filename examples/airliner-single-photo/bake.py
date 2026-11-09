# Blender: bake every part's world position and normal into its UV space (float EXR), and render the photo
# camera's depth. numpy (texbuild.py) then projects the photo onto the texels that the camera sees.
# blender -b -P bake.py
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import importlib, build, geom, params
importlib.reload(geom); importlib.reload(params)

def texsize(name):
    k = name.split('_')[0]
    return {'fuselage': (4096, 2048), 'wing': (2048, 1024), 'htail': (1024, 512), 'fin': (1024, 1024),
            'nacelle': (1024, 1024), 'belly': (1024, 512), 'duct': (512, 512), 'fan': (512, 512), 'spinner': (256, 256)}.get(k, (256, 256))

def ensure_uv(o):
    if not o.data.uv_layers:
        bpy.context.view_layer.objects.active = o
        for x in bpy.context.selected_objects: x.select_set(False)
        o.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(island_margin=0.02); bpy.ops.object.mode_set(mode='OBJECT')

def bake_attr(o, attr, size, path):
    m = bpy.data.materials.new('bk'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    geo = nt.nodes.new('ShaderNodeNewGeometry'); em = nt.nodes.new('ShaderNodeEmission')
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(geo.outputs['Position' if attr == 'P' else 'Normal'], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    img = bpy.data.images.new(o.name + attr, size[0], size[1], float_buffer=True, alpha=True)
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img; nt.nodes.active = tn
    o.data.materials.clear(); o.data.materials.append(m)
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    # alpha 0 where nothing is baked
    img.generated_color = (0, 0, 0, 0)
    img.colorspace_settings.name = 'Non-Color'
    bpy.ops.object.bake(type='EMIT', margin=3, use_clear=True)
    img.filepath_raw = path; img.file_format = 'OPEN_EXR'; img.save()

if __name__ == '__main__':
    build.clear()
    P = params.params()
    obs = geom.build_all(P)
    cam = build.set_camera()
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 1; sc.cycles.device = 'CPU'
    bpy.context.view_layer.update()
    # apply modifiers / transforms so baked positions are world positions
    for o in obs:
        for x in bpy.context.selected_objects: x.select_set(False)
        o.select_set(True); bpy.context.view_layer.objects.active = o
        if o.modifiers:
            for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        ensure_uv(o)
    os.makedirs('bake', exist_ok=True)
    names = []
    for o in obs:
        sz = texsize(o.name)
        bake_attr(o, 'P', sz, os.path.abspath('bake/%s_P.exr' % o.name))
        bake_attr(o, 'N', sz, os.path.abspath('bake/%s_N.exr' % o.name))
        names.append(o.name)
    open('bake/names.txt', 'w').write('\n'.join(names))
    # depth from the photo camera (camera-space distance along the view axis), no AA
    m = bpy.data.materials.new('depth'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    geo = nt.nodes.new('ShaderNodeNewGeometry'); vt = nt.nodes.new('ShaderNodeVectorTransform')
    vt.vector_type = 'POINT'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); neg = nt.nodes.new('ShaderNodeMath'); neg.operation = 'ABSOLUTE'
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(geo.outputs['Position'], vt.inputs[0]); nt.links.new(vt.outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs['Z'], neg.inputs[0]); nt.links.new(neg.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
    for o in obs: o.data.materials.clear(); o.data.materials.append(m)
    sc.cycles.pixel_filter_type = 'BOX'; sc.cycles.filter_width = 0.01
    sc.render.film_transparent = True; sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
    sc.render.filepath = os.path.abspath('bake/depth.exr')
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('bake/baked_geom.blend'))
