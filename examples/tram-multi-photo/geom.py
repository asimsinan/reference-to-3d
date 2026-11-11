# Blender: the tram as named mesh objects, built from params.json (metres; +X front, +Y left, z = 0 rail top).
# The rear end is the front turned 180 deg about z (a double-ended car).
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'params.json')))
hw, Xs, Xf, ac, xo = D['hw'], D['Xs'], D['Xf'], D['ac'], D['xo']
EXT = D['ext_len']

OBJS = []

def clear():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for c in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for b in list(c): c.remove(b)

def mk(name, verts, faces, mats=None, smooth=False, solid=0.0):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    if mats is not None:
        for i, mi in enumerate(mats): me.polygons[i].material_index = mi
    if smooth:
        for p in me.polygons: p.use_smooth = True
    if solid:
        md = o.modifiers.new('sol', 'SOLIDIFY'); md.thickness = solid; md.offset = -1; md.use_even_offset = True
    OBJS.append(o); return o

class MB:
    """mesh builder"""
    def __init__(s): s.v = []; s.f = []; s.m = []
    def add(s, pts):
        i = len(s.v); s.v += [tuple(p) for p in pts]; return list(range(i, i + len(pts)))
    def face(s, idx, mat=0): s.f.append(list(idx)); s.m.append(mat)
    def quad(s, a, b, c, d, mat=0): s.face(s.add([a, b, c, d]), mat)
    def build(s, name, **kw): return mk(name, s.v, s.f, s.m, **kw)

def rotz180(p): return (-p[0], -p[1], p[2])

def wall_segment(mb, p0, p1, za, zb, holes, mat=0):
    """vertical wall along p0->p1 (plan), outward normal on the right of travel for a CCW polygon.
    holes: list of (s0, s1, z0, z1) in metres along the segment. Grid split so no face covers a hole."""
    L = math.dist(p0, p1); dx, dy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    ss = sorted(set([0.0, L] + [h[0] for h in holes] + [h[1] for h in holes]))
    zz = sorted(set([za, zb] + [h[2] for h in holes] + [h[3] for h in holes]))
    P = lambda s, z: (p0[0] + dx * s, p0[1] + dy * s, z)
    for i in range(len(ss) - 1):
        for j in range(len(zz) - 1):
            sm, zm = (ss[i] + ss[i + 1]) / 2, (zz[j] + zz[j + 1]) / 2
            if any(h[0] <= sm <= h[1] and h[2] <= zm <= h[3] for h in holes): continue
            mb.quad(P(ss[i], zz[j]), P(ss[i + 1], zz[j]), P(ss[i + 1], zz[j + 1]), P(ss[i], zz[j + 1]), mat)

def panes(mb, p0, p1, holes, inset):
    L = math.dist(p0, p1); dx, dy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L; nx, ny = dy, -dx
    for s0, s1, z0, z1 in holes:
        P = lambda s, z: (p0[0] + dx * s - nx * inset, p0[1] + dy * s - ny * inset, z)
        mb.quad(P(s0, z0), P(s1, z0), P(s1, z1), P(s0, z1))

# ---------------------------------------------------------------- plan
def nose_pts(front=True):
    pts = [(xo, -hw), (Xf, -ac), (Xf, ac), (xo, hw)]
    return pts if front else [(-x, -y) for x, y in pts]

POLY = [(-xo, -hw), (xo, -hw), (Xf, -ac), (Xf, ac), (xo, hw), (-xo, hw), (-Xf, ac), (-Xf, -ac)]  # CCW

def side_extent(side):
    # +Y: wall from -Xs to Xs+EXT ; -Y: from -Xs-EXT to Xs  (rotational symmetry of the door-leaf panel)
    return (-Xs, Xs + EXT) if side > 0 else (-Xs - EXT, Xs)

