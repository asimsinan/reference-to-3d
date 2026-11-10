# Kiz Kulesi geometry (solve units: shaft half-width A = 3.25; +X the sunlit door face, +Y the annex side, z=0 terrace)
import bpy, bmesh, json, os
from math import cos, sin, pi, radians, sqrt, atan2
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))


def P():
    p = json.load(open(os.path.join(HERE, 'params.json')))
    return p


def new_obj(name, bm, smooth=False):
    if name == 'room': bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    if name not in ('flag', 'corbel'): bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if name in ('room', 'corbel'):
        bm.normal_update()
        for f in bm.faces:
            c = f.calc_center_median(); r = Vector((c.x, c.y, 0.0))
            if r.length > 1e-6 and f.normal.dot(r.normalized()) < -0.2: f.normal_flip()
    me = bpy.data.meshes.new(name); bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    if smooth:
        for f in me.polygons: f.use_smooth = True
    return o


def prism(bm, poly, z0, z1, cap=True):
    """poly: list of (x,y) counter-clockwise seen from above."""
    lo = [bm.verts.new((x, y, z0)) for x, y in poly]; hi = [bm.verts.new((x, y, z1)) for x, y in poly]
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    if cap:
        bm.faces.new(hi); bm.faces.new(lo[::-1])
    return lo, hi


