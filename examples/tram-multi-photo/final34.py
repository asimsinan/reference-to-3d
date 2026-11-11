# blender -b bake34/baked.blend -P final34.py -- MODE [actions]
#   MODE real  : tram 34 in real materials (colours measured on the photos, lettering as decals cut from them)
#   MODE photo : the photos' pixels (photos 9, 13) projected, unlit
# actions: cams | views | save=PATH | glb=PATH
import bpy, bmesh, sys, os, math, json
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
os.environ.setdefault('CAMS', 'cams34.json')
import rig, geom34 as T
args = sys.argv[sys.argv.index('--') + 1:]; MODE = args[0]; ACTS = args[1:]
SAMPLES = int(os.environ.get('SAMPLES', '64')); EXPO = float(os.environ.get('EXPO', '0'))
CJ = json.load(open('tex34m/colors.json'))['srgb']
K = {'red': 0.438, 'white': 0.9, 'maroon': 0.033, 'roof': 0.07}
K.update({k: float(v) for k, v in (a.split('=') for a in os.environ.get('LEV', '').split(',') if a)})   # albedo level overrides

def lin(c): c = c / 255.0; return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def hue(name, level):
    """the photo's chromaticity at a chosen albedo level (max channel = level)"""
    l = [lin(c) for c in CJ[name]]; m = max(l); return tuple(level * x / m for x in l)
RED = hue('red', K.get('red', 0.42)); WHITE = hue('white', K.get('white', 0.80)); MAROON = hue('maroon', K.get('maroon', 0.10))
ROOF = hue('roofgrey', 0.55); ROOFL = (K.get('roof', 0.14),) * 2 + (K.get('roof', 0.14) * 1.07,); BATT = hue('battery', K.get('batt', 0.62))
RIB = hue('ribwood', 0.30); HONEY = tuple(K.get('honey', 1.0) * c for c in (0.22, 0.08, 0.019)); ENDW = hue('endwood', 0.25); CEIL = hue('ceiling', 0.72)

def img(p, srgb=True):
    i = bpy.data.images.load(os.path.abspath(p), check_existing=True)
    if not srgb: i.colorspace_settings.name = 'Non-Color'
    return i