def build_body():
    zs, zws, zwd, zb = D['zs'], D['zws'], D['zwd'], D['zband']
    # lower side walls (red panels)
    for side, nm in ((1, 'L'), (-1, 'R')):
        a, b = side_extent(side)
        p0, p1 = ((b, hw), (a, hw)) if side > 0 else ((a, -hw), (b, -hw))
        mb = MB(); wall_segment(mb, p0, p1, zs, zws, []); mb.build('side_lower_' + nm, solid=0.03)
        # window band with the side windows
        mb = MB(); holes = []
        L = math.dist(p0, p1)
        for w0, w1 in D['side_win']:
            xa, xb = (w0, w1) if side < 0 else (w0, w1)
            s0 = (p0[0] - max(w0, w1)) if side > 0 else (min(w0, w1) - p0[0])
            s1 = s0 + abs(w0 - w1)
            holes.append((s0, s1, D['zwin_lo'], zb - 0.03))
        wall_segment(mb, p0, p1, zws, zb, holes); mb.build('side_upper_' + nm, solid=0.03)
        mg = MB(); panes(mg, p0, p1, holes, 0.035); mg.build('glass_side_' + nm)
    # the nose at each end: dash below, cab windows above
    for front, nm in ((True, 'F'), (False, 'B')):
        pts = nose_pts(front)
        mbl = MB(); mbu = MB(); mg = MB()
        for i in range(3):
            p0, p1 = pts[i], pts[i + 1]; L = math.dist(p0, p1)
            if i == 1:
                holes = [(0.04, L / 2 - 0.025, zwd + 0.05, zb - 0.05), (L / 2 + 0.025, L - 0.04, zwd + 0.05, zb - 0.05)]
            else:
                holes = [(0.17 * L, 0.83 * L, zwd + 0.05, zb - 0.05)]
            wall_segment(mbl, p0, p1, 0.72, zwd, [])
            wall_segment(mbu, p0, p1, zwd, zb, holes)
            panes(mg, p0, p1, holes, 0.03)
        mbl.build('dash_' + nm, solid=0.03); mbu.build('cab_' + nm, solid=0.03); mg.build('glass_cab_' + nm)
    # bulkheads (saloon end walls facing the platforms) with a doorway
    for front, nm in ((True, 'F'), (False, 'B')):
        x = Xs if front else -Xs; hb = hw - 0.03     # 3 cm inside the side walls: no rim showing on their outer face
        p0, p1 = ((x, -hb), (x, hb)) if front else ((x, hb), (x, -hb))
        mb = MB(); hole = [(hb - 0.36, hb + 0.36, D['zfloor'], 2.30)]
        wall_segment(mb, p0, p1, D['zfloor'], zb, hole); mb.build('bulkhead_' + nm, solid=0.03)
        mg = MB(); panes(mg, p0, p1, [(hb - 0.36, hb + 0.36, 1.45, 2.25)], -0.0); mg.build('glass_door_' + nm)
        mb = MB(); wall_segment(mb, p0, p1, D['zfloor'], 1.45, []); # door leaf lower half (closed sliding door)
        # keep only the doorway part of that wall: rebuild narrowly
        mb = MB(); L = math.dist(p0, p1); dx, dy = (p1[0]-p0[0])/L, (p1[1]-p0[1])/L
        s0, s1 = hb - 0.36, hb + 0.36
        P = lambda s, z: (p0[0] + dx*s - dy*0.04, p0[1] + dy*s + dx*0.04, z)
        mb.quad(P(s0, D['zfloor']), P(s1, D['zfloor']), P(s1, 1.45), P(s0, 1.45)); mb.build('door_' + nm)

def build_floor():
    zf = D['zfloor']; mb = MB()
    pts = [(p[0], p[1], zf) for p in POLY]
    mb.face(mb.add(pts)); mb.build('floor', solid=0.06)

