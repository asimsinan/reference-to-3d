# blender -b bake/baked.blend -P final.py -- MODE [actions...]
#   MODE real  : real materials (albedo from the photos, light divided out) - the main version
#   MODE photo : the photos' own pixels as the surface colour (unlit look, for the fit check)
# actions: cams (render every photo camera, photo behind) | views (showcase) | save=PATH.blend | glb=PATH.glb
import bpy, bmesh, sys, os, math, json
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
import rig
D = json.load(open('params.json'))
args = sys.argv[sys.argv.index('--') + 1:]; MODE = args[0]; ACTS = args[1:]
TEXD = 'texalbf' if MODE == 'real' else 'texf'
EXPO = float(os.environ.get('EXPO', '0.0'))
SAMPLES = int(os.environ.get('SAMPLES', '64'))

def img(path, srgb=True):
    i = bpy.data.images.load(os.path.abspath(path), check_existing=True)
    if not srgb: i.colorspace_settings.name = 'Non-Color'
    return i

def principled(name, tex=None, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, coat=0.0, spec=0.5, trans=0.0, ior=1.45, alpha=None,
               emit=None, scale=None, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    if tex:
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img(tex); tn.interpolation = 'Linear'
        if scale:
            uv = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, 1)
            nt.links.new(uv.outputs['UV'], mp.inputs[0]); nt.links.new(mp.outputs[0], tn.inputs[0])
        if tint:
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
            mx.inputs[7].default_value = (*tint, 1); nt.links.new(tn.outputs[0], mx.inputs[6]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
        else:
            nt.links.new(tn.outputs[0], b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = (*base, 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.08
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior
    if emit:
        b.inputs['Emission Color'].default_value = (*emit[0], 1); b.inputs['Emission Strength'].default_value = emit[1]
    return m

def photo_mat(name, tex):
    # the photos' pixels as they are (emission), for the photo version
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img(tex)
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(tn.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0]); return m

def cls(n):
    pre = lambda *p: n.startswith(p)
    if pre('glass_side', 'glass_cab', 'glass_door'): return 'glass'
    if pre('headglass'): return 'lens'
    if pre('siglens'): return 'redlens'
    if pre('side_', 'dash_', 'cab_', 'fender_', 'bulkhead_', 'sign_', 'signtab_'): return 'paint'
    if n == 'roof': return 'roof'
    if pre('monitor', 'roofboard'): return 'canvas'
    if pre('wheel', 'flange'): return 'steel'
    if pre('pole_', 'bolt_', 'toplamp'): return 'brass'
    if pre('headlamp', 'mirror_', 'siglamp'): return 'blackgloss'
    if pre('bow', 'voltsign'): return 'iron'
    if pre('bench', 'controller', 'door_'): return 'wood'
    if pre('floor'): return 'floor'
    if pre('ceiling'): return 'ceiling'
    if pre('gate_'): return 'gate'
    return 'iron'

def interior_faces(o):
    """faces of a wall that look into the car (towards the long axis / the saloon)"""
    me = o.data; idx = []
    for p in me.polygons:
        c = p.center; n = p.normal
        if o.name.startswith('bulkhead'):
            inward = Vector((-math.copysign(1, c.x), 0, 0))
        elif o.name.startswith('roof'):
            inward = Vector((0, 0, -1))
        else:
            ax = Vector((max(-2.7, min(2.7, c.x)), 0, c.z)); inward = (ax - c); inward.z = 0
            if inward.length < 1e-6: continue
            inward.normalize()
        if n.dot(inward) > 0.5: idx.append(p.index)
    return idx

def build_gate(o):
    """scissor gate: the photo's diamond lattice as thin bars (pitch read on the rectified side, ~0.14 x 0.24 m)"""
    me = o.data; vs = [o.matrix_world @ v.co for v in me.vertices]
    xs = [v.x for v in vs]; ys = [v.y for v in vs]; zs = [v.z for v in vs]
    x0, x1, y, z0, z1 = min(xs), max(xs), sum(ys) / len(ys), min(zs), max(zs)
    bm = bmesh.new(); w = 0.012; dpx, dpz = 0.14, 0.24
    nx = max(2, round((x1 - x0) / dpx)); dpx = (x1 - x0) / nx
    def bar(a, b):
        a = Vector(a); b = Vector(b); d = (b - a).normalized(); s = Vector((0, 1, 0)).cross(d).normalized() * w
        t = Vector((0, 0.006, 0))
        q = [bm.verts.new(p) for p in (a - s - t, b - s - t, b + s - t, a + s - t, a - s + t, b - s + t, b + s + t, a + s + t)]
        for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)): bm.faces.new([q[i] for i in f])
    H = z1 - z0
    for i in range(-int(H / dpz) - 2, nx + int(H / dpz) + 3):
        for sgn in (1, -1):
            # line x = x0 + i*dpx + sgn * (z - z0) * dpx/dpz, clipped to the box
            pts = []
            for z in (z0, z1):
                pts.append((x0 + i * dpx + sgn * (z - z0) * dpx / dpz * 1.0, z))
            (xa, za), (xb, zb) = pts
            # clip in x
            def clip(xa, za, xb, zb):
                if xa > xb: xa, za, xb, zb = xb, zb, xa, za
                if xb < x0 or xa > x1: return None
                if xa < x0: za = za + (zb - za) * (x0 - xa) / (xb - xa); xa = x0
                if xb > x1: zb = za + (zb - za) * (x1 - xa) / (xb - xa); xb = x1
                return xa, za, xb, zb
            r = clip(xa, za, xb, zb)
            if r and abs(r[3] - r[1]) > 0.02: bar((r[0], y, r[1]), (r[2], y, r[3]))
    for z in (z0 + 0.01, z1 - 0.01): bar((x0, y, z), (x1, y, z))
    for x in (x0 + 0.01, x1 - 0.01): bar((x, y, z0), (x, y, z1))
    bm.to_mesh(me); bm.free(); o.matrix_world = Matrix()
    # UVs so the exporter is happy
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(); bpy.ops.object.mode_set(mode='OBJECT')

