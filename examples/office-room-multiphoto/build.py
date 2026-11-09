"""Build the office room in Blender from room_final.json + tex/.

  Blender -b --factory-startup -P build.py -- OUT.blend
Room frame: x across (0 = recessed left wall, W = right wall), y along (0 = window wall, L = door wall), z up, metres.
"""
import json
import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.join(HERE, 'oda_build.blend')
R = json.load(open(os.path.join(HERE, 'room_final.json')))
TJ = json.load(open(os.path.join(HERE, 'tex', 'tex.json')))
W, L, H = R['W'], R['L'], R['H']
d, d2, r0, rz, p = R['d'], R['d2'], R['r0'], R['rz'], R['p']
T = lambda n: os.path.join(HERE, 'tex', n)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
COL = {}
for n in ('Room', 'Furniture', 'Lights'):
    c = bpy.data.collections.new(n); sc.collection.children.link(c); COL[n] = c
ROOT = bpy.data.objects.new('Oda', None); COL['Room'].objects.link(ROOT)


# ---------------------------------------------------------------- materials
def srgb(c):
    return [((v / 255) / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4) for v in c] + [1]


WIN_EMIT = 5.0


def mat(name, color=None, rough=0.5, metal=0.0, img=None, alpha_img=False, emit=None, emit_img=None, emit_mask=None, emit_strength=1.0, emit_full=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if color: b.inputs['Base Color'].default_value = srgb(color)
    if img:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(T(img)); t.location = (-400, 200)
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
        if alpha_img:
            nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
            m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
            try: m.surface_render_method = 'BLENDED'
            except Exception: pass
        if emit_full:
            nt.links.new(t.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emit_strength
            nt.links.remove(b.inputs['Base Color'].links[0]); b.inputs['Base Color'].default_value = (0, 0, 0, 1)
        if emit_mask:
            mk = nt.nodes.new('ShaderNodeTexImage'); mk.image = bpy.data.images.load(T(emit_mask)); mk.location = (-400, -200)
            mk.image.colorspace_settings.name = 'Non-Color'
            mul = nt.nodes.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs['Fac'].default_value = 1
            nt.links.new(t.outputs['Color'], mul.inputs[1]); nt.links.new(mk.outputs['Color'], mul.inputs[2])
            nt.links.new(mul.outputs['Color'], b.inputs['Emission Color'])
            b.inputs['Emission Strength'].default_value = emit_strength
    if emit:
        b.inputs['Emission Color'].default_value = srgb(emit); b.inputs['Emission Strength'].default_value = emit_strength
    return m


wb = TJ['wall_bgr']
M = {
    'paint': mat('Wall paint', (wb[2], wb[1], wb[0]), rough=0.85),
    'ceiling': mat('Ceiling paint', (246, 246, 245), rough=0.9),
    'floor': mat('Laminate floor', img='floor_tile.jpg', rough=0.35),
    'maple': mat('Maple melamine', img='maple.jpg', rough=0.45),
    'skirt': mat('Skirting', (150, 100, 62), rough=0.5),
    'fabric': mat('Chair fabric black', (28, 27, 30), rough=0.95),
    'fabric2': mat('Chair fabric brown', (48, 32, 34), rough=0.95),
    'steel': mat('Black steel', (20, 20, 22), rough=0.35, metal=0.8),
    'chrome': mat('Chrome', (220, 220, 225), rough=0.12, metal=1.0),
    'white_plastic': mat('White plastic', (225, 226, 222), rough=0.4),
    'grey_plastic': mat('Dark plastic', (45, 46, 50), rough=0.4),
    'enamel': mat('Radiator enamel', (236, 234, 226), rough=0.3),
    'tube': mat('Fluorescent tube', (250, 250, 250), rough=0.2, emit=(255, 252, 244), emit_strength=6.0),
    'window': mat('Window wall (photo)', img='window_wall_c_rgba.png', alpha_img=True, rough=0.6, emit_strength=WIN_EMIT, emit_full=True),
    'door': mat('Door (photo)', img='door_rgba.png', alpha_img=True, rough=0.5),
    'switch': mat('Switch (photo)', img='switch_rgba.png', alpha_img=True, rough=0.5),
    'bookcase': mat('Bookcase front (photo)', img='bookcase_lit.jpg', rough=0.5),
    'tallcab': mat('Tall cabinet front (photo)', img='tallcab_lit.jpg', rough=0.45),
    'screen': mat('Laptop screen', (12, 14, 20), rough=0.15, emit=(40, 60, 90), emit_strength=0.6),
    'mug': mat('Mug', (240, 240, 238), rough=0.2),
    'red': mat('Flowers red', (200, 30, 60), rough=0.7), 'yellow': mat('Flowers yellow', (240, 200, 30), rough=0.7),
    'whitef': mat('Flowers white', (245, 245, 240), rough=0.7), 'leaf': mat('Leaves', (40, 90, 40), rough=0.7),
    'clockface': mat('Clock face', (245, 245, 245), rough=0.3),
}


# ---------------------------------------------------------------- geometry helpers
def obj_from_bm(name, bm, m, col='Furniture', parent=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); COL[col].objects.link(o)
    if isinstance(m, list):
        for mm in m: me.materials.append(mm)
    else: me.materials.append(m)
    o.parent = parent or ROOT
    return o


def add_box(bm, x0, x1, y0, y1, z0, z1, uvs=0.6, mi=0):
    """box with per-face UVs: face-local metres / uvs (grain vertical on side faces)."""
    uv = bm.loops.layers.uv.verify()
    V = [bm.verts.new(v) for v in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for f in F:
        face = bm.faces.new([V[i] for i in f]); face.material_index = mi
        n = face.normal
        for lp in face.loops:
            co = lp.vert.co
            if abs(n.z) > 0.5: a, b = co.x, co.y
            elif abs(n.x) > 0.5: a, b = co.y, co.z
            else: a, b = co.x, co.z
            lp[uv].uv = (a / uvs, b / uvs)


def box(name, x0, x1, y0, y1, z0, z1, m, uvs=0.6, col='Furniture', parent=None, bevel=0.0):
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1, uvs)
    o = obj_from_bm(name, bm, m, col, parent)
    if bevel:
        md = o.modifiers.new('Bevel', 'BEVEL'); md.width = bevel; md.segments = 3; md.limit_method = 'ANGLE'
    return o


def plane(name, origin, u, v, us, vs, m, col='Room', uv_tile=None, flip=False):
    """quad origin + a*u + b*v, a in [0,us], b in [0,vs]; UV 0..1 (or metres/uv_tile)."""
    o_, u_, v_ = Vector(origin), Vector(u), Vector(v)
    P = [o_, o_ + u_ * us, o_ + u_ * us + v_ * vs, o_ + v_ * vs]
    UV = [(0, 0), (1, 0), (1, 1), (0, 1)] if not uv_tile else [(0, 0), (us / uv_tile[0], 0), (us / uv_tile[0], vs / uv_tile[1]), (0, vs / uv_tile[1])]
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify(); vs_ = [bm.verts.new(q) for q in P]
    f = bm.faces.new(vs_[::-1] if flip else vs_)
    for lp in f.loops: lp[uv].uv = UV[vs_.index(lp.vert)]
    return obj_from_bm(name, bm, m, col)


def cyl(name, p0, p1, r, m, seg=16, col='Furniture', parent=None):
    p0, p1 = Vector(p0), Vector(p1); dv = p1 - p0
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=dv.length)
    rot = dv.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((p0 + p1) / 2) @ rot, verts=bm.verts)
    return obj_from_bm(name, bm, m, col, parent)