def box(bm, x0, x1, y0, y1, z0, z1):
    return prism(bm, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def ngon(r, n=8, a0=0.0):
    return [(r * cos(a0 + 2 * pi * k / n), r * sin(a0 + 2 * pi * k / n)) for k in range(n)]


def lathe(bm, prof, n=8, a0=0.0, cap_top=True, cap_bot=True, cx=0.0, cy=0.0):
    """prof: [(r,z)...] bottom to top."""
    rings = [[bm.verts.new((cx + r * cos(a0 + 2 * pi * k / n), cy + r * sin(a0 + 2 * pi * k / n), z)) for k in range(n)] for r, z in prof]
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(n):
            j = (k + 1) % n; bm.faces.new((a[k], a[j], b[j], b[k]))
    if cap_top: bm.faces.new(rings[-1])
    if cap_bot: bm.faces.new(rings[0][::-1])
    return rings


def cyl_between(bm, p0, p1, r, n=6):
    p0 = Vector(p0); p1 = Vector(p1); d = (p1 - p0); L = d.length
    if L < 1e-6: return
    z = d.normalized(); x = z.orthogonal().normalized(); y = z.cross(x)
    a = [bm.verts.new(p0 + r * (cos(2 * pi * k / n) * x + sin(2 * pi * k / n) * y)) for k in range(n)]
    b = [bm.verts.new(p1 + r * (cos(2 * pi * k / n) * x + sin(2 * pi * k / n) * y)) for k in range(n)]
    for k in range(n):
        j = (k + 1) % n; bm.faces.new((a[k], a[j], b[j], b[k]))
    bm.faces.new(b); bm.faces.new(a[::-1])


def railing(bm, poly, z0, h, post_step, r=0.03, rails=(1.0, 0.12), corner_r=0.05):
    n = len(poly)
    for i in range(n):
        a = Vector((*poly[i], 0)); b = Vector((*poly[(i + 1) % n], 0)); L = (b - a).length
        for fz in rails:
            cyl_between(bm, (a.x, a.y, z0 + h * fz), (b.x, b.y, z0 + h * fz), r * 1.2, 5)
        m = max(1, int(round(L / post_step)))
        for k in range(m):
            p = a.lerp(b, k / m)
            cyl_between(bm, (p.x, p.y, z0), (p.x, p.y, z0 + h * (1.0 if k else 1.08)), corner_r if k == 0 else r, 5)


def merlons(bm, a, b, inward, z, p):
    """merlons along the outer edge a->b (xy), `inward` unit vector towards the courtyard."""
    a = Vector(a); b = Vector(b); d = (b - a); L = d.length; d.normalize(); inw = Vector(inward)
    n = max(2, int(round((L - p['mer_w']) / p['mer_pitch'])) + 1)
    pitch = (L - p['mer_w']) / (n - 1)
    for k in range(n):
        s = k * pitch
        c0 = a + d * s; c1 = a + d * (s + p['mer_w'])
        q = [c0, c1, c1 + inw * p['mer_t'], c0 + inw * p['mer_t']]
        poly = [(v.x, v.y) for v in q]
        # keep counter-clockwise
        area = sum(poly[i][0] * poly[(i + 1) % 4][1] - poly[(i + 1) % 4][0] * poly[i][1] for i in range(4))
        if area < 0: poly = poly[::-1]
        lo, hi = prism(bm, poly, z, z + p['mer_h'])


def build_all(p=None):
    p = p or P(); A = p['A']; obs = []
    # ---------------- tower shaft
    bm = bmesh.new(); box(bm, -A, A, -A, A, 0, p['z_corb1']); obs.append(new_obj('shaft', bm))
    # ---------------- corbel: wall apex Q (face-mid, z_corb0) and corners (z_corb1) up to the octagon (z_balc)
    bm = bmesh.new()
    Rb = p['r_balc']; zb = p['z_balc']; z0 = p['z_corb0']; z1 = p['z_corb1']
    octv = [bm.verts.new((x, y, zb)) for x, y in ngon(Rb)]            # k*45 deg
    corners = [bm.verts.new((A * sx, A * sy, z1)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]   # at 45,135,225,315
    mids = [bm.verts.new((A * cos(k * pi / 2), A * sin(k * pi / 2), z0)) for k in range(4)]       # at 0,90,180,270
    for k in range(4):
        q = mids[k]; vm = octv[2 * k]; vl = octv[(2 * k + 1) % 8]; vr = octv[(2 * k - 1) % 8]
        cl = corners[k]; cr = corners[(k - 1) % 4]
        bm.faces.new((q, vl, vm)); bm.faces.new((q, vm, vr))
        bm.faces.new((q, cl, vl)); bm.faces.new((q, vr, cr))
        # wall triangle below the corbel (shaft face between z0..z1 is covered by the shaft box up to z1)
    obs.append(new_obj('corbel', bm))
    # ---------------- balcony slab + lantern room + cornice
    bm = bmesh.new(); prism(bm, ngon(Rb), zb, zb + p['balc_t']); obs.append(new_obj('balcony', bm))
    bm = bmesh.new(); zf = zb + p['balc_t']
    railing(bm, ngon(Rb - 0.08), zf, p['rail_h'], 0.42, r=0.016, corner_r=0.035); obs.append(new_obj('balcony_rail', bm))
    bm = bmesh.new(); rv = ngon(p['r_room']); zc = p['z_corn']
    ww, w0, w1, dep = p['win_w'], zf + p['win_z0'], zf + p['win_z1'], p['win_d']
    for k in range(8):
        a_ = Vector((*rv[k], 0)); b_ = Vector((*rv[(k + 1) % 8], 0)); d = (b_ - a_); L = d.length; d.normalize(); nin = Vector((-d.y, d.x, 0))
        if nin.dot(-a_) < 0: nin = -nin
        us = [0, (L - ww) / 2, (L + ww) / 2, L]; zs = [zf, w0 if k not in p['doors'] else zf + 0.05, w1, zc]
        def V(u, z, r=0.0):
            q = a_ + d * u + nin * r; return bm.verts.new((q.x, q.y, z))
        for i in range(3):
            for j in range(3):
                if i == 1 and j == 1:
                    o_ = [V(us[1], zs[1]), V(us[2], zs[1]), V(us[2], zs[2]), V(us[1], zs[2])]
                    n_ = [V(us[1], zs[1], dep), V(us[2], zs[1], dep), V(us[2], zs[2], dep), V(us[1], zs[2], dep)]
                    bm.faces.new(n_)
                    for m in range(4): bm.faces.new((o_[m], o_[(m + 1) % 4], n_[(m + 1) % 4], n_[m]))
                else:
                    bm.faces.new((V(us[i], zs[j]), V(us[i + 1], zs[j]), V(us[i + 1], zs[j + 1]), V(us[i], zs[j + 1])))
    obs.append(new_obj('room', bm))
    bm = bmesh.new()
    lathe(bm, [(p['r_room'] + 0.05, p['z_corn']), (p['r_corn'], p['z_corn'] + 0.18), (p['r_corn'], p['z_dome'])], 8)
    obs.append(new_obj('cornice', bm))
    # ---------------- dome (octagonal bell)
    bm = bmesh.new(); prof = [(r, z) for r, z in p['dome']]
    # subdivide the profile smoothly (Catmull-Rom)
    def cr(pts, m=4):
        out = []
        for i in range(len(pts) - 1):
            p0 = pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(i + 2, len(pts) - 1)]
            for s in range(m):
                t = s / m
                out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
        out.append(pts[-1]); return out
    rings = lathe(bm, cr(prof), 48)
    for ring in rings[1:-1]:                     # standing seams of the lead sheet: every third meridian raised (16 ribs, read on r1)
        for k_, v in enumerate(ring):
            if k_ % 3 == 0: v.co.x *= 1.03; v.co.y *= 1.03
    obs.append(new_obj('dome', bm, True))
    # ---------------- upper balcony, cone, pole, finial
    bm = bmesh.new(); zu = p['z_ubalc']
    lathe(bm, [(p['r_neck'], p['dome'][-1][1] - 0.05), (p['r_neck'], zu - 0.25), (p['r_ubalc'], zu - 0.05), (p['r_ubalc'], zu)], 8)
    # crenellated parapet ring (octagonal): a low solid wall and two merlons per side
    ro, ri, hw_, hm = p['r_ubalc'], p['r_ubalc'] - 0.28, p['upar_h'], p['upar_m']
    O = ngon(ro); I = ngon(ri)
    for k in range(8):
        j = (k + 1) % 8
        prism(bm, [O[k], O[j], I[j], I[k]][::-1] if False else [I[k], I[j], O[j], O[k]], zu, zu + hw_)
        for t0, t1 in ((0.12, 0.38), (0.62, 0.88)):
            def L(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            prism(bm, [L(I[k], I[j], t0), L(I[k], I[j], t1), L(O[k], O[j], t1), L(O[k], O[j], t0)], zu + hw_, zu + hw_ + hm)
    obs.append(new_obj('ubalcony', bm))
    bm = bmesh.new()
    lathe(bm, [(p['r_cone'], zu), (p['r_cone'] * 0.8, zu + 0.5), (p['r_pole'] * 1.6, p['z_pole'] - 0.3), (p['r_pole'], p['z_pole']), (p['r_pole'] * 0.8, p['z_gold'])], 16)
    obs.append(new_obj('pole', bm, True))
    bm = bmesh.new(); zg = p['z_gold']; s = p['fin_s']
    fin = [(0.16, 0), (0.30, 0.1), (0.30, 0.22), (0.14, 0.32), (0.12, 0.6), (0.22, 0.8), (0.30, 1.05), (0.26, 1.35), (0.15, 1.7), (0.10, 2.1), (0.14, 2.3), (0.08, 2.5), (0.04, 3.0), (0.02, 3.9), (0.0, 4.0)]
    lathe(bm, [(r * s, zg + z * s) for r, z in fin], 16, cap_top=False); obs.append(new_obj('finial', bm, True))
    # ---------------- flag
    bm = bmesh.new(); fa = radians(p['flag_az']); fw, fh = p['flag_w'], p['flag_h']; zt = p['flag_top']
    nx = 12
    vs = [[bm.verts.new(((0.2 + fw * i / nx) * cos(fa) - 0.12 * sin(i * 0.9) * sin(fa), (0.2 + fw * i / nx) * sin(fa) + 0.12 * sin(i * 0.9) * cos(fa), zt - fh * j)) for i in range(nx + 1)] for j in range(2)]
    uvl = bm.loops.layers.uv.new('UVMap')
    for i in range(nx):
        f = bm.faces.new((vs[1][i], vs[1][i + 1], vs[0][i + 1], vs[0][i]))
        for l, (u, v) in zip(f.loops, ((i / nx, 0), ((i + 1) / nx, 0), ((i + 1) / nx, 1), (i / nx, 1))): l[uvl].uv = (u, v)
    obs.append(new_obj('flag', bm, True))
    # ---------------- fortress
    F = p['fort']; x0, x1, y0, y1 = F['x0'], F['x1'], F['y0'], F['y1']; t = F['t']; zw = F['hw'] - p['mer_h']
    bm = bmesh.new()
    # -Y wall, -X wall, +X wall (from y0 to the tower), +Y wall (from x0 to the tower)
    box(bm, x0, x1, y0, y0 + t, 0, zw)
    box(bm, x0, x0 + t, y0 + t, y1, 0, zw)
    box(bm, x1 - t, x1, y0 + t, -A, 0, zw)
    box(bm, x0 + t, -A, y1 - t, y1, 0, zw)
    obs.append(new_obj('fort', bm))
    bm = bmesh.new()
    merlons(bm, (x0, y0), (x1, y0), (0, 1), zw, p)
    merlons(bm, (x0, y0 + p['mer_w'] + 0.5), (x0, y1), (1, 0), zw, p)
    merlons(bm, (x1, y0 + p['mer_w'] + 0.5), (x1, -A - 0.2), (-1, 0), zw, p)
    merlons(bm, (x0 + p['mer_w'] + 0.5, y1), (-A - 0.2, y1), (0, -1), zw, p)
    obs.append(new_obj('merlons', bm))
    bm = bmesh.new(); box(bm, x0 + t, x1 - t, y0 + t, y1 - t, 0, F['floor']); obs.append(new_obj('court', bm))
    # ---------------- annex
    a = p['annex']; ax0, ax1, ay0, ay1 = a['x0'], a['x1'], a['y0'], a['y1']; ze, zr = a['eave'], a['ridge']; yr = (ay0 + ay1) / 2; ov = a['over']
    bm = bmesh.new(); box(bm, ax0, ax1, ay0, ay1, 0, ze)
    # gable ends
    for xx, sgn in ((ax1, 1), (ax0, -1)):
        v = [bm.verts.new((xx, ay0, ze)), bm.verts.new((xx, ay1, ze)), bm.verts.new((xx, yr, zr - 0.08))]
        bm.faces.new(v if sgn > 0 else v[::-1])
    # porch (cross gable towards +Y)
    px0, px1, py1 = a['px0'], a['px1'], a['py1']
    obs.append(new_obj('annex', bm))
    bm = bmesh.new()
    def slab(pts, th=0.12):
        up = [bm.verts.new(q) for q in pts]; dn = [bm.verts.new((q[0], q[1], q[2] - th)) for q in pts]
        bm.faces.new(up); bm.faces.new(dn[::-1])
        for i in range(len(pts)):
            j = (i + 1) % len(pts); bm.faces.new((dn[i], dn[j], up[j], up[i]))
    sl = (zr - ze) / (ay1 - yr)
    slab([(ax0 - ov, ay1 + ov, ze - sl * ov), (ax1 + ov, ay1 + ov, ze - sl * ov), (ax1 + ov, yr, zr), (ax0 - ov, yr, zr)])
    slab([(ax1 + ov, ay0, ze), (ax0 - ov, ay0, ze), (ax0 - ov, yr, zr), (ax1 + ov, yr, zr)])
    # porch roof: ridge along y at x = pxm from the main roof to py1
    pxm = (px0 + px1) / 2; zpr = a['pridge']; zpe = a['peave']
    ymeet = ay1 - (zpr - ze) / sl * 1.0
    slab([(px0 - 0.2, py1 + 0.3, zpe), (pxm, py1 + 0.3, zpr), (pxm, max(ymeet, yr), zpr), (px0 - 0.2, ay1, zpe)])
    slab([(pxm, py1 + 0.3, zpr), (px1 + 0.2, py1 + 0.3, zpe), (px1 + 0.2, ay1, zpe), (pxm, max(ymeet, yr), zpr)])
    obs.append(new_obj('annex_roof', bm))
    bm = bmesh.new()
    for xx in (px0, px1):
        box(bm, xx - 0.1, xx + 0.1, py1 - 0.1, py1 + 0.1, 0, zpe - 0.1)
    v = [bm.verts.new((px0, py1, zpe - 0.12)), bm.verts.new((px1, py1, zpe - 0.12)), bm.verts.new((pxm, py1, zpr - 0.14))]; bm.faces.new(v)
    v = [bm.verts.new((px0, py1 - .02, zpe - 0.12)), bm.verts.new((px1, py1 - .02, zpe - 0.12)), bm.verts.new((pxm, py1 - .02, zpr - 0.14))]; bm.faces.new(v[::-1])
    obs.append(new_obj('porch', bm))
    # ---------------- terrace, parapet, quay, rocks
    T = p['terrace']; bm = bmesh.new(); prism(bm, T, -0.6, 0.0); obs.append(new_obj('terrace', bm))
    bm = bmesh.new(); n = len(T)
    cen = Vector((sum(x for x, y in T) / n, sum(y for x, y in T) / n))
    def strip(a_, b_, nrm, th, z0_, z1_):
        q = [a_, b_, b_ + nrm * th, a_ + nrm * th]; poly = [(v.x, v.y) for v in q]
        area = sum(poly[k][0] * poly[(k + 1) % 4][1] - poly[(k + 1) % 4][0] * poly[k][1] for k in range(4))
        if area < 0: poly = poly[::-1]
        prism(bm, poly, z0_, z1_)
    for i in range(n):
        if i in p['parapet_skip']: continue
        a_ = Vector(T[i]); b_ = Vector(T[(i + 1) % n]); d = (b_ - a_); L = d.length; d.normalize(); nrm = Vector((-d.y, d.x))
        if (cen - a_).dot(nrm) < 0: nrm = -nrm
        strip(a_, b_, nrm, p['kerb_t'], 0, p['kerb_h'])
        m = max(1, int(round((L - 2.0) / p['blk_pitch']))); pitch = (L - 2.0) / m; bl = p['blk_len']
        for k in range(m):
            c0 = a_ + d * (1.0 + k * pitch + (pitch - bl) / 2) + nrm * p['kerb_t']
            strip(c0, c0 + d * bl, nrm, p['blk_t'], 0, p['blk_h'])
    obs.append(new_obj('parapet', bm))
    bm = bmesh.new(); prism(bm, p['quay'], p['water'] + 0.15, -0.15); obs.append(new_obj('quay', bm))
    # rocks: a skirt from the rock outline (z=-0.4) down to the water outline
    bm = bmesh.new(); R0 = p['rocks_in']; R1 = p['rocks_out']; rows = 9; NS = 320
    def radial(poly, th, c):
        d = Vector((cos(th), sin(th))); best = None
        for i in range(len(poly)):
            a_ = Vector(poly[i]); b_ = Vector(poly[(i + 1) % len(poly)]); e = b_ - a_
            den = d.x * e.y - d.y * e.x
            if abs(den) < 1e-9: continue
            w = a_ - c; t = (w.x * e.y - w.y * e.x) / den; u = (w.x * d.y - w.y * d.x) / den
            if t > 0 and -1e-6 <= u <= 1 + 1e-6 and (best is None or t > best): best = t
        return c + d * best
    cen = Vector((sum(x for x, y in R0) / len(R0), sum(y for x, y in R0) / len(R0)))
    ths = [2 * pi * k / NS for k in range(NS)]; P0 = [radial(R0, t, cen) for t in ths]; P1 = [radial(R1, t, cen) for t in ths]
    P1 = [q + (q - cen).normalized() * p.get('rock_grow', 0.0) for q in P1]
    QX, QY = max(x for x, y in p['quay']), max(y for x, y in p['quay'])
    Q = [Vector(q) for q in p['quay']]
    def dq(v):
        best = 1e9
        for i in range(len(Q)):
            a_, b_ = Q[i], Q[(i + 1) % len(Q)]; e = b_ - a_; t = max(0.0, min(1.0, (v - a_).dot(e) / max(e.length_squared, 1e-9)))
            best = min(best, (a_ + e * t - v).length)
        return best
    for k in range(NS):   # wherever the top edge is the quay wall, it drops vertically into the water: no rock slope
        if dq(P0[k]) < 0.5: P1[k] = P0[k] + (P0[k] - cen).normalized() * 0.05
    for k in range(NS):     # the skirt never runs inward of its top edge
        if (P1[k] - cen).length < (P0[k] - cen).length + 0.05: P1[k] = P0[k] + (P0[k] - cen).normalized() * 0.05
    grid = []
    import random; random.seed(3)
    for j in range(rows + 2):
        tt = min(j / rows, 1.0); ring = []
        for k in range(NS):
            q = P0[k].lerp(P1[k], tt); z = -0.3 + (p['water'] + 0.3) * tt ** 0.8 + (random.uniform(-0.3, 0.35) if 0 < j < rows else 0)
            if j == rows + 1: q = P1[k] + (P1[k] - cen).normalized() * 1.0; z = p['water'] - 0.8
            jit = 0.2 if j < rows else 0.0
            ring.append(bm.verts.new((q.x + random.uniform(-jit, jit), q.y + random.uniform(-jit, jit), z)))
        grid.append(ring)
    rows += 1
    for j in range(rows):
        L = len(grid[j])
        for i in range(L):
            k = (i + 1) % L; bm.faces.new((grid[j][i], grid[j + 1][i], grid[j + 1][k], grid[j][k]))
    obs.append(new_obj('rocks', bm))
    # boulders: armour stones scattered on the skirt (size read on r5: 0.6-0.9 m), each a lumpy squashed icosphere with its own tile UVs
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); rnd = random.Random(11); nb = 0
    for k in range(0, NS, 1):
        if dq(P0[k]) < 0.5: continue
        span = (P1[k] - P0[k]).length
        for t_ in [x / 10 for x in range(1, 10)]:
            if rnd.random() > 0.55 * max(span, 0.0) / 6.0 + 0.15: continue
            tt = t_ + rnd.uniform(-0.05, 0.05); q = P0[k].lerp(P1[k], tt) + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3)))
            z = -0.3 + (p['water'] + 0.3) * max(tt, 0) ** 0.8
            r = rnd.uniform(0.35, 0.6); sx, sy, sz = r * rnd.uniform(0.9, 1.4), r * rnd.uniform(0.8, 1.2), r * rnd.uniform(0.55, 0.8)
            res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
            vs = res['verts']; rot = rnd.uniform(0, 2 * pi); ou, ov = rnd.random(), rnd.random()
            for v in vs:
                n_ = v.co.normalized(); j = 1.0 + rnd.uniform(-0.24, 0.2)
                x_, y_, z_ = n_.x * sx * j, n_.y * sy * j, n_.z * sz * j
                v.co = Vector((q.x + x_ * cos(rot) - y_ * sin(rot), q.y + x_ * sin(rot) + y_ * cos(rot), z + z_ * 0.9 + sz * 0.25))
            fs = {f for v in vs for f in v.link_faces}
            for f in fs:
                c = f.calc_center_median() - Vector((q.x, q.y, z))
                for l in f.loops:
                    d_ = l.vert.co - Vector((q.x, q.y, z)); u_ = (atan2(d_.y, d_.x) / (2 * pi)) * 0.35 + ou; v_ = d_.z * 0.25 + ov
                    l[uvl].uv = (u_, v_)
            nb += 1
    print('boulders', nb)
    obs.append(new_obj('boulders', bm))
    # ---------------- beacon
    b = p['beacon']; bm = bmesh.new(); bx, by = b['x'], b['y']; a45 = radians(b['rot'])
    lathe(bm, [(b['r0'], b['z0']), (b['r1'], b['z1'])], 4, a0=a45, cx=bx, cy=by)                      # tapered trunk
    zl = b['z1']; rl = b['r1'] * 0.72
    lathe(bm, [(b['r1'] * 1.04, zl), (b['r1'] * 1.04, zl + 0.12)], 4, a0=a45, cx=bx, cy=by)                          # platform slab
    obs.append(new_obj('beacon', bm))
    bm = bmesh.new(); zc = zl + 0.12; sq = [(bx + rl * cos(a45 + k * pi / 2), by + rl * sin(a45 + k * pi / 2)) for k in range(4)]
    railing(bm, sq, zc, b['lant'], 0.5, r=0.035, rails=(1.0, 0.5), corner_r=0.05)                                  # open cage
    lathe(bm, [(0.2, zc), (0.2, zc + 0.35), (0.28, zc + 0.35), (0.28, zc + 0.6), (0.12, zc + 0.75)], 8, cx=bx, cy=by)  # lamp
    lathe(bm, [(rl * 1.05, zc + b['lant']), (rl * 1.05, zc + b['lant'] + 0.06), (0.04, b['top'] - 0.2), (0.02, b['top'])], 4, a0=a45, cx=bx, cy=by)  # cap + spike
    obs.append(new_obj('beacon_cage', bm))
    # ---------------- sea
    bm = bmesh.new(); box(bm, -3000, 3000, -3000, 3000, p['water'] - 0.1, p['water']); obs.append(new_obj('sea', bm))
    return obs


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def set_camera(name, cams=None):
    """Blender camera for photo `name` (r1..r6) from cams.json."""
    cams = cams or json.load(open(os.path.join(HERE, 'cams.json'))); c = cams[name]
    cam = bpy.data.cameras.new(name); o = bpy.data.objects.new('cam_' + name, cam); bpy.context.scene.collection.objects.link(o)
    R = Matrix(c['R'])            # rows: right, down, forward (world)
    M = Matrix((R[0], -R[1], -R[2])).transposed().to_4x4()   # columns: cam x (right), y (up), z (back)
    M.translation = Vector(c['pos']); o.matrix_world = M
    W, H = c['W'], c['H']; cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36.0; cam.lens = c['f'] / W * 36.0
    cam.shift_x = -(c['cx'] - W / 2) / W; cam.shift_y = (c['cy'] - H / 2) / W
    cam.clip_start = 1; cam.clip_end = 3000
    sc = bpy.context.scene; sc.render.resolution_x = W; sc.render.resolution_y = H; sc.render.resolution_percentage = 100
    sc.camera = o
    return o
