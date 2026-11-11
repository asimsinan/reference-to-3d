# Galata Tower, parametric (solve units: z = 0 at the lower cornice's bottom, x/y the tower axis; params.json)
import bpy, bmesh, json, os
from math import cos, sin, pi, radians, atan2, sqrt
from mathutils import Matrix, Vector
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, 'params.json')))
N = 384


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def obj_from_bm(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); return o


def lathe(name, prof, n=N, closed_top=False):
    """prof: [(r,z)] bottom->top. Cylindrical UVs: u = angle (seam at the back, theta = pi), v = arc length."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    L = [0.0]
    for a, b in zip(prof[:-1], prof[1:]): L.append(L[-1] + sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))
    rows = []
    for (r, z) in prof:
        row = []
        for j in range(n):
            t = -pi + 2 * pi * j / n; row.append(bm.verts.new((r * cos(t), r * sin(t), z)))
        rows.append(row)
    for i in range(len(prof) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            f = bm.faces.new((rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]))
            us = (j / n, (j + 1) / n, (j + 1) / n, j / n); vs = (L[i], L[i], L[i + 1], L[i + 1])
            for lp, u, v in zip(f.loops, us, vs): lp[uv].uv = (u, v / max(L[-1], 1e-6))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    o = obj_from_bm(name, bm)
    for p in o.data.polygons: p.use_smooth = True
    return o


def solid_ring(name, r_out, r_in, z0, z1, n=N):
    bm = bmesh.new(); ring = []
    for (r, z) in ((r_in, z0), (r_out, z0), (r_out, z1), (r_in, z1)):
        ring.append([bm.verts.new((r * cos(-pi + 2 * pi * j / n), r * sin(-pi + 2 * pi * j / n), z)) for j in range(n)])
    for i in range(4):
        a, b = ring[i], ring[(i + 1) % 4]
        for j in range(n):
            j2 = (j + 1) % n; bm.faces.new((a[j], a[j2], b[j2], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm)


def arch_prisms(name, r0, r1, th_list, w, sill, crown, nseg=16):
    """closed prisms, arch-shaped in (tangential, z), spanning radially r0..r1, one per angle (degrees)."""
    bm = bmesh.new(); rad = w / 2; spring = crown - rad
    outline = [(-rad, sill), (rad, sill)] + [(rad * cos(pi * k / nseg), spring + rad * sin(pi * k / nseg)) for k in range(nseg + 1)]
    outline = outline[:2] + outline[2:]
    for th in th_list:
        t = radians(th); er = Vector((cos(t), sin(t), 0)); et = Vector((-sin(t), cos(t), 0))
        def P3(r, tt, z):
            v = er * r + et * tt; v.z = z; return bm.verts.new(v)
        A = [P3(r0, tt, z) for tt, z in outline]; B = [P3(r1, tt, z) for tt, z in outline]
        bm.faces.new(A); bm.faces.new(B[::-1])
        m = len(A)
        for k in range(m):
            k2 = (k + 1) % m; bm.faces.new((A[k], B[k], B[k2], A[k2]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm)


def strip_hidden(o, z0, z1):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update(); kill = []
    for f in bm.faces:
        c = f.calc_center_median(); rr = Vector((c.x, c.y, 0)); n = f.normal
        if rr.length > 1e-6 and n.dot(rr.normalized()) < -0.5: kill.append(f); continue
        if abs(n.z) > 0.9 and all(abs(v.co.z - z0) < 1e-3 or abs(v.co.z - z1) < 1e-3 for v in f.verts): kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(o.data); bm.free()


def boolean_diff(o, cutter):
    m = o.modifiers.new('cut', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = cutter; m.solver = 'EXACT'
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cutter)


def cone_r(z):
    u = P['z_apex'] - z; return P['cone_a'] * u + P['cone_b'] * u * u


def roof_profile():
    zj = P['flare_join_z']; rj = cone_r(zj); u = P['z_apex'] - zj
    slope = P['cone_a'] + 2 * P['cone_b'] * u          # -dr/dz on the cone at the join
    re, ze = P['r_e'], P['z_e']
    prof = [(P['up_r'] - 0.05, ze + 0.02), (re - 0.1, ze - 0.01), (re, ze), (re + 0.03, ze + 0.06), (re + 0.02, ze + 0.16)]
    p0 = (re - 0.02, ze + 0.18); p2 = (rj, zj); t = zj - p0[1]; p1 = (rj + slope * t, p0[1])
    for k in range(0, 21):
        s = k / 20; prof.append(((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * p1[0] + s * s * p2[0], (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * p1[1] + s * s * p2[1]))
    zs = [zj + (P['z_apex'] - 0.12 - zj) * k / 60 for k in range(1, 61)]
    prof += [(cone_r(z), z) for z in zs] + [(0.0, P['z_apex'])]
    return prof


def finial_profile():
    za = P['z_apex']; zb = P['z_ball']; h = P['z_tip'] - za
    pr = [(0.32, za - 0.25), (0.26, za), (0.15, za + 0.15), (0.14, za + 0.45), (0.2, za + 0.52)]
    rb = 0.5
    for k in range(1, 24):
        a = -pi / 2 + pi * k / 24; pr.append((rb * cos(a), zb + rb * sin(a)))
    top = zb + rb
    pr += [(0.1, top + 0.05), (0.18, top + 0.4), (0.3, top + 0.85), (0.28, top + 0.95), (0.12, top + 1.0), (0.24, top + 1.08), (0.31, top + 1.4),
           (0.32, top + 1.9), (0.27, top + 2.4), (0.18, top + 2.75), (0.1, top + 2.85), (0.17, top + 2.95), (0.17, top + 3.05), (0.08, top + 3.12),
           (0.14, top + 3.3), (0.14, top + 3.4), (0.07, top + 3.45), (0.06, za + h - 0.3), (0.03, za + h - 0.05), (0.0, za + h)]
    return pr


def railing():
    r = P['rail_r']; z0 = P['bal'][-1][1]; h = P['rail_h']; bm = bmesh.new(); n = 0
    def box(c, ex, ey, ez, t):
        ct, st = cos(t), sin(t)
        vs = []
        for dx in (-ex, ex):
            for dy in (-ey, ey):
                for dz in (0, ez):
                    vs.append(bm.verts.new((c[0] + dx * ct - dy * st, c[1] + dx * st + dy * ct, c[2] + dz)))
        idx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        for q in idx: bm.faces.new([vs[i] for i in q])
    nb = int(2 * pi * r / 0.09)
    for k in range(nb):
        t = 2 * pi * k / nb; box((r * cos(t), r * sin(t), z0), 0.01, 0.011, h - 0.05, t)
    for zz, th in ((z0 + 0.06, 0.04), (z0 + h - 0.06, 0.05), (z0 + 0.55, 0.025)):
        m = 720
        for k in range(m):
            t0 = 2 * pi * k / m; t1 = 2 * pi * (k + 1) / m; tm = (t0 + t1) / 2
            box((r * cos(tm), r * sin(tm), zz - th), th, r * (t1 - t0) / 2 + 0.002, 2 * th, tm)
    o = obj_from_bm('railing', bm)
    # stone posts between the upper storey's openings
    bm = bmesh.new(); s = P['post']
    def box2(c, ex, ey, ez, t):
        ct, st = cos(t), sin(t); vs = []
        for dx in (-ex, ex):
            for dy in (-ey, ey):
                for dz in (0, ez):
                    vs.append(bm.verts.new((c[0] + dx * ct - dy * st, c[1] + dx * st + dy * ct, c[2] + dz)))
        for q in [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]: bm.faces.new([vs[i] for i in q])
    for k in range(P['n_arch']):
        t = radians(P['th0'] + 360 / P['n_arch'] * (k + 0.5)); c = (r * cos(t), r * sin(t), z0)
        box2(c, s / 2 + 0.04, s / 2 + 0.04, 0.12, t); box2((c[0], c[1], z0 + 0.12), s / 2, s / 2, h - 0.27, t)
        box2((c[0], c[1], z0 + h - 0.15), s / 2 + 0.05, s / 2 + 0.05, 0.1, t)
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.15, matrix=Matrix.Translation((c[0], c[1], z0 + h + 0.1)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return o, obj_from_bm('posts', bm)


def dormers():
    D = P['dormer']; bm = bmesh.new()
    for k in range(4):
        t = radians(P['th0'] + 90 * k); er = Vector((cos(t), sin(t), 0)); et = Vector((-sin(t), cos(t), 0))
        z0, z1 = D['z0'], D['z1']; w = D['w'] / 2; zr = z1 + 0.45
        rf = cone_r(z0) + 0.05                      # front face, just ahead of the roof at the sill
        rb = cone_r(zr) - 0.6
        outline = [(-w, z0), (w, z0), (w, z1), (0, zr), (-w, z1)]
        def V(r, tt, z):
            v = er * r + et * tt; v.z = z; return bm.verts.new(v)
        A = [V(rf, tt, z) for tt, z in outline]; B = [V(rb, tt, z) for tt, z in outline]
        bm.faces.new(A); bm.faces.new(B[::-1])
        for i in range(5):
            i2 = (i + 1) % 5; bm.faces.new((A[i], B[i], B[i2], A[i2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm('dormers', bm)


def smart_uv(o, angle=1.15):
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=angle, island_margin=0.004); bpy.ops.object.mode_set(mode='OBJECT')


def build_all():
    obs = []
    zg = P['zg']; tp = P['taper']; r0 = P['r_s0']
    shaft = lathe('shaft', [(r0 - tp * z, z) for z in [zg - 0.6 + (0.6 - zg) * k / 40 for k in range(41)]][:-1] + [(r0, 0.0)])
    obs.append(shaft)
    obs.append(lathe('cornice', [tuple(p) for p in P['cor']]))
    th = [P['th0'] + 360 / P['n_arch'] * k for k in range(P['n_arch'])]
    a = P['arc_open']; z0, z1 = P['arc_z']
    arc = solid_ring('arcade', P['arc_r'], 6.6, z0, z1)
    boolean_diff(arc, arch_prisms('cut', P['arc_r'] - a['depth'], P['arc_r'] + 1.0, th, a['w'], a['sill'], a['crown']))
    aw = P['arc_win']; boolean_diff(arc, arch_prisms('cut', P['arc_r'] - a['depth'] - aw['depth'], P['arc_r'] - a['depth'] + 0.05, th, aw['w'], aw['sill'], aw['crown']))
    strip_hidden(arc, z0, z1); smart_uv(arc); obs.append(arc)
    obs.append(lathe('balcony', [tuple(p) for p in P['bal']]))
    u = P['up_open']; z0, z1 = P['up_z']
    up = solid_ring('upper', P['up_r'], 6.0, z0, z1)
    boolean_diff(up, arch_prisms('cut', P['up_r'] - u['depth'], P['up_r'] + 1.0, th, u['w'], u['sill'], u['crown']))
    strip_hidden(up, z0, z1); smart_uv(up); obs.append(up)
    obs.append(lathe('roof', roof_profile()))
    d = dormers(); smart_uv(d); obs.append(d)
    obs.append(lathe('finial', finial_profile(), n=96))
    rl, po = railing(); smart_uv(po); obs += [rl, po]
    return obs


def set_camera(name, cams=None):
    cams = cams or json.load(open(os.path.join(HERE, 'cams.json'))); c = cams[name]
    cam = bpy.data.cameras.new(name); o = bpy.data.objects.new('cam_' + name, cam); bpy.context.scene.collection.objects.link(o)
    R = Matrix(c['R'])
    M = Matrix((R[0], -R[1], -R[2])).transposed().to_4x4(); M.translation = Vector(c['pos']); o.matrix_world = M
    W, H = c['W'], c['H']; cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36.0; cam.lens = c['f'] / W * 36.0
    cam.shift_x = -(c['cx'] - W / 2) / W; cam.shift_y = (c['cy'] - H / 2) / W
    cam.clip_start = 1; cam.clip_end = 3000
    sc = bpy.context.scene; sc.render.resolution_x = W; sc.render.resolution_y = H; sc.render.resolution_percentage = 100
    sc.camera = o
    return o
