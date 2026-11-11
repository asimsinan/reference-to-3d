# Interior of tram 34, from photo 8 (saloon) and photo 7 (cab). Called by geom34.build_all.
# Saloon: 6 single leather seats a side, all facing +X; honey wood wainscot to the sill; maroon frames; white barrel
# ceiling with wood ribs and two longitudinal beams; two chrome grab rails with leather straps; three ceiling lamps;
# glazed wooden bulkheads with a centre door. Cab: cream console across the nose with the displays of photo 7.
import bpy, bmesh, math
from mathutils import Vector, Matrix
import geom as G

def build(T):
    hw, Xe, Xr, CX, ZFL, ZSILL, ZWT = T.hw, T.Xe, T.Xr, T.CX, T.ZFL, T.ZSILL, T.ZWT
    yi = hw - 0.035                                   # inner face of the side walls
    # ---- wainscot and inner sill, posts, cornice
    for sd, nm in ((1, 'L'), (-1, 'R')):
        y = sd * yi
        mb = G.MB(); p0, p1 = ((Xr, y), (Xe, y)) if sd > 0 else ((Xe, y), (Xr, y))
        G.wall_segment(mb, p0, p1, ZFL, ZSILL - 0.02, []); mb.build('woodlam_wall_' + nm)
        G.box('frame_insill_' + nm, Xr, Xe, *sorted((y, y - sd * 0.09)), ZSILL - 0.02, ZSILL + 0.03)
        G.box('woodrib_cornice_' + nm, Xr, Xe, *sorted((y, y - sd * 0.06)), ZWT, 2.72)
        G.box('frame_inrail_' + nm, Xr, Xe, *sorted((y, y - sd * 0.03)), ZWT - 0.04, ZWT)
        for i in range(T.NW + 1):
            x = Xe - T.wp - i * T.WW
            G.box('frame_inpost_%s%d' % (nm, i), x - 0.05, x + 0.05, *sorted((y, y - sd * 0.05)), ZSILL, ZWT)
            G.box('woodrib_bracket_%s%d' % (nm, i), x - 0.045, x + 0.045, *sorted((y - sd * 0.05, y - sd * 0.13)), ZWT - 0.02, 2.70)
        for i in range(T.NW):
            xc = Xe - T.wp - (i + 0.5) * T.WW
            pts = [(xc + 0.13 * math.cos(a), y - sd * (0.02 + 0.06 * math.sin(a)), ZWT + 0.02) for a in [math.pi * k / 10 for k in range(11)]]
            G.tube('brass_handle_%s%d' % (nm, i), pts, 0.012, n=8)
        # narrow panel's inside: plain wainscot board up to the cornice
        G.box('woodlam_panelin_' + nm, Xe - T.wp, Xe, *sorted((y, y - sd * 0.01)), ZSILL, ZWT)
    # ---- ceiling: barrel from the cornice (2.72, y = +-0.80) to 2.95 at the centre
    def cz(y): return 2.72 + 0.23 * math.cos(min(1.0, abs(y) / 0.80) * math.pi / 2)
    ny = 24; ys = [-0.80 + 1.60 * j / ny for j in range(ny + 1)]
    mb = G.MB()
    for j in range(ny):
        a, b = ys[j], ys[j + 1]
        mb.quad((Xe, a, cz(a)), (Xr, a, cz(a)), (Xr, b, cz(b)), (Xe, b, cz(b)))
    mb.build('ceiling_white')
    nrib = 7
    for k in range(nrib):
        x = Xr + (Xe - Xr) * (k + 0.5) / nrib
        G.tube('woodrib_arch_%d' % k, [(x, y, cz(y) - 0.02) for y in ys], 0.022, n=6)
    for s in (1, -1):
        G.tube('woodrib_beam_%d' % (s > 0), [(Xr, s * 0.42, cz(0.42) - 0.025), (Xe, s * 0.42, cz(0.42) - 0.025)], 0.028, n=6)
        # chrome grab rail with hangers and leather straps
        zr = 2.48
        G.tube('chrome_rail_%d' % (s > 0), [(Xr + 0.25, s * 0.33, zr), (Xe - 0.25, s * 0.33, zr)], 0.016, n=10)
        for x in (Xr + 0.35, (Xr + Xe) / 2, Xe - 0.35):
            G.tube('chrome_hanger_%d_%.1f' % (s > 0, x), [(x, s * 0.33, zr), (x, s * 0.36, cz(0.36))], 0.01, n=6)
        nstrap = int((Xe - Xr - 0.6) / 0.24)
        for i in range(nstrap):
            x = Xr + 0.3 + i * 0.24
            pts = [(x + 0.03 * math.sin(a), s * 0.33, zr - 0.28 * (1 - math.cos(a)) / 2) for a in [2 * math.pi * k / 16 for k in range(17)]]
            G.tube('leather_strap_%d_%d' % (s > 0, i), pts, 0.009, n=6)
    for x in (Xr + 0.7, (Xr + Xe) / 2, Xe - 0.7):
        G.cyl('black_lampbody_%.1f' % x, (x, 0, cz(0) - 0.05), (0, 0, 1), 0.13, 0.10, n=32)
        G.cyl('lamp_diffuser_%.1f' % x, (x, 0, cz(0) - 0.105), (0, 0, 1), 0.10, 0.012, n=32)
    # ---- seats: 6 a side, facing +X
    n = 6; pitch = 0.60
    for sd, nm in ((1, 'L'), (-1, 'R')):
        yc = sd * 0.68
        for i in range(n):
            x0 = -2.05 + i * pitch                # front edge of the cushion (toward -X, the way the seat faces); backs at -1.60 + 0.6 i
            seat(nm + str(i), x0, yc, ZFL)
    # ---- bulkheads at both saloon ends: wood frame, three glazed openings, door with a wood lower panel
    for x, nm, sgn in ((Xe, 'F', 1), (Xr, 'B', -1)):
        bulkhead(nm, x, sgn, hw, ZFL, ZWT)
    # ---- cabs
    cab(T, False); cab(T, True)