MESH = [o for o in bpy.data.objects if o.type == 'MESH']
WOOD = principled('wood interior', tex='texalbf/_wood.png', rough=0.42, coat=0.35, scale=4.0)
mats = {}
def mat_for(o):
    c = cls(o.name); tex = '%s/%s.png' % (TEXD, o.name)
    if MODE == 'photo':
        return photo_mat('photo ' + o.name, tex)
    if c == 'paint':   return principled('paint ' + o.name, tex=tex, rough=0.32, coat=0.45, spec=0.5)
    if c == 'roof':    return principled('roof ' + o.name, tex=tex, rough=0.8, spec=0.3)
    if c == 'canvas':  return principled('canvas ' + o.name, tex=tex, rough=0.85, spec=0.3)
    if c == 'steel':   return principled('steel ' + o.name, tex=tex, rough=0.38, metal=0.75)
    if c == 'brass':   return principled('brass ' + o.name, tex=tex, rough=0.3, metal=0.85)
    if c == 'blackgloss': return principled('black ' + o.name, tex=tex, rough=0.25, coat=0.5)
    if c == 'iron':    return principled('iron ' + o.name, tex=tex, rough=0.6, metal=0.3)
    if c == 'wood':    return WOOD
    if c == 'floor':   return principled('floor', tex='texalbf/_wood.png', rough=0.7, scale=6.0, tint=(0.35, 0.3, 0.27))
    if c == 'ceiling': return principled('ceiling', base=(0.42, 0.38, 0.30), rough=0.7)
    if c == 'gate':    return principled('gate', base=(0.05, 0.05, 0.05), rough=0.45, metal=0.6)
    if c == 'glass':   return principled('glass', base=(0.80, 0.84, 0.82), rough=0.02, trans=1.0, ior=1.0, coat=1.0, spec=0.3)
    if c == 'lens':    return principled('lamp glass', tex=tex, rough=0.08, coat=1.0, spec=0.6)
    if c == 'redlens': return principled('red lens', base=(0.55, 0.02, 0.03), rough=0.08, trans=0.6, ior=1.5, coat=1.0)
    return principled('misc ' + o.name, tex=tex, rough=0.6)