PROF = [(0.0, 2.92), (0.06, 2.99), (0.15, 3.05), (0.3, 3.12), (0.5, 3.19), (0.7, 3.23), (0.891, D['roof_c'])]
def prof(s):
    d = s * 0.891
    for (d0, z0), (d1, z1) in zip(PROF, PROF[1:]):
        if d <= d1: return z0 + (z1 - z0) * (d - d0) / (d1 - d0)
    return PROF[-1][1]

def perimeter(n_per_m=30):
    out = []
    for i in range(len(POLY)):
        p0, p1 = POLY[i], POLY[(i + 1) % len(POLY)]; L = math.dist(p0, p1); n = max(2, int(L * n_per_m))
        for k in range(n): t = k / n; out.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))
    return out

def vnormal(pts, i):
    a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
    def n(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy); return (dy / L, -dx / L)
    n1, n2 = n(a, b), n(b, c); x, y = n1[0] + n2[0], n1[1] + n2[1]; L = math.hypot(x, y); return (x / L, y / L)

def build_roof():
    B = perimeter(); N = len(B); Lc = Xf - 0.891
    rings = []
    # letterboard band (vertical), lip, then the cove and roof as a function of s
    rings.append([(b[0], b[1], D['zband']) for b in B])
    rings.append([(b[0], b[1], D['zlet']) for b in B])
    nrm = [vnormal(B, i) for i in range(N)]
    rings.append([(b[0] + n[0] * 0.04, b[1] + n[1] * 0.04, D['zlet']) for b, n in zip(B, nrm)])
    rings.append([(b[0] + n[0] * 0.04, b[1] + n[1] * 0.04, D['zlet'] + 0.035) for b, n in zip(B, nrm)])
    S = [0, 0.03, 0.07, 0.12, 0.18, 0.26, 0.36, 0.48, 0.62, 0.78, 1.0]
    for s in S:
        r = []
        for b in B:
            c = (max(-Lc, min(Lc, b[0])), 0.0)
            r.append((b[0] + s * (c[0] - b[0]), b[1] + s * (c[1] - b[1]), prof(s)))
        rings.append(r)
    mb = MB(); idx = [mb.add(r) for r in rings]
    for j in range(len(rings) - 1):
        mat = 0 if j < 3 + 4 else 1        # cream band, lip and cove; roof above
        for i in range(N):
            a, b2 = idx[j][i], idx[j][(i + 1) % N]; c, d = idx[j + 1][(i + 1) % N], idx[j + 1][i]
            mb.f.append([a, b2, c, d]); mb.m.append(mat)
    o = mb.build('roof', solid=0.03)
    # merge the collapsed ridge
    bpy.context.view_layer.objects.active = o
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges); bm.to_mesh(o.data); bm.free()
    # clerestory / monitor on the saloon roof
    box('monitor', -1.95, 1.95, -0.40, 0.40, D['roof_c'] - 0.06, D['roof_c'] + 0.17)
    box('roofboard', -2.3, 2.6, -0.22, 0.22, D['roof_c'] + 0.17, D['roof_c'] + 0.21)

def box(name, x0, x1, y0, y1, z0, z1, rot=None, solid=0):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    if rot: v = [rot(p) for p in v]
    f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    return mk(name, v, f)

def cyl(name, c, axis, r, L, n=24, cap=True, r2=None):
    axis = Vector(axis).normalized(); c = Vector(c)
    t = axis.orthogonal().normalized(); u = axis.cross(t)
    r2 = r if r2 is None else r2
    v = []; f = []
    for k in range(n):
        a = 2 * math.pi * k / n; d = t * math.cos(a) + u * math.sin(a)
        v.append(c - axis * L / 2 + d * r); v.append(c + axis * L / 2 + d * r2)
    for k in range(n):
        a, b = 2 * k, 2 * ((k + 1) % n); f.append([a, b, b + 1, a + 1])
    if cap:
        f.append([2 * k for k in range(n)][::-1]); f.append([2 * k + 1 for k in range(n)])
    o = mk(name, v, f)
    for p in o.data.polygons: p.use_smooth = len(p.vertices) == 4
    return o