MATS = {}
def P(name, base=(0.8, 0.8, 0.8), tex=None, rough=0.5, metal=0.0, coat=0.0, spec=0.5, trans=0.0, ior=1.45, alpha_tex=False, emit=None, emit_tex=False, alpha=None):
    key = (name, tex)
    if key in MATS: return MATS[key]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    if tex:
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img(tex); tn.interpolation = 'Linear'
        nt.links.new(tn.outputs['Color'], b.inputs['Base Color'])
        if alpha_tex:
            nt.links.new(tn.outputs['Alpha'], b.inputs['Alpha'])
            m.blend_method = 'HASHED' if hasattr(m, 'blend_method') else None
        if emit_tex:
            nt.links.new(tn.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emit or 1.0
    else:
        b.inputs['Base Color'].default_value = (*base, 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec; b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.03
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior
    if alpha is not None:
        b.inputs['Alpha'].default_value = alpha
        if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
        if hasattr(m, 'use_transparency_overlap'): m.use_transparency_overlap = True
    if alpha_tex and hasattr(m, 'surface_render_method'): m.surface_render_method = 'DITHERED'
    if emit and not emit_tex:
        b.inputs['Emission Color'].default_value = (*emit[0], 1); b.inputs['Emission Strength'].default_value = emit[1]
    MATS[key] = m; return m

def photo_mat(o):
    m = bpy.data.materials.new('foto ' + o.name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img('tex34/%s.png' % o.name)
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(tn.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0]); return m

def planar_uv(o, fu, fv):
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co; uv[li].uv = (fu(co, poly.normal), fv(co, poly.normal))

def rear(o): return any(len(t) <= 3 and t[0] == 'B' and (len(t) == 1 or t[1] in 'LR0123') for t in o.name.split('_')[1:])
def local(co, o):     # front-end frame coordinates of a point on a rear-end object
    return (2 * T.CX - co.x, -co.y, co.z) if rear(o) else (co.x, co.y, co.z)

def real_mat(o):
    n = o.name; pre = lambda *p: n.startswith(p)
    AT = 'tex34alb/%s.png' % n
    if pre('paint_', 'sign_'):        return P('kirmizi boya', RED, tex=AT if os.path.exists(AT) else None, rough=0.3, coat=1.0, spec=0.35)
    if pre('white_'):                 return P('beyaz boya', WHITE, tex=AT if os.path.exists(AT) else None, rough=0.3, coat=0.8, spec=0.4)
    if pre('frame_in'):               return P('bal rengi ahsap', HONEY, rough=0.3, coat=0.5)
    if pre('frame_'):                 return P('bordo cerceve', MAROON, tex=AT if os.path.exists(AT) else None, rough=0.3, coat=0.8)
    if pre('glass_door'):             return P('fume kapi cami', (0.03, 0.03, 0.035), rough=0.03, coat=1.0, spec=0.6, alpha=0.45)
    if pre('glass_'):                 return P('cam', (0.10, 0.11, 0.11), rough=0.02, coat=1.0, spec=0.6, alpha=0.18)
    if pre('black_'):                 return P('siyah', (0.018, 0.018, 0.02), rough=0.4)
    if pre('chrome_'):                return P('krom', (0.9, 0.9, 0.9), rough=0.12, metal=1.0)
    if pre('lens_head'):              return P('far cami', (0.9, 0.9, 0.9), rough=0.02, coat=1.0, spec=0.6, alpha=0.08)
    if pre('reflector_'):             return P('far reflektor', (0.78, 0.78, 0.76), rough=0.35, metal=0.2, emit=((0.9, 0.9, 0.88), 0.35))
    if pre('lens_amber'):             return P('kehribar lamba', (0.35, 0.10, 0.01), rough=0.1, coat=1.0)
    if pre('lens_red'):               return P('kirmizi sinyal', (0.25, 0.008, 0.01), rough=0.08, coat=1.0)
    if pre('roof_battery'):           return P('batarya yan', ROOFL, rough=0.5, spec=0.4)
    if pre('roof_'):                  return P('cati', ROOFL, rough=0.6, spec=0.35)
    if pre('steel_flange', 'steel_wheel'): return P('tekerlek', (0.09, 0.085, 0.08), rough=0.55, metal=0.6)
    if pre('steel_'):                 return P('celik', (0.30, 0.29, 0.27), rough=0.5, metal=0.5)
    if pre('gear_'):                  return P('yuruyen aksam', (0.15, 0.13, 0.11), rough=0.8, spec=0.3)
    if pre('rust_'):                  return P('pasli demir', (0.16, 0.09, 0.05), rough=0.75)
    if pre('perf_'):                  return P('delikli kapak', tex='tex34m/perf.png', rough=0.5, metal=0.4)
    if pre('gate_'):                  return P('makas kapi', (0.03, 0.03, 0.03), rough=0.45, metal=0.5)
    if pre('wood_floor'):             return P('ahsap zemin', tex='tex34m/floor_cal.png', rough=0.55, coat=0.08, spec=0.35)
    if pre('woodlam_'):               return P('ahsap lambri', tex='tex34m/wainscot_cal.png', rough=0.45, coat=0.15, spec=0.4)
    if pre('woodrib_', 'woodlam_panelin'): return P('bal rengi ahsap', HONEY, rough=0.3, coat=0.5)
    if pre('woodend_', 'wood_seat'):  return P('kizil ahsap', (0.16, 0.05, 0.025), rough=0.45, coat=0.15)
    if pre('ceiling_'):               return P('tavan', tuple(min(0.9, K.get('ceil', 1.0) * c) for c in (0.62, 0.59, 0.55)), rough=0.7)
    if pre('leather_strap'):          return P('kayis', (0.02, 0.018, 0.016), rough=0.5)
    if pre('leather_cushion'):        return P('deri oturak', tuple(K.get('cushion', 0.6) * c for c in (0.075, 0.052, 0.044)), rough=0.55, coat=0.0, spec=0.3)
    if pre('leather_'):               return P('deri', tuple(K.get('leather', 1.0) * c for c in (0.075, 0.052, 0.044)), rough=0.5, coat=0.0, spec=0.35)
    if pre('brass_', 'gold_'):        return P('pirinc', (0.62, 0.48, 0.28), rough=0.38, metal=1.0)
    if pre('console_top'):            return P('konsol ust', tex='tex34m/console_top.png', rough=0.5)
    if pre('console_'):               return P('konsol', (0.70, 0.68, 0.62), rough=0.5)
    if pre('screen_'):
        k = n.split('_')[1] + '_' + n.split('_')[2]
        return P('ekran ' + k, tex='tex34m/%s.png' % k, rough=0.08, emit=0.9, emit_tex=True)
    if pre('blackseat_'):             return P('surucu koltugu', (0.02, 0.02, 0.022), rough=0.45)
    if pre('red_knob'):               return P('kirmizi topuz', (0.6, 0.02, 0.02), rough=0.2)
    if pre('lamp_diffuser'):          return P('lamba', (0.95, 0.93, 0.85), rough=0.3, emit=((1.0, 0.92, 0.78), 12.0))
    if pre('disp_'):                  return P('siyah', (0.018, 0.018, 0.02), rough=0.4)
    return P('siyah', (0.018, 0.018, 0.02), rough=0.4)

src = open('final.py').read(); g0 = src.index('def build_gate(o):'); g1 = src.index('MESH = ')
exec(src[g0:g1])

MESH = [o for o in bpy.data.objects if o.type == 'MESH']
for o in MESH:
    if MODE == 'photo' and os.path.exists('tex34/%s.png' % o.name) and not o.name.startswith(('screen_',)):
        m = photo_mat(o)
    else:
        m = real_mat(o)
    o.data.materials.clear(); o.data.materials.append(m)
    n = o.name
    if n.startswith(('glass_', 'lens_')): o.visible_shadow = False
    if MODE == 'real' and n == 'roof_deck':
        o.data.materials.clear(); o.data.materials.append(P('beyaz boya', WHITE, rough=0.3, coat=0.8, spec=0.4)); o.data.materials.append(P('cati', ROOFL, rough=0.6, spec=0.35))
        for poly in o.data.polygons: poly.material_index = 1 if poly.center.z > 2.922 else 0
    if MODE == 'real' and n == 'roof_battery':                              # light top (photo 15), dark sides (photo 9)
        o.data.materials.append(P('batarya ust', BATT, rough=0.55, spec=0.4))
        for poly in o.data.polygons:
            if poly.normal.z > 0.7: poly.material_index = 1          # daylight reaches the saloon and the cab
    if MODE == 'real' and n.startswith(('paint_dash', 'paint_cab', 'paint_side', 'white_hood', 'white_band', 'roof_deck', 'frame_doorpost')):
        inner = (P('bal rengi ahsap', HONEY, rough=0.3, coat=0.5) if n.startswith(('paint_side_upper', 'white_band')) else P('ic ahsap', MAROON, rough=0.35, coat=0.3)) if not n.startswith(('white_hood', 'roof_deck')) else P('ic tavan', CEIL, rough=0.7)
        o.data.materials.append(inner); ki = len(o.data.materials) - 1
        for poly in o.data.polygons:
            c = poly.center; nn = poly.normal
            if n.startswith('roof_deck'): inward = Vector((0, 0, -1))
            else:
                ax = Vector((max(T.Xr + 0.3, min(T.Xe - 0.3, c.x)) if T.Xr < c.x < T.Xe else max(2 * T.CX - T.Xf + 0.8, min(T.Xf - 0.8, c.x)), 0, c.z)); inward = ax - c; inward.z = 0
                if inward.length < 1e-6: continue
                inward.normalize()
            if nn.dot(inward) > 0.5: poly.material_index = ki
    if n.startswith('perf_'): planar_uv(o, lambda c, nn: c.x / 0.3, lambda c, nn: c.z / 0.3)
    if n.startswith('wood_floor'): planar_uv(o, lambda c, nn: c.x / 1.6, lambda c, nn: c.y / 1.6)
    if n.startswith('woodlam_'):  planar_uv(o, lambda c, nn: (c.x + c.y) / 0.8, lambda c, nn: c.z / 0.8)
    if n.startswith('leather_') and not n.startswith('leather_strap'): planar_uv(o, lambda c, nn: (c.x + c.y) / 0.4, lambda c, nn: c.z / 0.4 + c.x / 0.4 * abs(nn.z))
    if n.startswith('console_top'):
        xb, xf = T.Xf - 0.62, T.Xf - 0.06
        planar_uv(o, lambda c, nn, o=o: (0.5 - local(c, o)[1] / 1.6), lambda c, nn, o=o: (local(c, o)[0] - xb) / (xf - xb))

# ------------------------------------------------------------- decals (white lettering, alpha), real version
def decal(name, origin, udir, vdir, w, h, tex, off=0.006):
    o_ = Vector(origin); u = Vector(udir).normalized(); v = Vector(vdir).normalized(); nrm = u.cross(v)
    c = [o_ + nrm * off, o_ + u * w + nrm * off, o_ + u * w + v * h + nrm * off, o_ + v * h + nrm * off]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(p) for p in c], [], [(0, 1, 2, 3)]); uv = me.uv_layers.new(name='UVMap')
    for i, t in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))): uv.data[i].uv = t
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    me.materials.append(P('yazi ' + tex, (1, 1, 1), tex='tex34m/%s_a.png' % tex, rough=0.25, coat=0.6, alpha_tex=True)); return ob
DECALS = []
if MODE == 'real':
    def R3(p, r): return (2 * T.CX - p[0], -p[1], p[2]) if r else p
    def Rd(d, r): return (-d[0], -d[1], d[2]) if r else d
    z0, z1 = 1.03, T.ZWD - 0.045
    for r in (False, True):
        tg = 'B' if r else 'F'
        for i, (sa, sb) in enumerate(((0.0, T.SPOST[0]), (T.SPOST[1], T.SL))):
            o = T.decal_strip('decal_dash_%s%d' % (tg, i), sa + 0.05, sb - 0.05, z0, z1, r)
            o.data.materials.append(P('yazi dash_side', (1, 1, 1), tex='tex34m/dash_side_a.png', rough=0.25, coat=0.6, alpha_tex=True)); DECALS.append(o)
        xk = T.M['xk'] + 0.022
        DECALS.append(decal('decal_sign_' + tg, R3((xk, -0.56, 2.97), r), Rd((0, 1, 0), r), (0, 0, 1), 1.12, 0.17, 'sign', off=0.002))
        DECALS.append(decal('decal_signtab_' + tg, R3((xk + 0.001, -0.085, 3.14), r), Rd((0, 1, 0), r), (0, 0, 1), 0.17, 0.165, 'signtab', off=0.002))
    # logos (photo 18): in the lower row, from the viewer's left: Nostalji Tramvay, IETT, IBB
    xs = [T.Xe - T.wp - (i + 0.5) * T.WW for i in range(T.NW)]; yo = T.hw + 0.008
    L = [('logo_nostalji', 0.16, 0.31), ('logo_iett18', 0.33, 0.18), ('logo_ibb', 0.56, 0.24)]
    for sd in (1, -1):
        order = xs if sd > 0 else xs[::-1]                      # +Y side: viewer's left is +X
        for xc, (t, w, h) in zip(order, L):
            u = (-1, 0, 0) if sd > 0 else (1, 0, 0)
            org = (xc - u[0] * w / 2, sd * yo, 1.012 - h / 2)
            DECALS.append(decal('decal_%s_%d_%.1f' % (t, sd, xc), org, u, (0, 0, 1), w, h, t, off=0.0))