for o in MESH:
    if MODE == 'real' and cls(o.name) == 'gate': build_gate(o)
    m = mat_for(o); o.data.materials.clear(); o.data.materials.append(m)
    if MODE == 'real':
        if o.name == 'roof':
            # cream band and cove are paint, the top is canvas (polygon material index from geom.py was lost at bake)
            o.data.materials.append(principled('roof canvas', tex='%s/roof.png' % TEXD, rough=0.85, spec=0.3))
            for p in o.data.polygons: p.material_index = 1 if p.center.z > 3.0 else 0
            o.data.materials[0] = principled('roof cove paint', tex='%s/roof.png' % TEXD, rough=0.35, coat=0.3)
        if cls(o.name) == 'paint' and o.name.startswith(('side_', 'dash_', 'cab_', 'bulkhead_')):
            o.data.materials.append(WOOD); k = len(o.data.materials) - 1
            for i in interior_faces(o): o.data.polygons[i].material_index = k
    for p in o.data.polygons: p.use_smooth = p.use_smooth

# ------------------------------------------------------------- organise: model under one parent, studio apart
sc = bpy.context.scene
col_m = bpy.data.collections.new('Tramvay 115'); sc.collection.children.link(col_m)
col_s = bpy.data.collections.new('Sahne (zemin, isik, kamera)'); sc.collection.children.link(col_s)
root = bpy.data.objects.new('Tramvay_115', None); col_m.objects.link(root); root.empty_display_size = 1.0
for o in MESH:
    for c in o.users_collection: c.objects.unlink(o)
    col_m.objects.link(o); o.parent = root
for o in list(bpy.data.objects):
    if o.type == 'CAMERA': bpy.data.objects.remove(o)

# street with the two rails (the photo's own pavement, tiled)
def plane(name, x0, x1, y0, y1, z, mat):
    me = bpy.data.meshes.new(name); me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(); uv = me.uv_layers[0].data
    for i, (u, v) in enumerate(((0, 0), ((x1 - x0) / 2.0, 0), ((x1 - x0) / 2.0, (y1 - y0) / 2.0), (0, (y1 - y0) / 2.0))): uv[i].uv = (u, v)
    o = bpy.data.objects.new(name, me); col_s.objects.link(o); me.materials.append(mat); return o
street = principled('street', tex='texalbf/_street.png', rough=0.85, spec=0.3)
plane('Zemin', -14, 14, -9, 9, -0.002, street)
rail = principled('rail', base=(0.55, 0.55, 0.56), rough=0.25, metal=1.0)
for s in (1, -1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, s * D['gauge'] / 2, 0.0)); r = bpy.context.object
    r.scale = (28, 0.06, 0.012); r.name = 'Ray_%s' % ('L' if s > 0 else 'R'); r.data.materials.append(rail)
    for c in r.users_collection: c.objects.unlink(r)
    col_s.objects.link(r)

# light: overcast daylight with a soft sun (photo 6 is the reference light)
w = bpy.data.worlds.new('gokyuzu'); sc.world = w; w.use_nodes = True; nt = w.node_tree
tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); cr = nt.nodes.new('ShaderNodeValToRGB')
nt.links.new(tc.outputs['Generated'], sp.inputs[0]); nt.links.new(sp.outputs['Z'], cr.inputs[0])
cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (0.28, 0.27, 0.26, 1)      # below horizon: street bounce
e = cr.color_ramp.elements.new(0.5); e.color = (0.92, 0.94, 0.97, 1)                                   # hazy horizon
cr.color_ramp.elements[-1].position = 1.0; cr.color_ramp.elements[-1].color = (0.55, 0.66, 0.85, 1)   # zenith
bg = nt.nodes['Background']; bg.inputs[1].default_value = float(os.environ.get('SKY', '1.4'))
nt.links.new(cr.outputs[0], bg.inputs[0])
sun_d = bpy.data.lights.new('Gunes', 'SUN'); sun_d.energy = float(os.environ.get('SUN', '1.0')); sun_d.angle = math.radians(12)
sun = bpy.data.objects.new('Gunes', sun_d); col_s.objects.link(sun); sun.rotation_euler = (math.radians(52), 0, math.radians(150))

sc.render.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.view_settings.view_transform = 'AgX' if os.environ.get('AGX') else 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = EXPO
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.render.image_settings.color_depth = '8'