def tube(name, pts, r, n=10):
    """polyline tube (bow collector, poles, handrails)"""
    mb = MB(); rings = []
    P = [Vector(p) for p in pts]
    for i, p in enumerate(P):
        d = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        t = d.orthogonal().normalized(); u = d.cross(t)
        rings.append(mb.add([p + (t * math.cos(2 * math.pi * k / n) + u * math.sin(2 * math.pi * k / n)) * r for k in range(n)]))
    for a, b in zip(rings, rings[1:]):
        for k in range(n): mb.face([a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]])
    o = mb.build(name)
    for p in o.data.polygons: p.use_smooth = True
    return o

def build_fender_bumper():
    for front, nm in ((True, 'F'), (False, 'B')):
        pts = [(xo - 0.30, -hw)] + nose_pts(True) + [(xo - 0.30, hw)]
        # dense smooth sampling of the polyline
        S = []
        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i + 1]; n = max(3, int(math.dist(p0, p1) * 30))
            for k in range(n): t = k / n; S.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))
        S.append(pts[-1])
        nr = []
        for i in range(len(S)):
            a, b = S[max(i - 1, 0)], S[min(i + 1, len(S) - 1)]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
            nr.append((dy / L, -dx / L))
        def out(p):  # outward reach: largest at the front centre, small along the sides
            ang = abs(math.atan2(p[1], max(p[0] - (xo - 0.6), 1e-3)))
            return 0.05 + (D['fend_out'] - 0.05) * max(0.0, math.cos(min(ang, math.pi / 2))) ** 1.2
        rows = [(0.0, D['zfend_top']), (0.45, D['zfend_top'] - 0.07), (0.8, D['zfend_bot'] + 0.07), (1.0, D['zfend_bot'])]
        mb = MB(); R = []
        for fr, z in rows:
            R.append(mb.add([(p[0] + n[0] * out(p) * fr, p[1] + n[1] * out(p) * fr, z) for p, n in zip(S, nr)]))
        for a, b in zip(R, R[1:]):
            for i in range(len(S) - 1): mb.face([a[i + 1], a[i], b[i], b[i + 1]])
        o = mb.build('fender_' + nm, solid=0.012)
        for p in o.data.polygons: p.use_smooth = True
        if not front: o.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
        # bumper beam: a band following the nose, below the fender
        mb = MB(); z0, z1 = D['zbump']
        R0 = mb.add([(p[0] + n[0] * 0.06, p[1] + n[1] * 0.06, z0) for p, n in zip(S, nr)])
        R1 = mb.add([(p[0] + n[0] * 0.06, p[1] + n[1] * 0.06, z1) for p, n in zip(S, nr)])
        for i in range(len(S) - 1): mb.face([R0[i + 1], R0[i], R1[i], R1[i + 1]])
        o = mb.build('bumper_' + nm, solid=0.10)
        if not front: o.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))

