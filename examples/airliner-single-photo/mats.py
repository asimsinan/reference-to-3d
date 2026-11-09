# Materials for the match (photo emission) and final (real) builds.
import bpy, json, os, math
TEXUSE = {'fuselage': ('fuselage', False), 'wing_L': ('wing', False), 'wing_R': ('wing', False),
          'htail_L': ('htail', False), 'htail_R': ('htail', False), 'fin': ('fin', False),
          'nacelle_L': ('nacelle', False), 'nacelle_R': ('nacelle', True), 'duct_L': ('duct', False),
          'duct_R': ('duct', True), 'spinner_L': ('spinner', False), 'fan_L': ('fan', False), 'fan_R': ('fan', False), 'spinner_R': ('spinner', False),
          'belly_fairing': ('belly', False)}

def uv_image_node(nt, path, mirror, noncolor=False):
    img = bpy.data.images.load(os.path.abspath(path), check_existing=True)
    if noncolor: img.colorspace_settings.name = 'Non-Color'
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img; tn.interpolation = 'Cubic'; tn.extension = 'REPEAT'
    if mirror:
        uv = nt.nodes.new('ShaderNodeUVMap'); mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Location'].default_value = (0, 0.5, 0); mp.inputs['Scale'].default_value = (1, -1, 1)
        nt.links.new(uv.outputs[0], mp.inputs[0]); nt.links.new(mp.outputs[0], tn.inputs[0])
    return tn

def proj_node(nt, cam):
    """photo projected through the solved camera (exact, per pixel)."""
    geo = nt.nodes.new('ShaderNodeNewGeometry'); R = cam['R']; t = cam['t']
    comps = []
    for k in range(3):
        d = nt.nodes.new('ShaderNodeVectorMath'); d.operation = 'DOT_PRODUCT'
        d.inputs[1].default_value = R[k]; nt.links.new(geo.outputs['Position'], d.inputs[0])
        a = nt.nodes.new('ShaderNodeMath'); a.operation = 'ADD'; a.inputs[1].default_value = t[k]
        nt.links.new(d.outputs['Value'], a.inputs[0]); comps.append(a)
    def div_aff(num, scale, off):
        dv = nt.nodes.new('ShaderNodeMath'); dv.operation = 'DIVIDE'
        nt.links.new(num.outputs[0], dv.inputs[0]); nt.links.new(comps[2].outputs[0], dv.inputs[1])
        ma = nt.nodes.new('ShaderNodeMath'); ma.operation = 'MULTIPLY_ADD'
        nt.links.new(dv.outputs[0], ma.inputs[0]); ma.inputs[1].default_value = scale; ma.inputs[2].default_value = off
        return ma
    u = div_aff(comps[0], cam['f'] / cam['W'], 0.5)
    v = div_aff(comps[1], -cam['f'] / cam['H'], 0.5)
    cb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(u.outputs[0], cb.inputs[0]); nt.links.new(v.outputs[0], cb.inputs[1])
    img = bpy.data.images.load(os.path.abspath('ref.jpg'), check_existing=True)
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img; tn.extension = 'EXTEND'; tn.interpolation = 'Cubic'
    nt.links.new(cb.outputs[0], tn.inputs[0])
    return tn