def rbox(name, x0, x1, y0, y1, z0, z1, bev=0.02, seg=3, lean=0.0):
    """bevelled box; lean moves the top face by +lean in x"""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        t = v.co.z + 0.5
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0) + lean * t, (y0 + y1) / 2 + v.co.y * (y1 - y0), z0 + t * (z1 - z0)))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bev, segments=seg, affect='EDGES')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); G.OBJS.append(o); return o

def seat(nm, x0, yc, zf):
    """photo 8 (measured through its camera): single seats facing the rear (-X), 0.32 m wide, cushion top 0.46 m and back
    top 0.75 m above the floor, 0.60 m pitch; padded back with rounded edges, thick cushion; brass tube along the back's
    top that turns down the aisle-side edge (the grip); reddish wood side plate and a pedestal on the aisle side"""
    w = 0.32; s = math.copysign(1, yc); ya = yc - s * w / 2; yw = yc + s * w / 2
    rbox('leather_cushion_' + nm, x0, x0 + 0.40, yc - w / 2, yc + w / 2, zf + 0.30, zf + 0.39, bev=0.035, seg=4)
    rbox('leather_back_' + nm, x0 + 0.37, x0 + 0.45, yc - w / 2, yc + w / 2, zf + 0.37, zf + 0.75, bev=0.035, seg=4, lean=0.05)
    zt = zf + 0.755; xb = x0 + 0.45
    G.tube('brass_seattop_' + nm, [(xb + 0.01, yw - s * 0.03, zt), (xb + 0.01, ya + s * 0.04, zt), (xb + 0.005, ya + s * 0.005, zt - 0.03), (xb - 0.01, ya + s * 0.005, zt - 0.22)], 0.007, n=8)
    G.box('woodend_seatside_' + nm, x0 + 0.04, x0 + 0.44, *sorted((ya, ya + s * 0.022)), zf + 0.18, zf + 0.36)
    G.box('woodend_seatarm_' + nm, x0 + 0.36, x0 + 0.44, *sorted((ya, ya + s * 0.022)), zf + 0.36, zf + 0.52)
    G.cyl('woodend_seatpost_' + nm, (x0 + 0.22, ya + s * 0.07, zf + 0.10), (0, 0, 1), 0.035, 0.20, n=16)
    G.cyl('chrome_seatfoot_' + nm, (x0 + 0.22, ya + s * 0.07, zf + 0.008), (0, 0, 1), 0.075, 0.016, n=24)
    G.box('woodend_seatbracket_' + nm, x0 + 0.12, x0 + 0.38, *sorted((yw - s * 0.04, yw + s * 0.02)), zf + 0.18, zf + 0.30)