def build_under():
    zsol = D['zsol']
    for sd in (1, -1):
        box('solebar_' + ('L' if sd > 0 else 'R'), -xo + 0.1, xo - 0.1, sd * (hw - 0.09) - 0.04, sd * (hw - 0.09) + 0.04, zsol, D['zs'] + 0.01)
    box('underbody', -xo + 0.2, xo - 0.2, -hw + 0.13, hw - 0.13, zsol + 0.05, D['zfloor'] - 0.06)
    r = D['wheel_r']; gy = D['gauge'] / 2
    for ax in (D['axle_x'], -D['axle_x']):
        for sd in (1, -1):
            cyl('wheel_%s%s' % ('F' if ax > 0 else 'B', 'L' if sd > 0 else 'R'), (ax, sd * (gy + 0.03), r), (0, 1, 0), r, 0.09, n=40)
            cyl('flange_%s%s' % ('F' if ax > 0 else 'B', 'L' if sd > 0 else 'R'), (ax, sd * (gy - 0.025), r), (0, 1, 0), r + 0.025, 0.02, n=40)
            box('axlebox_%s%s' % ('F' if ax > 0 else 'B', 'L' if sd > 0 else 'R'), ax - 0.13, ax + 0.13, sd * 0.68 - 0.08, sd * 0.68 + 0.08, r - 0.12, r + 0.12)
            # leaf spring: a shallow arc of plates above the axle box
            pts = [(ax + t * 0.55, sd * 0.68, r + 0.16 + 0.10 * (1 - t * t)) for t in [i / 8 - 1 for i in range(17)]]
            tube('spring_%s%s' % ('F' if ax > 0 else 'B', 'L' if sd > 0 else 'R'), pts, 0.035, n=8)
        cyl('axle_' + ('F' if ax > 0 else 'B'), (ax, 0, r), (0, 1, 0), 0.06, 2 * gy + 0.3, n=16)
        box('motor_' + ('F' if ax > 0 else 'B'), ax - (0.75 if ax > 0 else -0.15) , ax - (0.15 if ax > 0 else -0.75), -0.35, 0.35, 0.18, 0.62)
    # brake rods between the axles, both sides
    for sd in (1, -1):
        tube('brakerod_' + ('L' if sd > 0 else 'R'), [(-1.3, sd * 0.62, 0.30), (1.3, sd * 0.62, 0.30)], 0.02, n=8)

def build_steps():
    zs = D['step_z']
    for front in (True, False):
        for sd in (1, -1):
            if front: a = (Xs + EXT if sd > 0 else Xs) + 0.05; b = xo - 0.05
            else: a = -xo + 0.05; b = -(Xs + EXT if sd < 0 else Xs) - 0.05
            nm = 'step_%s%s' % ('F' if front else 'B', 'L' if sd > 0 else 'R')
            y0, y1 = sorted([sd * (hw - 0.10), sd * (hw + 0.17)])
            box(nm, a, b, y0, y1, zs - 0.04, zs)
            box(nm + '_riser', a, b, *sorted([sd * (hw - 0.10), sd * (hw - 0.07)]), zs, D['zfloor'])
            for x in (a + 0.04, b - 0.04):
                box(nm + '_hang%d' % (x > 0), x - 0.02, x + 0.02, *sorted([sd * (hw + 0.10), sd * (hw + 0.14)]), zs, D['zs'] + 0.02)