# ------------------------------------------------------------- organise, ground, light
sc = bpy.context.scene
col_m = bpy.data.collections.new('Tramvay 34'); sc.collection.children.link(col_m)
col_s = bpy.data.collections.new('Sahne (zemin, isik, kamera)'); sc.collection.children.link(col_s)
root = bpy.data.objects.new('Tramvay_34', None); col_m.objects.link(root)
for o in MESH + DECALS:
    for c in list(o.users_collection): c.objects.unlink(o)
    col_m.objects.link(o); o.parent = root
root.location = (-T.CX, 0, 0)                     # the car centred on the origin
for o in list(bpy.data.objects):
    if o.type == 'CAMERA': bpy.data.objects.remove(o)
def plane(name, x0, x1, y0, y1, z, mat, tile=2.0):
    me = bpy.data.meshes.new(name); me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name='UVMap')
    for i, (u, v) in enumerate(((0, 0), ((x1 - x0) / tile, 0), ((x1 - x0) / tile, (y1 - y0) / tile), (0, (y1 - y0) / tile))): uv.data[i].uv = (u, v)
    ob = bpy.data.objects.new(name, me); col_s.objects.link(ob); me.materials.append(mat); return ob
plane('Zemin', -16, 16, -10, 10, -0.002, P('zemin', tex='texalbf/_street.png', rough=0.85, spec=0.3))
rail = P('ray', (0.55, 0.55, 0.56), rough=0.25, metal=1.0)
for s in (1, -1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, s * 0.525, 0.0)); r = bpy.context.object
    r.scale = (32, 0.06, 0.012); r.name = 'Ray_%s' % ('L' if s > 0 else 'R'); r.data.materials.append(rail)
    for c in list(r.users_collection): c.objects.unlink(r)
    col_s.objects.link(r)