def match_material(o, cam):
    m = bpy.data.materials.new('match_' + o.name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    if os.path.exists('tex/own_%s.png' % o.name):
        tn = uv_image_node(nt, 'tex/own_%s.png' % o.name, False)
    elif o.name in TEXUSE:
        g, mir = TEXUSE[o.name]; tn = uv_image_node(nt, 'tex/%s_photo.png' % g, mir)
    else:
        tn = proj_node(nt, cam)
    nt.links.new(tn.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
    o.data.materials.clear(); o.data.materials.append(m)

def principled(name, base=(0.8, 0.8, 0.8), rough=0.3, metal=0.0, spec=0.5, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if 'Specular IOR Level' in b.inputs: b.inputs['Specular IOR Level'].default_value = spec
    if coat and 'Coat Weight' in b.inputs: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.08
    return m, nt, b

def final_material(o, cal):
    name = o.name; k = name.split('_')[0]
    if name in TEXUSE:
        g, mir = TEXUSE[name]
        m, nt, b = principled('fin_' + name, rough=0.28, coat=cal.get('coat', 0.25))
        tn = uv_image_node(nt, 'tex/%s_albedo.png' % g, mir); nt.links.new(tn.outputs[0], b.inputs['Base Color'])
        rn = uv_image_node(nt, 'tex/%s_rough.png' % g, mir, noncolor=True); nt.links.new(rn.outputs[0], b.inputs['Roughness'])
        if g in ('duct', 'spinner'): b.inputs['Metallic'].default_value = 0.6
        if g == 'fan': b.inputs['Metallic'].default_value = 0.5
    elif k in ('mainwheel', 'nosewheel') and name.endswith('tyre'):
        m, nt, b = principled('tyre', base=tuple(cal.get('tyre', [0.012, 0.011, 0.010])), rough=0.75, spec=0.3)
    elif k in ('mainwheel', 'nosewheel'):
        m, nt, b = principled('hub', base=tuple(cal.get('hub', [0.45, 0.45, 0.46])), rough=0.35, metal=0.7)
    elif k in ('nose', 'main'):
        m, nt, b = principled('strut', base=(0.55, 0.56, 0.58), rough=0.25, metal=0.9)
    elif k == 'ngbay':
        m, nt, b = principled('bay', base=(0.03, 0.03, 0.03), rough=0.6)
    elif k in ('core', 'plug'):
        m, nt, b = principled('core', base=(0.32, 0.31, 0.30), rough=0.4, metal=0.8)
    else:   # pylons, flap-track fairings: paint
        m, nt, b = principled('paint', base=tuple(cal.get('paint', [0.8, 0.8, 0.8])), rough=0.28, coat=cal.get('coat', 0.25))
    o.data.materials.clear(); o.data.materials.append(m)

def ground(cal, size=800):
    import json as _j
    T = _j.load(open('tex/ground_tile.json'))
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0)); g = bpy.context.active_object; g.name = 'ground'
    m = bpy.data.materials.new('concrete'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.85
    if 'Specular IOR Level' in b.inputs: b.inputs['Specular IOR Level'].default_value = 0.3
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    # u = (y_left - y)/len_y ; v = 1 - (x_top - x)/len_x
    mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY_ADD'; mu.inputs[1].default_value = -1 / T['len_y']; mu.inputs[2].default_value = T['y_left'] / T['len_y']
    nt.links.new(sep.outputs['Y'], mu.inputs[0])
    mv = nt.nodes.new('ShaderNodeMath'); mv.operation = 'MULTIPLY_ADD'; mv.inputs[1].default_value = 1 / T['len_x']; mv.inputs[2].default_value = 1 - T['x_top'] / T['len_x']
    nt.links.new(sep.outputs['X'], mv.inputs[0])
    cb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(mu.outputs[0], cb.inputs[0]); nt.links.new(mv.outputs[0], cb.inputs[1])
    img = bpy.data.images.load(os.path.abspath('tex/ground_tile.png'), check_existing=True)
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img; tn.extension = 'REPEAT'; nt.links.new(cb.outputs[0], tn.inputs[0])
    gain = nt.nodes.new('ShaderNodeMixRGB'); gain.blend_type = 'MULTIPLY'; gain.inputs[0].default_value = 1.0
    gain.inputs[2].default_value = (*cal.get('ground_gain', [1.0, 1.0, 1.0]), 1)
    nt.links.new(tn.outputs[0], gain.inputs[1]); nt.links.new(gain.outputs[0], b.inputs['Base Color'])
    if os.environ.get('WHITEGROUND'):
        b.inputs['Base Color'].default_value = (0.5, 0.5, 0.5, 1)
        for l in list(nt.links):
            if l.to_socket == b.inputs['Base Color']: nt.links.remove(l)
    g.data.materials.append(m)
    return g

def world_and_sun(cal, sun_on=True, sky_on=True):
    import json as _j
    sc = bpy.context.scene
    w = bpy.data.worlds.new('photo_sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree
    bg = nt.nodes['Background']
    env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.abspath('tex/env.exr'), check_existing=True)
    tint = nt.nodes.new('ShaderNodeMixRGB'); tint.blend_type = 'MULTIPLY'; tint.inputs[0].default_value = 1.0
    # sky split into a low band and the high sky, each with its own fitted colour/strength
    tc = nt.nodes.new('ShaderNodeTexCoord'); sz = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sz.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.26; mr.inputs['From Max'].default_value = 0.42
    nt.links.new(sz.outputs['Z'], mr.inputs['Value'])
    lohi = nt.nodes.new('ShaderNodeMixRGB'); nt.links.new(mr.outputs[0], lohi.inputs[0])
    lohi.inputs[1].default_value = (*cal.get('sky_low', [1.0, 1.0, 1.0]), 1); lohi.inputs[2].default_value = (*cal.get('sky_high', [1.0, 1.0, 1.0]), 1)
    nt.links.new(lohi.outputs[0], tint.inputs[2])
    nt.links.new(env.outputs[0], tint.inputs[1])
    # camera rays see the photo's own sky at its true elevations; everything else is lit by the sky profile
    envc = nt.nodes.new('ShaderNodeTexEnvironment'); envc.image = bpy.data.images.load(os.path.abspath('tex/env_cam.exr'), check_existing=True)
    lp = nt.nodes.new('ShaderNodeLightPath'); mix = nt.nodes.new('ShaderNodeMixRGB')
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0]); nt.links.new(tint.outputs[0], mix.inputs[1]); nt.links.new(envc.outputs[0], mix.inputs[2])
    bgc = nt.nodes.new('ShaderNodeMath'); bgc.operation = 'MAXIMUM'
    nt.links.new(mix.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 1.0 if sky_on else 0.0
    S = _j.load(open('sun.json'))
    el, az = math.radians(S['el']), math.radians(S['az'])
    d = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
    sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = cal.get('sun', 3.0) if sun_on else 0.0
    sd.color = tuple(cal.get('sun_color', [1.0, 0.62, 0.36])); sd.angle = math.radians(0.6)
    so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
    from mathutils import Vector
    so.rotation_mode = 'QUATERNION'; so.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(d))
    return so

def fill_light(rgb, el_deg, az_deg, angle_deg=20.0):
    from mathutils import Vector
    el, az = math.radians(el_deg), math.radians(az_deg)
    d = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
    s = max(rgb); ld = bpy.data.lights.new('fill', 'SUN'); ld.energy = s
    ld.color = tuple(c / s for c in rgb) if s > 0 else (1, 1, 1); ld.angle = math.radians(angle_deg)
    o = bpy.data.objects.new('fill', ld); bpy.context.scene.collection.objects.link(o)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(d))
    return o