def build_ends():
    for front, nm in ((True, 'F'), (False, 'B')):
        R = (lambda p: p) if front else rotz180
        objs = []
        hx, hy, hz = D['hl']
        objs.append(cyl('headlamp_' + nm, R((Xf + 0.06, 0, hz)), (1, 0, 0), 0.20, 0.12, n=40))
        objs.append(cyl('headglass_' + nm, R((Xf + 0.125, 0, hz)), (1, 0, 0), 0.145, 0.01, n=40))
        bx, by, bz = D['bolt']
        for s in (1, -1):
            objs.append(cyl('bolt_%s%d' % (nm, s > 0), R((Xf + 0.03, s * by, bz)), (1, 0, 0), 0.045, 0.06, n=20))
        sx, sy, sz = D['sl']
        for s in (1, -1):
            o = box('siglamp_%s%d' % (nm, s > 0), sx - 0.06, sx + 0.07, s * sy - 0.085, s * sy + 0.085, sz - 0.10, sz + 0.10, rot=R)
            cyl('siglens_%s%d' % (nm, s > 0), R((sx + 0.075, s * sy, sz)), (1 if front else -1, 0, 0), 0.07, 0.015, n=28)
            cyl('sigpost_%s%d' % (nm, s > 0), R((sx, s * sy, (2.9 + sz - 0.1) / 2)), (0, 0, 1), 0.022, sz - 0.1 - 2.9, n=10)
        kx, _, kz = D['sign']
        box('sign_' + nm, kx - 0.02, kx + 0.02, -0.53, 0.53, 2.99, 3.21, rot=R)
        # "4" tab with a rounded top
        tab = [(0.11 * math.cos(a), 3.21 + 0.10 + 0.11 * math.sin(a)) for a in [math.pi * i / 12 for i in range(13)]]
        pts = [(-0.11, 3.21)] + [(-y, z) for y, z in tab[::-1]][::-1] + [(0.11, 3.21)]
        pts = [(0.11, 3.21)] + [(0.11 * math.cos(a), 3.31 + 0.11 * math.sin(a)) for a in [math.pi * i / 12 for i in range(13)]] + [(-0.11, 3.21)]
        mb = MB(); fr = mb.add([R((kx + 0.02, y, z)) for y, z in pts]); bk = mb.add([R((kx - 0.02, y, z)) for y, z in pts])
        mb.face(fr if front else fr[::-1]); mb.face(bk[::-1] if front else bk)
        n = len(pts)
        for i in range(n): mb.face([fr[i], bk[i], bk[(i + 1) % n], fr[(i + 1) % n]] if front else [fr[(i + 1) % n], bk[(i + 1) % n], bk[i], fr[i]])
        mb.build('signtab_' + nm)
        for s in (1, -1):
            cyl('signpost_%s%d' % (nm, s > 0), R((kx, s * 0.40, 2.97)), (0, 0, 1), 0.02, 0.12, n=10)
        # small lamps on the hood's front, under the sign
        cyl('toplamp_' + nm, R((Xf - 0.02, 0, 2.93)), (1, 0, 0), 0.05, 0.09, n=20)
        cyl('toplamp2_' + nm, R((Xf + 0.02, 0, 2.80)), (1, 0, 0), 0.04, 0.07, n=20)
        # mirror on the +Y front corner post (rotational copy at the rear)
        tube('mirrorarm_' + nm, [R((xo - 0.04, hw, 2.47)), R((xo - 0.04, hw + 0.16, 2.47))], 0.012, n=8)
        box('mirror_' + nm, xo - 0.09, xo - 0.03, hw + 0.13, hw + 0.30, 2.22, 2.72, rot=R)
        # coupler with its link
        box('coupler_' + nm, Xf + 0.05, Xf + 0.42, -0.08, 0.08, 0.33, 0.45, rot=R)
        tube('chain_' + nm, [R((Xf + 0.40, 0.0, 0.33)), R((Xf + 0.44, 0.03, 0.26)), R((Xf + 0.42, -0.03, 0.21))], 0.025, n=8)

def build_poles_gates():
    for front in (True, False):
        for sd in (1, -1):
            if front: a = (Xs + EXT if sd > 0 else Xs); b = xo
            else: a = -xo; b = -(Xs + EXT if sd < 0 else Xs)
            nm = '%s%s' % ('F' if front else 'B', 'L' if sd > 0 else 'R')
            y = sd * (hw - 0.04)
            tube('pole_%s0' % nm, [(a + 0.04, y, D['zfloor']), (a + 0.04, y, D['zband'])], 0.018)
            tube('pole_%s1' % nm, [(b - 0.04, y, D['zfloor']), (b - 0.04, y, D['zband'])], 0.018)
            mb = MB(); gy = sd * (hw - 0.07)
            p0, p1 = ((b - 0.07, gy), (a + 0.07, gy)) if sd > 0 else ((a + 0.07, gy), (b - 0.07, gy))
            wall_segment(mb, p0, p1, 0.86, 2.34, []); mb.build('gate_' + nm)

BOW = dict(x0=0.202, z0=3.491, s=1.008, us=1.674, th=-0.583, th2=-0.31)
def bow_pt(u, v):
    p = BOW; u = u * p['s'] * p['us']; v = v * p['s']; vw = 1.05 * p['s']; th = p['th']
    if v <= vw: return (p['x0'] + v * math.sin(th), u, p['z0'] + v * math.cos(th))
    bx, bz = p['x0'] + vw * math.sin(th), p['z0'] + vw * math.cos(th); t = th + p['th2']
    return (bx + (v - vw) * math.sin(t), u, bz + (v - vw) * math.cos(t))

