# Parametric 737-800 geometry (Blender, bmesh). Frame: +X front, +Y aircraft's left, +Z up, metres.
# Stations s are metres aft of the nose tip, X = X0 - s.
import bpy, bmesh, math, json
from mathutils import Vector, Matrix
import importlib, secs as secs_mod
importlib.reload(secs_mod)

def loft(name, rings, cap0=True, cap1=True, closed=True, smooth=True, us=None):
    """rings: list of lists of (x,y,z), same length each. UV: u along the rings (cumulative centroid distance,
    normalised, or `us`), v around each ring (vertex index / n, wrapping to 1.0 at the seam)."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in r] for r in rings]
    n = len(rings[0])
    if us is None:
        cs = [Vector(tuple(sum(p[k] for p in r) / len(r) for k in range(3))) for r in rings]
        d = [0.0]
        for c0, c1 in zip(cs[:-1], cs[1:]): d.append(d[-1] + (c1 - c0).length)
        us = [x / max(d[-1], 1e-9) for x in d]
    uvl = bm.loops.layers.uv.new('UVMap')
    def setuv(f, uvs):
        for lp, uv in zip(f.loops, uvs): lp[uvl].uv = uv
    for r, (a, b) in enumerate(zip(vs[:-1], vs[1:])):
        for i in range(n if closed else n - 1):
            j = (i + 1) % n; vj = 1.0 if j == 0 else j / n
            try:
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
                setuv(f, [(us[r], i / n), (us[r], vj), (us[r + 1], vj), (us[r + 1], i / n)])
            except ValueError: pass
    for cap, ring, rev, u in ((cap0, vs[0], True, us[0]), (cap1, vs[-1], False, us[-1])):
        if not cap: continue
        c = Vector((0, 0, 0))
        for v in ring: c += v.co
        c /= len(ring); cv = bm.verts.new(c)
        for i in range(n):
            j = (i + 1) % n; vj = 1.0 if j == 0 else j / n
            f = (ring[j], ring[i], cv) if rev else (ring[i], ring[j], cv)
            try:
                ff = bm.faces.new(f)
                setuv(ff, [(u, vj), (u, i / n), (u, (i + 0.5) / n)] if rev else [(u, i / n), (u, vj), (u, (i + 0.5) / n)])
            except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob

from secs import lerp, smoothstep, fus_section, ring_xyz

def fuselage(P):
    return loft('fuselage', secs_mod.fuselage_rings(P), cap0=False, cap1=True)

# ---------------- lifting surfaces ----------------
def airfoil(n=28, t=0.12, camber=0.02):
    """closed loop from TE over the upper side to LE and back under: list of (xc 0..1 from LE, zc)."""
    up, lo = [], []
    for i in range(n + 1):
        b = math.pi * i / n; x = (1 - math.cos(b)) / 2
        yt = 5 * t * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        m, p = camber, 0.4
        yc = m / p ** 2 * (2 * p * x - x * x) if x < p else m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x * x)
        up.append((x, yc + yt)); lo.append((x, yc - yt))
    loop = list(reversed(up)) + lo[1:-1]
    return loop

def surface(name, secs, n=24, vertical=False):
    """secs: list of dicts {le:(x,y,z) leading edge point, chord, t, camber, twist(deg), normal axis}.
    Chord runs toward -X (aft). For horizontal surfaces thickness is along local up (z, tilted by dihedral 'up'),
    for vertical along y."""
    rings = []
    for S in secs:
        foil = airfoil(n, S['t'], S.get('camber', 0.0))
        le = Vector(S['le']); c = S['chord']
        up = Vector(S.get('up', (0, 0, 1) if not vertical else (0, 1, 0)))
        tw = math.radians(S.get('twist', 0.0))
        ring = []
        for xc, zc in foil:
            dx = -xc * c; dz = zc * c
            # twist about LE (nose up for +)
            dxr = dx * math.cos(tw) - dz * math.sin(tw) * 0
            ring.append(tuple(le + Vector((dx, 0, 0)) + up * (dz + (-dx) * math.sin(tw) * 0)))
        rings.append(ring)
    return loft(name, rings, cap0=True, cap1=True)

def wing(P, side):
    return surface('wing_' + side, secs_mod.wing_secs(P, side))

def htail(P, side):
    return surface('htail_' + side, secs_mod.htail_secs(P, side))

def fin(P):
    return surface('fin', secs_mod.fin_secs(P))

def nacelle(P, side):
    E = P['eng']; X0 = P['X0']; sg = 1 if side == 'L' else -1
    xf = X0 - E['s_front']; L = E['len']; Ro = E['r_out']
    # outer profile from lip (front) to nozzle (rear): (dx aft, radius)
    prof = [(0.0, E['r_lip_in']), (0.03, E['r_lip_in'] + 0.06), (0.10, Ro * 0.97), (0.3, Ro), (0.9, Ro * 1.02),
            (1.6, Ro * 1.0), (2.4, Ro * 0.94), (3.0, Ro * 0.82), (3.4, Ro * 0.72), (L * 0.86, Ro * 0.62)]
    n = 48; rings = []
    for dx, r in prof:
        ring = []
        for i in range(n):
            th = 2 * math.pi * i / n
            yy = r * math.cos(th); zz = r * math.sin(th)
            if zz < 0: zz *= E['flat_bot']          # flattened lower lip ("hamster pouch" inverted look)
            if zz < 0 and abs(yy) < r: pass
            ring.append((xf - dx, sg * E['y'] + yy * E['wscale'], E['z'] + zz))
        rings.append(ring)
    outer = loft('nacelle_' + side, rings, cap0=False, cap1=False)
    # inner duct + fan disc
    din = []
    for dx, r in ((0.0, E['r_lip_in']), (0.10, E['r_fan']), (0.20, E['r_fan'])):
        ring = []
        for i in range(n):
            th = 2 * math.pi * i / n; yy = r * math.cos(th); zz = r * math.sin(th)
            if zz < 0: zz *= E['flat_bot']
            ring.append((xf - dx, sg * E['y'] + yy * E['wscale'], E['z'] + zz))
        din.append(ring)
    duct = loft('duct_' + side, din, cap0=False, cap1=False)
    # fan face: flat disc with planar UV so the photo's fan can sit on it
    me = bpy.data.meshes.new('fan_' + side); bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rf = E['r_fan'] * 1.01; xd = xf - 0.18; cen = bm.verts.new((xd, sg * E['y'], E['z'])); ring = []
    for i in range(64):
        th = 2 * math.pi * i / 64; zz = rf * math.sin(th)
        if zz < 0: zz *= E['flat_bot']
        ring.append(bm.verts.new((xd, sg * E['y'] + rf * math.cos(th), E['z'] + zz)))
    for i in range(64):
        a_, b_ = ring[i], ring[(i + 1) % 64]
        f_ = bm.faces.new((cen, b_, a_)) if True else None
        for lp in f_.loops:
            co = lp.vert.co; lp[uvl].uv = (0.5 + (co.y - sg * E['y']) / (2 * rf), 0.5 + (co.z - E['z']) / (2 * rf))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    fan = bpy.data.objects.new('fan_' + side, me); bpy.context.scene.collection.objects.link(fan)
    # core nozzle and plug
    core = []
    for dx, r in ((L * 0.80, Ro * 0.55), (L * 0.86, Ro * 0.48), (L * 0.98, Ro * 0.36), (L * 1.02, Ro * 0.30)):
        core.append([(xf - dx, sg * E['y'] + r * math.cos(2 * math.pi * i / 32), E['z'] - 0.05 + r * math.sin(2 * math.pi * i / 32)) for i in range(32)])
    plug = []
    for dx, r in ((L * 1.0, 0.28), (L * 1.08, 0.2), (L * 1.16, 0.02)):
        plug.append([(xf - dx, sg * E['y'] + r * math.cos(2 * math.pi * i / 24), E['z'] - 0.05 + r * math.sin(2 * math.pi * i / 24)) for i in range(24)])
    c = loft('core_' + side, core, cap0=False, cap1=False); p = loft('plug_' + side, plug, cap0=False, cap1=True)
    # spinner
    sp = []
    for dx, r in ((0.0, 0.0), (0.04, 0.10), (0.10, 0.17), (0.17, 0.21)):
        sp.append([(xf - 0.03 - dx, sg * E['y'] + r * math.cos(2 * math.pi * i / 24), E['z'] + r * math.sin(2 * math.pi * i / 24)) for i in range(24)])
    spn = loft('spinner_' + side, sp, cap0=False, cap1=True)
    # pylon: slab from nacelle top to wing underside
    pr = []
    for dx, hz in ((0.6, 0.0), (1.6, 0.0), (L + 0.6, 0.0)):
        pass
    py = pylon(P, side)
    return [outer, duct, fan, c, p, spn, py]

def pylon(P, side):
    E = P['eng']; X0 = P['X0']; sg = 1 if side == 'L' else -1
    xf = X0 - E['s_front']; y = sg * E['y']; zt = E['z'] + E['r_out'] * 0.9
    w = 0.22; z_top = E['pylon_ztop']
    pts = [(xf - 0.5, zt), (xf - E['len'] + 0.2, zt - 0.1), (xf - E['len'] - 0.9, z_top - 0.25), (xf - 2.0, z_top + 0.1)]
    me = bpy.data.meshes.new('pylon_' + side); bm = bmesh.new()
    a = [bm.verts.new((x, y - w, z)) for x, z in pts]; b = [bm.verts.new((x, y + w, z)) for x, z in pts]
    bm.faces.new(a); bm.faces.new(list(reversed(b)))
    for i in range(4):
        j = (i + 1) % 4; bm.faces.new((a[j], a[i], b[i], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('pylon_' + side, me); bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new('bev', 'BEVEL'); m.width = 0.08; m.segments = 3
    return ob

# ---------------- gear ----------------
def cyl(name, center, axis, r, length, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=length, location=center)
    ob = bpy.context.active_object; ob.name = name
    ax = Vector(axis).normalized(); q = Vector((0, 0, 1)).rotation_difference(ax)
    ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = q
    for p in ob.data.polygons: p.use_smooth = True
    return ob

def wheel(name, c, r, w):
    bpy.ops.mesh.primitive_torus_add(major_radius=r - w * 0.42, minor_radius=w * 0.5, major_segments=48,
                                     minor_segments=16, location=c)
    t = bpy.context.active_object; t.name = name + '_tyre'; t.rotation_euler = (math.pi / 2, 0, 0)
    t.scale = (1, 1, 1.0)
    for p in t.data.polygons: p.use_smooth = True
    h = cyl(name + '_hub', c, (0, 1, 0), r * 0.62, w * 0.86)
    return [t, h]

def gear(P):
    G = P['gear']; X0 = P['X0']; obs = []
    xn = X0 - G['s_nose']; rn = G['r_nose']
    for sg in (1, -1):
        obs += wheel('nosewheel_%s' % ('L' if sg > 0 else 'R'), (xn, sg * 0.19, rn), rn, 0.2)
    obs.append(cyl('nose_strut', (xn, 0, rn + 0.6), (0, 0, 1), 0.08, 1.3))
    obs.append(cyl('nose_axle', (xn, 0, rn), (0, 1, 0), 0.06, 0.5))
    # nose gear housing/door (white) and the open bay ahead of it (dark), as read from the photo
    for nm, s0, s1, z0, z1, wd in (('ngdoor', 3.3, 5.1, 1.22, 1.70, 0.72), ('ngbay', 2.5, 3.3, 1.52, 1.85, 0.62)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(X0 - (s0 + s1) / 2, 0, (z0 + z1) / 2))
        b = bpy.context.active_object; b.name = nm; b.scale = (s1 - s0, wd, z1 - z0)
        bv = b.modifiers.new('bev', 'BEVEL'); bv.width = 0.06; bv.segments = 3
        obs.append(b)
    xm = X0 - G['s_main']; rm = G['r_main']
    for sg in (1, -1):
        y = sg * G['track']
        for k in (-1, 1):
            obs += wheel('mainwheel_%s%d' % ('L' if sg > 0 else 'R', k), (xm, y + k * 0.43, rm), rm, 0.4)
        obs.append(cyl('main_strut_' + ('L' if sg > 0 else 'R'), (xm, y, rm + 0.7), (0, -sg * 0.35, 1), 0.12, 1.8))
        obs.append(cyl('main_axle_' + ('L' if sg > 0 else 'R'), (xm, y, rm), (0, 1, 0), 0.08, 1.2))
    return obs

def belly(P):
    """wing-to-body fairing: a flattened bulge under the centre section."""
    B = P['belly']; X0 = P['X0']; rings = []
    n = 40
    for i in range(13):
        f = i / 12; s = lerp(B['s0'], B['s1'], f)
        k = math.sin(math.pi * f) ** 0.6
        a = P['fus_a'] * lerp(0.75, B['w'], k); zb = P['zc'] - P['fus_b'] - B['drop'] * k
        zt = P['zc'] - 0.6
        ring = []
        for j in range(n):
            th = 2 * math.pi * j / n
            c, s_ = math.cos(th), math.sin(th)
            zz = (zt + zb) / 2 + (zt - zb) / 2 * s_
            ring.append((X0 - s, a * math.copysign(abs(c) ** 0.8, c), zz))
        rings.append(ring)
    return loft('belly_fairing', rings)

def flap_fairings(P, side):
    W = P['wing']; X0 = P['X0']; sg = 1 if side == 'L' else -1; obs = []
    dih = math.radians(W['dihedral'])
    for y in W['ftf_y']:
        s_le = W['s_le_glove'] + (y - W['y_glove']) * math.tan(math.radians(W['sweep_le']))
        z = W['z_root'] + (y - W['y_root']) * math.tan(dih) - 0.15
        s0 = s_le + 1.5; L = W['ftf_len']; rings = []
        for i in range(9):
            f = i / 8; r = 0.26 * math.sin(math.pi * (0.05 + 0.9 * f)) ** 0.7
            rings.append([(X0 - (s0 + L * f), sg * y + r * 0.6 * math.cos(2 * math.pi * j / 16),
                           z - r * (0.5 + 0.5 * math.sin(2 * math.pi * j / 16)) * 1.25) for j in range(16)])
        obs.append(loft('ftf_%s_%.0f' % (side, y), rings))
    return obs

def build_all(P):
    obs = [fuselage(P), belly(P), fin(P)]
    for side in ('L', 'R'):
        obs.append(wing(P, side)); obs.append(htail(P, side)); obs += nacelle(P, side); obs += flap_fairings(P, side)
    obs += gear(P)
    return obs