def sphere(name, c, r, m, col='Furniture', parent=None, scale=(1, 1, 1)):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*scale, 1)), verts=bm.verts)
    return obj_from_bm(name, bm, m, col, parent)


# ---------------------------------------------------------------- shell
t = 0.12
box('Wall right', W, W + t, 0, L, 0, H, M['paint'], col='Room')
box('Wall left', -t, 0, 0, L, 0, H, M['paint'], col='Room')
box('Chase', 0, d, 0, r0, 0, H, M['paint'], col='Room')
box('Beam', 0, d, r0, L - p, rz, H, M['paint'], col='Room')
box('Pilaster', 0, d2, L - p, L, 0, H, M['paint'], col='Room')
fl = plane('Floor', (0, 0, 0), (1, 0, 0), (0, 1, 0), W, L, M['floor'], uv_tile=TJ['floor_tile_m'])
plane('Ceiling', (0, 0, H), (1, 0, 0), (0, 1, 0), W, L, M['ceiling'], flip=True)
# photo decals (2 mm off the walls)
plane('Switch photo', (1.55, L - 0.003, 1.16), (1, 0, 0), (0, 0, 1), 0.18, 0.18, M['switch'], flip=True)
# skirting (6 cm high, 1.2 cm proud)
sk, st = 0.06, 0.012
for nm, a in (('Skirting right', (W - st, W, 0, L)), ('Skirting door', (d2, R['dx0'], L - st, L)), ('Skirting door 2', (R['dx1'], W, L - st, L)),
              ('Skirting chase', (d, d + st, 0, r0)), ('Skirting chase end', (0, d, r0, r0 + st)),
              ('Skirting recess', (0, st, r0, L - p)), ('Skirting pilaster end', (0, d2, L - p - st, L - p)), ('Skirting pilaster', (d2, d2 + st, L - p, L))):
    box(nm, a[0], a[1], a[2], a[3], 0, sk, M['skirt'], col='Room')