def bulkhead(nm, x, sgn, hw, zf, zt):
    """photo 8: a 0.9 m door frame in the middle (one leaf closed: wood below, glass above; the other leaf folded open),
    glazed panels each side over a wood dado, a transom band above"""
    yb = hw - 0.04; t = 0.04; dw = 0.39; zdoor = 2.48; zdado = zf + 0.75
    xa, xb = sorted((x, x - sgn * t))
    G.box('woodend_top_' + nm, xa, xb, -yb, yb, zdoor, 2.80)
    for y0, y1 in ((-yb, -dw), (dw, yb)):
        G.box('woodend_low_%s_%.2f' % (nm, y0), xa, xb, y0, y1, zf, zdado)
    for y0, y1 in ((-yb, -yb + 0.06), (-0.66, -0.62), (0.62, 0.66), (yb - 0.06, yb), (-dw - 0.05, -dw), (dw, dw + 0.05)):
        G.box('woodend_post_%s_%.2f' % (nm, y0), xa, xb, y0, y1, zf if abs(abs(y0) - dw) < 0.06 or abs(abs(y1) - dw) < 0.06 else zdado, zdoor)
    xm = (xa + xb) / 2
    for y0, y1 in ((-yb + 0.06, -0.66), (-0.62, -dw - 0.05), (dw + 0.05, 0.62), (0.66, yb - 0.06)):
        mb = G.MB(); mb.quad((xm, y0, zdado), (xm, y1, zdado), (xm, y1, zdoor), (xm, y0, zdoor)); mb.build('glass_end_%s_%.2f' % (nm, y0))
    # closed leaf on +Y (the left half seen from the saloon of the F end); open leaf folded against the -Y post
    ly0, ly1 = (0.0, dw) if sgn > 0 else (-dw, 0.0)
    if sgn < 0: ly0 = ly1 = None                                      # the rear door stands open (photo 8 is taken from it)
    if ly0 is None:
        G.box('gold_ornament_' + nm, xa - sgn * 0.005, xb + sgn * 0.005, 0.05, 0.25, zdoor + 0.05, zdoor + 0.16); return
    G.box('woodend_door_' + nm, xa + 0.005, xb - 0.005, ly0, ly1, zf, zf + 1.05)
    for (y0, y1, z0, z1) in ((ly0, ly1, zdoor - 0.06, zdoor), (ly0, ly0 + 0.05, zf + 1.05, zdoor), (ly1 - 0.05, ly1, zf + 1.05, zdoor)):
        G.box('woodend_doorframe_%s_%.2f_%.2f' % (nm, y0, z0), xa + 0.005, xb - 0.005, y0, y1, z0, z1)
    mb = G.MB(); mb.quad((xm, ly0 + 0.05, zf + 1.05), (xm, ly1 - 0.05, zf + 1.05), (xm, ly1 - 0.05, zdoor - 0.06), (xm, ly0 + 0.05, zdoor - 0.06)); mb.build('glass_enddoor_' + nm)
    oy = -dw if sgn > 0 else dw                                       # open leaf, folded flat against the frame
    G.box('woodend_openleaf_' + nm, *sorted((x - sgn * 0.06, x - sgn * 0.10)), *sorted((oy, oy - math.copysign(0.03, oy) * -1)), zf, zdoor - 0.02)
    G.box('gold_ornament_' + nm, xa - sgn * 0.005, xb + sgn * 0.005, 0.05, 0.25, zdoor + 0.05, zdoor + 0.16)