if MODE == 'photo':
    for o in (sun,): o.hide_render = True
    sc.view_settings.exposure = 0

for a in ACTS:
    if a == 'cams':
        # photo-camera renders of the tram alone (transparent), for the comparison
        for o in col_s.objects: o.hide_render = o.name.startswith(('Zemin', 'Ray'))
        sc.render.film_transparent = True; sc.cycles.use_denoising = False; sc.cycles.pixel_filter_type = 'BOX'; sc.cycles.filter_width = 1.0
        for k in os.environ.get('CAMS', ','.join(rig.J['cams'])).split(','):
            rig.photo_camera(k); sc.render.filepath = os.path.abspath('out/%s%s.png' % (MODE, k)); bpy.ops.render.render(write_still=True)
        for o in list(bpy.data.objects):
            if o.type == 'CAMERA': bpy.data.objects.remove(o)
        for o in col_s.objects: o.hide_render = False
        sc.render.film_transparent = False; sc.cycles.use_denoising = True; sc.cycles.pixel_filter_type = 'BLACKMAN_HARRIS'; sc.cycles.filter_width = 1.5
    elif a == 'views':
        sc.render.film_transparent = False
        V = {'on34': ((10.5, 6.5, 2.0), (0.3, 0, 1.6), 38), 'arka34': ((-10.5, -6.5, 2.4), (-0.3, 0, 1.6), 38), 'sag': ((0.4, -12.5, 1.8), (0.4, 0, 1.7), 33),
             'sol': ((0.4, 12.5, 1.8), (0.4, 0, 1.7), 33), 'ust34': ((8, 9, 8.5), (0, 0, 1.8), 34), 'on': ((12, 0, 1.6), (0, 0, 1.7), 45),
             'yakin_far': ((5.4, 1.3, 1.35), (3.6, 0, 1.25), 38), 'platform': ((4.2, 2.6, 1.9), (2.6, 0.2, 1.6), 30), 'alt': ((2.6, 4.0, 0.3), (0.2, 0, 0.5), 30),
             'ic': ((2.9, 0.1, 1.65), (-2, 0, 1.5), 20)}
        cd = bpy.data.cameras.new('show'); co = bpy.data.objects.new('show', cd); col_s.objects.link(co); sc.camera = co
        sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
        only = os.environ.get('VIEWS')
        for n, (p, t, lens) in V.items():
            if only and n not in only.split(','): continue
            co.location = p; co.rotation_euler = (Vector(t) - Vector(p)).to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens
            sc.render.filepath = os.path.abspath('out/%s_%s.png' % (MODE, n)); bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(co)
    elif a.startswith('save='):
        cd = bpy.data.cameras.new('Kamera'); co = bpy.data.objects.new('Kamera', cd); col_s.objects.link(co); sc.camera = co
        co.location = (10.5, 6.5, 2.2); co.rotation_euler = (Vector((0.3, 0, 1.6)) - co.location).to_track_quat('-Z', 'Y').to_euler(); cd.lens = 38
        cd.display_size = 0.4; sun_d.energy = sun_d.energy
        sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
        for x in bpy.context.selected_objects: x.select_set(False)
        root.select_set(True); bpy.context.view_layer.objects.active = root
        # every 3D view framed on the tram in Material Preview
        for scr in bpy.data.screens:
            for area in scr.areas:
                if area.type == 'VIEW_3D':
                    for sp in area.spaces:
                        if sp.type == 'VIEW_3D':
                            sp.shading.type = 'MATERIAL'; sp.overlay.show_extras = False
                            r3 = sp.region_3d; r3.view_location = Vector((0, 0, 1.6)); r3.view_distance = 13.0
                            r3.view_rotation = (Vector((-0.75, -0.55, -0.25))).to_track_quat('-Z', 'Y')
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[5:]), compress=True)
    elif a.startswith('glb='):
        for x in bpy.context.selected_objects: x.select_set(False)
        for o in MESH: o.select_set(True)
        root.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.abspath(a[4:]), use_selection=True, export_format='GLB', export_apply=True,
                                  export_image_format='JPEG', export_jpeg_quality=92)
print('FINAL DONE', MODE, ACTS)