w = bpy.data.worlds.new('gokyuzu'); sc.world = w; w.use_nodes = True; nt = w.node_tree
tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); cr = nt.nodes.new('ShaderNodeValToRGB')
nt.links.new(tc.outputs['Generated'], sp.inputs[0]); nt.links.new(sp.outputs['Z'], cr.inputs[0])
cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (0.30, 0.29, 0.28, 1)
e = cr.color_ramp.elements.new(0.5); e.color = (0.85, 0.90, 0.97, 1)
cr.color_ramp.elements[-1].position = 1.0; cr.color_ramp.elements[-1].color = (0.30, 0.48, 0.85, 1)
bg = nt.nodes['Background']; bg.inputs[1].default_value = float(os.environ.get('SKY', '0.6')); nt.links.new(cr.outputs[0], bg.inputs[0])
# camera rays from photo 8's camera see the photo itself behind the windows (only exact from that camera)
bd_img = nt.nodes.new('ShaderNodeTexImage'); bd_img.image = img('ref2/p8.png'); bd_img.extension = 'EXTEND'
nt.links.new(tc.outputs['Window'], bd_img.inputs[0])
bd_bg = nt.nodes.new('ShaderNodeBackground'); nt.links.new(bd_img.outputs[0], bd_bg.inputs[0])
lp = nt.nodes.new('ShaderNodeLightPath'); mixw = nt.nodes.new('ShaderNodeMixShader'); wout = nt.nodes['World Output']
bd_on = nt.nodes.new('ShaderNodeValue'); bd_on.outputs[0].default_value = 0.0
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
nt.links.new(lp.outputs['Is Camera Ray'], mul.inputs[0]); nt.links.new(bd_on.outputs[0], mul.inputs[1])
nt.links.new(mul.outputs[0], mixw.inputs[0]); nt.links.new(bg.outputs[0], mixw.inputs[1]); nt.links.new(bd_bg.outputs[0], mixw.inputs[2])
nt.links.new(mixw.outputs[0], wout.inputs['Surface'])
sun_d = bpy.data.lights.new('Gunes', 'SUN'); sun_d.energy = float(os.environ.get('SUN', '3.5')); sun_d.angle = math.radians(2)
sun = bpy.data.objects.new('Gunes', sun_d); col_s.objects.link(sun)
SD = Vector([float(v) for v in os.environ.get('SUNDIR', '-0.35,0.75,0.55').split(',')]).normalized()
sun.rotation_euler = SD.to_track_quat('Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = os.environ.get('LOOK', 'Medium High Contrast').replace('_', ' '); sc.view_settings.exposure = EXPO
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.color_depth = '8'
if MODE == 'photo': sun.hide_render = True; sc.view_settings.look = 'None'

def place(co, cd, p, t, lens):
    co.location = Vector(p); co.rotation_euler = (Vector(t) - Vector(p)).to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens
for a in ACTS:
    if a == 'cams':
        root.location = (0, 0, 0)
        for o in col_s.objects: o.hide_render = o.name.startswith(('Zemin', 'Ray'))
        sc.render.film_transparent = True; sc.cycles.use_denoising = False; sc.cycles.pixel_filter_type = 'BOX'; sc.cycles.filter_width = 1.0
        for k in os.environ.get('KS', '9,13').split(','):
            sc.cycles.use_denoising = (k == '8'); sc.view_settings.exposure = float(os.environ.get('EXPO8', '1.5')) if k == '8' else EXPO
            sun.hide_render = (k == '8'); bg.inputs[1].default_value = float(os.environ.get('SKY8', '1.4')) if k == '8' else float(os.environ.get('SKY', '0.6'))
            bd_on.outputs[0].default_value = 1.0 if k == '8' else 0.0
            OVC = k == '8'                                    # photo 8: overcast, rain: a neutral grey-white sky
            zn = float(os.environ.get('ZEN8', '0.15')); gr = float(os.environ.get('GROUND8', '1.0'))
            cr.color_ramp.elements[-1].color = (zn, zn * 1.01, zn * 1.04, 1) if OVC else (0.30, 0.48, 0.85, 1)
            cr.color_ramp.elements[0].color = (gr, gr * 0.98, gr * 0.96, 1) if OVC else (0.30, 0.29, 0.28, 1)
            cr.color_ramp.elements[1].color = (0.90, 0.90, 0.91, 1) if OVC else (0.85, 0.90, 0.97, 1)
            sc.view_settings.look = 'None' if k == '8' else os.environ.get('LOOK', 'Medium High Contrast').replace('_', ' ')
            bd_bg.inputs[1].default_value = 2.0 ** -sc.view_settings.exposure
            camob = rig.photo_camera(k)
            if k == '8' and MODE == 'real':
                # what photo 8 shows through every pane, at the camera's screen coordinates (exact from this camera only)
                gm = bpy.data.materials.get('cam8 cam') or bpy.data.materials.new('cam8 cam')
                gm.use_nodes = True; gnt = gm.node_tree; gnt.nodes.clear()
                gtc = gnt.nodes.new('ShaderNodeTexCoord'); gti = gnt.nodes.new('ShaderNodeTexImage'); gti.image = img('ref2/p8.png'); gti.extension = 'EXTEND'
                gem = gnt.nodes.new('ShaderNodeEmission'); gem.inputs[1].default_value = 2.0 ** -sc.view_settings.exposure
                gtr = gnt.nodes.new('ShaderNodeBsdfTransparent'); glp = gnt.nodes.new('ShaderNodeLightPath'); gmx = gnt.nodes.new('ShaderNodeMixShader')
                gout = gnt.nodes.new('ShaderNodeOutputMaterial')
                gnt.links.new(gtc.outputs['Window'], gti.inputs[0]); gnt.links.new(gti.outputs[0], gem.inputs[0])
                gnt.links.new(glp.outputs['Is Camera Ray'], gmx.inputs[0]); gnt.links.new(gtr.outputs[0], gmx.inputs[1]); gnt.links.new(gem.outputs[0], gmx.inputs[2])
                gnt.links.new(gmx.outputs[0], gout.inputs['Surface'])
                SAVEG = {}
                for o in MESH:
                    if o.name.startswith(('glass_side', 'glass_cab', 'glass_end', 'glass_door')):
                        SAVEG[o.name] = [s.material for s in o.material_slots]
                        for s in o.material_slots: s.material = gm
            fl = bpy.data.objects.get('Flas')
            if fl is None:
                fd = bpy.data.lights.new('Flas', 'SPOT'); fd.spot_size = math.radians(120); fd.spot_blend = 0.6; fd.shadow_soft_size = 0.04
                fl = bpy.data.objects.new('Flas', fd); col_s.objects.link(fl)
            fl.matrix_world = camob.matrix_world.copy(); fl.data.energy = float(os.environ.get('FLASH', '15')) if k == '8' else 0.0
            fl.hide_render = k != '8'
            sc.render.filepath = os.path.abspath('out/%s34_%s.png' % (MODE, k)); bpy.ops.render.render(write_still=True)
            if k == '8' and MODE == 'real':
                for o in MESH:
                    if o.name in SAVEG:
                        for s, mm in zip(o.material_slots, SAVEG[o.name]): s.material = mm
        for o in list(bpy.data.objects):
            if o.type == 'CAMERA' or o.name == 'Flas': bpy.data.objects.remove(o)
        for o in col_s.objects: o.hide_render = False
        sc.render.film_transparent = False; sc.cycles.use_denoising = True; sc.cycles.pixel_filter_type = 'BLACKMAN_HARRIS'; sc.cycles.filter_width = 1.5
        root.location = (-T.CX, 0, 0)
    elif a == 'views':
        sc.render.film_transparent = False
        if os.environ.get('WORLD', 'city') == 'city':
            cw = bpy.data.worlds.new('sehir'); cw.use_nodes = True; cn = cw.node_tree
            et = cn.nodes.new('ShaderNodeTexEnvironment'); et.image = bpy.data.images.load('/Applications/Blender.app/Contents/Resources/5.2/datafiles/studiolights/world/city.exr')
            cn.links.new(et.outputs[0], cn.nodes['Background'].inputs[0]); cn.nodes['Background'].inputs[1].default_value = float(os.environ.get('CITY', '1.0'))
            sc.world = cw
        # car centred: front end at x ~ +3.79, rear at ~ -3.79
        V = {'on34': ((11, 7, 2.2), (0.5, 0, 1.6), 38), 'arka34': ((-11, -7, 2.4), (-0.5, 0, 1.6), 38), 'sol': ((0.3, 13, 1.8), (0.3, 0, 1.7), 33),
             'sag': ((0.3, -13, 1.8), (0.3, 0, 1.7), 33), 'ust': ((7, 8, 9), (0, 0, 2.0), 34), 'on': ((12, 0, 1.7), (0, 0, 1.8), 45),
             'yakin': ((6.0, 1.6, 1.5), (3.6, 0, 1.4), 32), 'salon': ((-2.30 - T.CX, 0.0, 1.96), (3.0, 0.0, 1.45), 14), 'kabin': ((3.0, 0.15, 1.95), (4.0, -0.05, 1.25), 14),
             'koltuk': ((0.9, -0.15, 1.35), (0.0, 0.6, 1.0), 20), 'altyan': ((1.2, -6.0, 0.55), (0.6, 0, 0.55), 30), 'arkakose': ((-6.2, -3.2, 1.5), (-3.4, 0, 1.5), 32)}
        cd = bpy.data.cameras.new('show'); co = bpy.data.objects.new('show', cd); col_s.objects.link(co); sc.camera = co
        sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
        only = os.environ.get('VIEWS')
        for n_, (p, t, lens) in V.items():
            if only and n_ not in only.split(','): continue
            inside = n_ in ('salon', 'kabin', 'koltuk')
            sc.view_settings.exposure = EXPO + (float(os.environ.get('EXPOIN', '1.6')) if inside else 0.0)
            place(co, cd, p, t, lens); sc.render.filepath = os.path.abspath('out/%s34_%s.png' % (MODE, n_)); bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(co)
    elif a.startswith('save='):
        cd = bpy.data.cameras.new('Kamera'); co = bpy.data.objects.new('Kamera', cd); col_s.objects.link(co); sc.camera = co
        place(co, cd, (11, 7, 2.2), (0.5, 0, 1.6), 38); cd.display_size = 0.4
        sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
        for x in bpy.context.selected_objects: x.select_set(False)
        root.select_set(True); bpy.context.view_layer.objects.active = root
        for scr in bpy.data.screens:
            for area in scr.areas:
                if area.type == 'VIEW_3D':
                    for s_ in area.spaces:
                        if s_.type == 'VIEW_3D':
                            s_.shading.type = 'MATERIAL'; s_.overlay.show_extras = False
                            r3 = s_.region_3d; r3.view_location = Vector((0, 0, 1.6)); r3.view_distance = 14.0
                            r3.view_rotation = Vector((-0.75, -0.55, -0.25)).to_track_quat('-Z', 'Y')
        bpy.ops.file.pack_all(); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[5:]), compress=True)
    elif a.startswith('glb='):
        for x in bpy.context.selected_objects: x.select_set(False)
        for o in MESH + DECALS: o.select_set(True)
        root.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.abspath(a[4:]), use_selection=True, export_format='GLB', export_apply=True,
                                  export_image_format='JPEG', export_jpeg_quality=92)
print('FINAL34 DONE', MODE, ACTS)