def build_bow():
    # Lyra bow collector (the photos' "keyhole" frame): two arms from a pivot on the roof board, a waist, a wide loop
    # with the contact strip across its top; pose fitted to photo 6 (it follows the wire, so it differs between photos)
    zb = D['roof_c'] + 0.21
    box('bowbase', BOW['x0'] - 0.25, BOW['x0'] + 0.25, -0.36, 0.36, zb, BOW['z0'])
    side = [(0.32, 0.0), (0.24, 0.45), (0.12, 1.05), (0.26, 1.13), (0.40, 1.25), (0.47, 1.42), (0.46, 1.60), (0.40, 1.73), (0.30, 1.78)]
    outline = [(-u, v) for u, v in side] + [(u, v) for u, v in side[::-1]]
    outline = [(-u, v) for u, v in side] + [(0.0, 1.785)] + [(u, v) for u, v in side[::-1]]
    tube('bowframe', [bow_pt(u, v) for u, v in outline], 0.016)
    tube('bowstrip', [bow_pt(-0.30, 1.79), bow_pt(0.30, 1.79)], 0.022)
    tube('bowwaist', [bow_pt(-0.12, 1.05), bow_pt(0.12, 1.05)], 0.012)
    for sg in (1, -1): tube('bowdiag_%d' % (sg > 0), [bow_pt(0, 1.05), bow_pt(sg * 0.22, 1.78)], 0.010)
    for v in (0.22, 0.36):
        w = 0.32 - (0.32 - 0.24) * v / 0.45
        tube('bowrung_%d' % int(v * 100), [bow_pt(-w, v), bow_pt(w, v)], 0.012)
    c = bow_pt(0.10, 0.30); n = (math.cos(BOW['th']), 0, -math.sin(BOW['th']))
    box('voltsign', c[0] - 0.015, c[0] + 0.015, c[1] - 0.12, c[1] + 0.12, c[2] - 0.07, c[2] + 0.07)
    for sg in (1, -1):
        tube('bowspring_%d' % (sg > 0), [(BOW['x0'] + 0.20, sg * 0.30, zb + 0.02), bow_pt(sg * 0.27, 0.30)], 0.010)

def build_interior():
    zf = D['zfloor']
    for sd in (1, -1):
        y0, y1 = sorted([sd * (hw - 0.05), sd * (hw - 0.50)])
        box('bench_seat_' + ('L' if sd > 0 else 'R'), -2.05, 2.05, y0, y1, zf + 0.40, zf + 0.46)
        box('bench_base_' + ('L' if sd > 0 else 'R'), -2.05, 2.05, *sorted([sd * (hw - 0.08), sd * (hw - 0.45)]), zf, zf + 0.40)
        box('bench_back_' + ('L' if sd > 0 else 'R'), -2.05, 2.05, *sorted([sd * (hw - 0.05), sd * (hw - 0.10)]), zf + 0.46, zf + 0.95)
    box('ceiling', -2.12, 2.12, -hw + 0.04, hw - 0.04, 2.70, 2.71)
    # driver's controller at each end
    for front in (True, False):
        R = (lambda p: p) if front else rotz180
        cyl('controller_' + ('F' if front else 'B'), R((Xf - 0.30, -0.25, zf + 0.5)), (0, 0, 1), 0.12, 1.0, n=20)

def build_all():
    clear()
    build_body(); build_floor(); build_roof(); build_fender_bumper(); build_under(); build_steps()
    build_ends(); build_poles_gates(); build_bow(); build_interior()
    return [o for o in bpy.data.objects if o.type == 'MESH']

if __name__ == '__main__':
    obs = build_all()
    print('objects', len(obs))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'out', 'geom.blend'))