def cab(T, rear):
    tag = 'B' if rear else 'F'; X = lambda o: T.xform(o, rear)
    Xf, xo, ac, hw = T.Xf, T.xo, T.ac, T.hw
    zt = 1.42; zb = 1.30                                # console top: back edge (driver) 1.30, front 1.42
    xb, xfr = Xf - 0.62, Xf - 0.06
    # console body: follows the nose, front edge 6 cm inside the dash
    def yhalf(x):                                       # half width of the nose at x (inside)
        if x >= xo: return ac + (hw - ac) * (Xf - x) / (Xf - xo) - 0.05
        return hw - 0.05
    nx = 10; xs = [xb + (xfr - xb) * i / nx for i in range(nx + 1)]
    mb = G.MB()
    for i in range(nx):
        a, b = xs[i], xs[i + 1]; za = zb + (zt - zb) * (a - xb) / (xfr - xb); zb2 = zb + (zt - zb) * (b - xb) / (xfr - xb)
        mb.quad((a, -yhalf(a), za), (b, -yhalf(b), zb2), (b, yhalf(b), zb2), (a, yhalf(a), za))
    mb.build('console_top_' + tag); X(G.OBJS[-1])
    mb = G.MB(); mb.quad((xb, yhalf(xb), T.ZFL), (xb, -yhalf(xb), T.ZFL), (xb, -yhalf(xb), zb), (xb, yhalf(xb), zb)); o = mb.build('console_front_' + tag); X(o)
    for s in (1, -1):
        mb = G.MB(); pts = [(x, s * yhalf(x)) for x in xs]
        for i in range(nx):
            (a, ya), (b, yb2) = pts[i], pts[i + 1]
            za = zb + (zt - zb) * (a - xb) / (xfr - xb); zz = zb + (zt - zb) * (b - xb) / (xfr - xb)
            q = [(a, ya, T.ZFL), (b, yb2, T.ZFL), (b, yb2, zz), (a, ya, za)]
            mb.quad(*(q if s < 0 else q[::-1]))
        o = mb.build('console_side_%s%d' % (tag, s > 0)); X(o)
    # displays (photo 7): main speedo display, camera monitor, right monitor on a stand, two tablets on arms
    def screen(name, xc, yc, zc, w, h, tilt, yaw=0.0, d=0.03):
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts: v.co = Vector((v.co.x * d, v.co.y * w, v.co.z * h))
        bm.transform(Matrix.Translation((xc, yc, zc)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'Y'))
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); G.OBJS.append(o); X(o)
        # the screen face (towards -X, the driver) as its own quad with UVs 0..1
        R = Matrix.Translation((xc, yc, zc)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'Y')
        c = [R @ Vector((-d / 2 - 0.002, yy, zz)) for yy, zz in ((w / 2, -h / 2), (-w / 2, -h / 2), (-w / 2, h / 2), (w / 2, h / 2))]
        me = bpy.data.meshes.new('screen_' + name); me.from_pydata([tuple(p) for p in c], [], [(0, 1, 2, 3)])
        uv = me.uv_layers.new(name='UVMap')
        for i, (u, v) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))): uv.data[i].uv = (u, v)
        so = bpy.data.objects.new('screen_' + name, me); bpy.context.scene.collection.objects.link(so); G.OBJS.append(so); X(so)
    zmid = (zt + zb) / 2
    screen('disp_main_' + tag, xb + 0.30, 0.05, zmid + 0.12, 0.30, 0.22, math.radians(-15))
    screen('disp_cam_' + tag, xb + 0.28, -0.30, zmid + 0.07, 0.20, 0.12, math.radians(-25))
    screen('disp_right_' + tag, xb + 0.33, -0.62, zmid + 0.13, 0.26, 0.15, math.radians(-20), math.radians(-25))
    for s, nm in ((1, 'tabL'), (-1, 'tabR')):
        screen('disp_%s_%s' % (nm, tag), xo - 0.12, s * (hw - 0.16), 1.75, 0.20, 0.34, math.radians(-8), math.radians(s * 20))
        o = G.tube('black_tabarm_%s_%s' % (nm, tag), [(xo - 0.10, s * (hw - 0.05), 1.55), (xo - 0.10, s * (hw - 0.14), 1.60)], 0.012); X(o)
    o = G.tube('black_controller_' + tag, [(xb + 0.18, -0.42, zb + 0.02), (xb + 0.12, -0.42, zb + 0.14)], 0.014); X(o)
    o = G.cyl('red_knob_' + tag, (xb + 0.12, -0.42, zb + 0.16), (0, 0, 1), 0.022, 0.03, n=16); X(o)
    # driver's seat (black, seen through the bulkhead in photo 8)
    o = G.box('blackseat_cushion_' + tag, xb - 0.62, xb - 0.20, -0.20, 0.20, T.ZFL + 0.50, T.ZFL + 0.58); X(o)
    o = G.box('blackseat_back_' + tag, xb - 0.66, xb - 0.58, -0.20, 0.20, T.ZFL + 0.58, T.ZFL + 1.10); X(o)
    o = G.cyl('blackseat_post_' + tag, (xb - 0.40, 0, T.ZFL + 0.25), (0, 0, 1), 0.04, 0.50, n=12); X(o)