# ---------------------------------------------------------------- furniture
F = {}
tx0, ty0, tw, th = W - R['tcd'], R['tc0'], R['tcw'], R['tch']
box('Tall cabinet', tx0 + 0.004, W, ty0, ty0 + tw, 0, th, M['maple'])
box('Tall cabinet door', tx0 - 0.004, tx0 + 0.006, ty0 + 0.003, ty0 + tw - 0.003, 0.06, th - 0.003, M['maple'])
cyl('Tall cabinet handle', (tx0 - 0.02, ty0 + tw - 0.05, 0.95), (tx0 - 0.02, ty0 + tw - 0.05, 1.07), 0.006, M['chrome'])
box('Tall cabinet plinth', tx0 + 0.03, W, ty0 + 0.01, ty0 + tw - 0.01, 0, 0.06, M['steel'])
# wall rail behind the right-hand chairs
box('Wall rail', W - 0.02, W, R['ry0'], R['ry1'], R['rzb'], R['rzt'], M['maple'])
# coffee table (box with a 2.5 cm top), flower cart and clock
cx0, cx1, cy0, cy1, ch = 1.06, 1.51, 1.72, 2.50, 0.42
box('Coffee table body', cx0 + 0.015, cx1 - 0.015, cy0 + 0.015, cy1 - 0.015, 0, ch - 0.025, M['maple'])
box('Coffee table top', cx0, cx1, cy0, cy1, ch - 0.025, ch, M['maple'])
# L desk: main desk across the room, return along the left wall (chase)
dz = 0.745
box('Desk top', 0.10, 1.50, 0.95, 1.60, dz - 0.025, dz, M['maple'])
box('Desk return top', d, 0.75, 0.0, 0.95, dz - 0.025, dz, M['maple'])
box('Desk return panel', d, 0.75, 0.02, 0.045, 0, dz - 0.025, M['maple'])
box('Desk end panel', 1.47, 1.50, 0.97, 1.58, 0, dz - 0.025, M['maple'])
cyl('Desk leg', (0.73, 0.93, 0), (0.73, 0.93, dz - 0.025), 0.03, M['chrome'])
# low drawer pedestal with the pencil cup
box('Pedestal', 1.56, 1.98, 1.18, 1.62, 0, 0.60, M['maple'])
# printer cabinet + printer + bag, near the window on the right wall
box('Printer cabinet', 2.03, W - 0.01, 0.05, 0.55, 0, 0.50, M['maple'])
# radiator: cast-iron columns under window A
rx0, rx1 = 1.50, 1.86
n = 9
for i in range(n):
    x = rx0 + (i + 0.5) * (rx1 - rx0) / n
    box(f'Radiator col {i}', x - 0.016, x + 0.016, 0.03, 0.13, 0.20, 0.77, M['enamel'], bevel=0.008)
cyl('Radiator pipe', (rx0 - 0.05, 0.08, 0.24), (rx1 + 0.02, 0.08, 0.24), 0.012, M['enamel'])


# ---------------------------------------------------------------- lights for rendering (glTF viewer has its own)
def area(name, loc, rot, size, energy, color=(1, 1, 1), shape='RECTANGLE', size_y=None):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.color = color; ld.shape = shape; ld.size = size
    if size_y: ld.size_y = size_y
    o = bpy.data.objects.new(name, ld); COL['Lights'].objects.link(o); o.location = loc; o.rotation_euler = rot
    return o


area('Daylight window A', ((R['xA0'] + R['xA1']) / 2, 0.05, 1.65), (math.radians(-90), 0, 0), 0.8, 900, (1.0, 0.97, 0.92), 'RECTANGLE', 1.2)
area('Daylight window B', ((R['xB0'] + R['xB1']) / 2, 0.05, 1.65), (math.radians(-90), 0, 0), 0.9, 900, (1.0, 0.97, 0.92), 'RECTANGLE', 1.2)
area('Fixture door', (R['xl'], (R['yl0'] + R['yl1']) / 2, H - 0.08), (0, 0, 0), 0.15, 260, (1, 0.98, 0.94), 'RECTANGLE', 1.2)
area('Fixture window', (1.40, 1.15, H - 0.08), (0, 0, 0), 0.15, 200, (1, 0.98, 0.94), 'RECTANGLE', 1.2)
exec(open(os.path.join(HERE, 'build_detail.py')).read())
sc.world = bpy.data.worlds.new('World'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.9, 0.93, 1.0, 1)
sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.15
sc.render.engine = 'CYCLES'; sc.cycles.samples = 96; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = -3.3

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('saved', OUT, len(bpy.data.objects), 'objects')
