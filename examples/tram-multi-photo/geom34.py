# Blender: tram No. 34 (new livery, battery operated: no bow collector) as named meshes.
# Frame: +X the photographed end ("front"), +Y left, z = 0 rail top, metres. Dimensions from cams34.json (photos 9, 13),
# the rectified side (photo 9) and the roof photo (15). The rear end is the front end turned 180 deg about x = CX.
# Every object's name starts with its material class (see final34.py): paint_, white_, frame_, glass_, black_, ...
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib, sys
sys.path.insert(0, HERE)
import geom as G           # mesh helpers only (MB, mk, wall_segment, panes, box, cyl, tube, clear)
M = json.load(open(os.path.join(HERE, 'cams34.json')))['model']

hw = 0.885
Xf, ac, xo, yo = M['Xf'], M['ac'], M['xo'], M['yo']
Xe = M['Xe']; wp = 0.25; Xr = -2.133             # saloon ends; narrow panel 0.25 m at both ends (photo 3)
NW = 3; WW = (Xe - Xr - 2 * wp) / NW                # three equal windows
CX = (Xe + Xr) / 2                                  # centre of the 180-deg turn (saloon centre)
ZS, ZSILL, ZTR, ZWT, ZBAND, ZCOVE, ZROOF = 0.72, 1.70, 2.20, 2.61, 2.75, 2.93, 3.00
ZWTE = 2.61                                         # white hood starts at 2.62 on the front (photo 13, measured)
ZHEADE = 0.035                                      # thin maroon head over the cab windows (photo 13)
ZHEAD = 0.10                                        # maroon frame head under the white hood (photo 13: z 2.51-2.61)
ZWD = M['zwd']; ZFL = 0.80
ZPT = 2.63                                          # narrow panel's rounded top
RAILS = [(1.33, 0.045), (0.94, 0.045), (0.77, 0.035)]   # lower-body mouldings (z centre, height)
OBJS = G.OBJS

def R(p):   # front -> rear
    return (2 * CX - p[0], -p[1], p[2])

def xform(o, rear):
    if rear: o.data.transform(Matrix.Translation((2 * CX, 0, 0)) @ Matrix.Rotation(math.pi, 4, 'Z'))
    return o

def front_plan():
    return [(xo, -hw), (Xf, -ac), (Xf, ac), (xo, hw)]

RS, RF = 0.20, 0.06                                 # walls: three panels with soft joints (photos 9, 13); hood and fender are oval
def _fillet(a, c, b, r, n):
    import numpy as np
    a, c, b = np.array(a), np.array(c), np.array(b)
    d1 = (c - a) / np.linalg.norm(c - a); d2 = (b - c) / np.linalg.norm(b - c)
    th = math.acos(max(-1.0, min(1.0, float(d1 @ d2)))); t = r * math.tan(th / 2)
    p1 = c - d1 * t; p2 = c + d2 * t
    nrm = np.array([-d1[1], d1[0]]); nrm = nrm if (d2 @ nrm) > 0 else -nrm; ctr = p1 + nrm * r
    a1 = math.atan2(*(p1 - ctr)[::-1]); a2 = math.atan2(*(p2 - ctr)[::-1])
    if a2 - a1 > math.pi: a2 -= 2 * math.pi
    if a1 - a2 > math.pi: a2 += 2 * math.pi
    return [tuple(ctr + r * np.array([math.cos(a1 + (a2 - a1) * k / n), math.sin(a1 + (a2 - a1) * k / n)])) for k in range(n + 1)], t

def nose(rs=None, rf=None, n=14):
    """front end plan from the side (y = -hw) round to the other side: list of segments (p0, p1, kind, facet)"""
    rs = RS if rs is None else rs; rf = RF if rf is None else rf
    C = [(xo - 1.0, -hw), (xo, -hw), (Xf, -ac), (Xf, ac), (xo, hw), (xo - 1.0, hw)]
    arcs = []; ts = []
    for i in range(1, 5):
        pts, t = _fillet(C[i - 1], C[i], C[i + 1], rs if i in (1, 4) else rf, n); arcs.append(pts); ts.append(t)
    segs = []
    for j, arc in enumerate(arcs):
        for k in range(len(arc) - 1): segs.append((arc[k], arc[k + 1], 'arc', None))
        if j < 3: segs.append((arc[-1], arcs[j + 1][0], 'facet', j))
    return segs, ts[0]

SEGS, TS = nose()
XN = xo - TS                                        # where the nose's curve leaves the straight side
def loop(rs, rf, n=14):
    """closed plan of the whole car (both ends) with the given corner radii, starting at the front end's -Y side"""
    segs, ts = nose(rs, rf, n); xn = xo - ts
    f = [(xn, -hw)] + [s[1] for s in segs][:-1] + [(xn, hw)]
    return f + [(2 * CX - x, -y) for x, y in f]
def facets(): return [(p0, p1) for p0, p1, k, f in SEGS if k == 'facet']
def nose_pts(): return [SEGS[0][0]] + [s[1] for s in SEGS]

_FP = nose_pts()
import numpy as _np
CP = _np.array(_FP); CS = _np.r_[0, _np.cumsum(_np.linalg.norm(_np.diff(CP, axis=0), axis=1))]; SL = float(CS[-1])
def _arcmid(j):            # arc length at the middle of fillet arc j (0..3)
    k = [i for i, sg in enumerate(SEGS) if sg[2] == 'arc']
    per = len(k) // 4; i0 = k[j * per] ; i1 = k[(j + 1) * per - 1]
    return float((CS[i0] + CS[i1 + 1]) / 2)
SPOST = [_arcmid(1), _arcmid(2)]          # the two front corner posts (old facet corners)
def at(s):
    s = min(max(s, 0.0), SL); i = int(_np.searchsorted(CS, s, side='right') - 1); i = min(i, len(CP) - 2)
    t = (s - CS[i]) / max(CS[i + 1] - CS[i], 1e-9); p = CP[i] + (CP[i + 1] - CP[i]) * t
    d = (CP[i + 1] - CP[i]) / max(CS[i + 1] - CS[i], 1e-9); return p, d
def strip(mb, s0, s1, z0, z1, off=0.0, uv=False):
    """quads following the nose curve between arc lengths s0..s1 (outward offset off)"""
    ss = [s0] + [float(c) for c in CS if s0 < c < s1] + [s1]
    for a, b in zip(ss, ss[1:]):
        (pa, da), (pb, db) = at(a), at(b if b < SL else b - 1e-6)
        if b >= SL: pb, _ = at(SL)
        na = (da[1], -da[0]); nb = (db[1], -db[0])
        A = (pa[0] + na[0] * off, pa[1] + na[1] * off); Bq = (pb[0] + nb[0] * off, pb[1] + nb[1] * off)
        mb.quad((A[0], A[1], z0), (Bq[0], Bq[1], z0), (Bq[0], Bq[1], z1), (A[0], A[1], z1))
        if uv: mb.uvq = getattr(mb, 'uvq', []) + [((a - s0) / (s1 - s0), (b - s0) / (s1 - s0))]
POLY = [(XN, -hw)] + _FP[1:-1] + [(XN, hw)]
POLY = POLY + [(2 * CX - x, -y) for x, y in POLY]

def win_x():
    """saloon window openings (x0 > x1), posts 9 cm"""
    out = []
    for i in range(NW):
        a = Xe - wp - i * WW; b = a - WW
        out.append((a - 0.045 if i > 0 else a - 0.06, b + 0.045 if i < NW - 1 else b + 0.06))
    return out

# ------------------------------------------------------------------ saloon walls
def saloon():
    for sd, nm in ((1, 'L'), (-1, 'R')):
        y = sd * hw
        p0, p1 = ((Xe, y), (Xr, y)) if sd > 0 else ((Xr, y), (Xe, y))
        L = Xe - Xr
        def s(x): return (Xe - x) if sd > 0 else (x - Xr)
        holes = []
        for a, b in win_x():
            s0, s1 = sorted((s(a), s(b))); holes.append((s0, s1, ZSILL + 0.06, ZWT - ZHEAD))
        mb = G.MB(); G.wall_segment(mb, p0, p1, ZS, ZSILL, []); mb.build('paint_side_lower_' + nm, solid=0.03)
        mb = G.MB(); G.wall_segment(mb, p0, p1, ZSILL, ZWT, holes); mb.build('paint_side_upper_' + nm, solid=0.03)
        mg = G.MB(); G.panes(mg, p0, p1, holes, 0.045); mg.build('glass_side_' + nm)
        # window frames (maroon): sill, head, transom, jambs; 3 cm proud of the glass
        for a, b in win_x():
            x0, x1 = b, a
            for (za, zb_) in ((ZSILL, ZSILL + 0.07), (ZWT - ZHEAD, ZWT), (ZTR - 0.025, ZTR + 0.025)):
                G.box('frame_win_%s_%.2f_%.2f' % (nm, x0, za), x0, x1, *sorted((y, y - sd * 0.05)), za, zb_)
            for xx in (x0, x1 - 0.05):
                G.box('frame_jamb_%s_%.2f' % (nm, xx), xx, xx + 0.05, *sorted((y, y - sd * 0.05)), ZSILL, ZWT)
        # posts between windows (maroon, proud), and the frame strip under the sill
        G.box('frame_sillstrip_' + nm, Xr + wp, Xe - wp, *sorted((y, y + sd * 0.025)), ZSILL - 0.03, ZSILL + 0.02)
        for i in range(1, NW):
            x = Xe - wp - i * WW
            G.box('frame_post_%s%d' % (nm, i), x - 0.045, x + 0.045, *sorted((y, y + sd * 0.02)), ZSILL, ZWT)
        # narrow panel: white border with a rounded top, inset maroon line
        tube_panel(nm, sd); tube_panel(nm + 'r', sd, Xr + wp)
        # lower body (photo 18): two rows of white-lined rectangles on flat red, one per column (end panel, three windows, end panel)
        cols = [(Xe - wp, Xe)] + [(Xe - wp - (i + 1) * WW, Xe - wp - i * WW) for i in range(NW)] + [(Xr, Xr + wp)]
        t = 0.018; yy = sorted((y + sd * 0.002, y + sd * 0.006))
        for (xa, xb) in cols:
            for (za, zb_) in ((1.25, 1.645), (0.83, 1.195)):
                a, b = xa + 0.035, xb - 0.035
                G.box('white_line_%s_%.2f_%.2f_b' % (nm, xa, za), a, b, *yy, za, za + t)
                G.box('white_line_%s_%.2f_%.2f_t' % (nm, xa, za), a, b, *yy, zb_ - t, zb_)
                G.box('white_line_%s_%.2f_%.2f_l' % (nm, xa, za), a, a + t, *yy, za, zb_)
                G.box('white_line_%s_%.2f_%.2f_r' % (nm, xa, za), b - t, b, *yy, za, zb_)

def tube_panel(nm, sd, x0=None):
    """photo 18: the narrow column at each saloon end is white above the sill, with a red panel with a rounded top"""
    x0 = Xe if x0 is None else x0
    y = sd * hw; xa, xb = x0 - wp, x0
    G.box('white_endcol_' + nm, xa, xb, *sorted((y, y + sd * 0.004)), ZSILL, ZWT)
    pa, pb = xa + 0.045, xb - 0.045; r = (pb - pa) / 2; zc = ZPT - r; z0 = ZSILL + 0.07
    prof = [(pa, z0), (pb, z0)] + [((pa + pb) / 2 + r * math.cos(t), zc + r * math.sin(t)) for t in [math.pi * i / 16 for i in range(17)]]
    mb = G.MB(); yy = y + sd * 0.008
    fr = mb.add([(x, yy, z) for x, z in prof]); bk = mb.add([(x, y + sd * 0.004, z) for x, z in prof])
    mb.face(fr if sd > 0 else fr[::-1]); n = len(prof)
    for i in range(n): mb.face([fr[i], fr[(i + 1) % n], bk[(i + 1) % n], bk[i]] if sd < 0 else [fr[(i + 1) % n], fr[i], bk[i], bk[(i + 1) % n]])
    mb.build('paint_endpanel_' + nm)

# ------------------------------------------------------------------ ends (front built, rear = turned copy)
def end(rear):
    """the nose as one oval curve: dash, cab window band, white hood; windows between posts at the old facet corners"""
    tag = 'B' if rear else 'F'
    s_side = CS[[i for i, sg in enumerate(SEGS) if sg[2] == 'arc'][0]]
    PW = 0.035
    P0, P1 = SPOST; ends = (0.0, SL)
    posts = [(0.0, 0.06), (P0 - PW, P0 + PW), (P1 - PW, P1 + PW), (SL - 0.06, SL)]
    wins = [(0.06, P0 - PW), (P0 + PW, P1 - PW), (P1 + PW, SL - 0.06)]
    mbl = G.MB(); mbw = G.MB(); mbc = G.MB(); mbu = G.MB(); mg = G.MB(); fr = G.MB(); lin = G.MB()
    strip(mbl, 0, SL, 0.82, ZWD)
    for a_, b_ in posts: strip(mbc, a_, b_, ZWD, ZWTE)
    for a_, b_ in wins:
        strip(mbu, a_, b_, ZWD, ZWD + 0.07); strip(mbu, a_, b_, ZWTE - ZHEADE, ZWTE)
        strip(mg, a_, b_, ZWD + 0.07, ZWTE - ZHEADE, off=-0.035)
        strip(fr, a_, b_, ZWD, ZWD + 0.07, off=0.012); strip(fr, a_, b_, ZWTE - ZHEADE, ZWTE, off=0.012)
    for a_, b_ in (wins[0], wins[2]): strip(fr, a_, b_, 2.06, 2.10, off=0.012)
    for a_, b_ in posts: strip(fr, a_, b_, ZWD, ZWTE, off=0.012)
    panels = [(0.0, P0), (P0, P1), (P1, SL)]
    for a_, b_ in panels:
        strip(lin, a_ + 0.04, b_ - 0.04, ZWD - 0.06, ZWD - 0.045, off=0.006); strip(lin, a_ + 0.04, b_ - 0.04, 1.03, 1.045, off=0.006)
        strip(lin, a_ + 0.04, a_ + 0.055, 1.03, ZWD - 0.045, off=0.006); strip(lin, b_ - 0.055, b_ - 0.04, 1.03, ZWD - 0.045, off=0.006)
    for mb, n, sol in ((mbl, 'paint_dash_', 0.03), (mbu, 'paint_cab_', 0.03), (mbc, 'frame_corner_', 0.03), 
                       (mg, 'glass_cab_', 0), (fr, 'frame_cab_', 0), (lin, 'white_dashline_', 0)):
        o = mb.build(n + tag, solid=sol)
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(o.data); bm.free()
        for p in o.data.polygons: p.use_smooth = True
        xform(o, rear)

    # platform: white band over the door opening on both sides, roof edge
    for sd, nm in ((1, 'L'), (-1, 'R')):
        y = sd * hw
        o = G.box('frame_doorpost_%s%s' % (tag, nm), Xe - 0.01, Xe + 0.15, *sorted((y, y - sd * 0.05)), ZS, ZWT); xform(o, rear)
        o = G.box('frame_doorpost2_%s%s' % (tag, nm), XN - 0.06, XN, *sorted((y, y - sd * 0.05)), 0.82, ZWT); xform(o, rear)
        doors(tag, nm, sd, rear)
        scissor_gate(tag, nm, sd, rear)
        # step
        for (y0, y1, z0, z1, k) in ((hw - 0.16, hw + 0.06, 0.27, 0.31, 0), (hw - 0.34, hw - 0.12, 0.53, 0.57, 1)):
            o = G.box('black_step_%s%s%d' % (tag, nm, k), Xe + 0.15, XN - 0.06, *sorted((sd * y0, sd * y1)), z0, z1); xform(o, rear)
            for r_ in range(5):                                             # ribbed rubber treads
                yy = y0 + (r_ + 0.5) * (y1 - y0) / 5
                o = G.box('black_steprib_%s%s%d%d' % (tag, nm, k, r_), Xe + 0.17, XN - 0.08, *sorted((sd * (yy - 0.012), sd * (yy + 0.012))), z1, z1 + 0.008); xform(o, rear)
        for (y0, y1, z0, z1, k) in ((hw - 0.16, hw - 0.14, 0.31, 0.57, 0), (hw - 0.34, hw - 0.32, 0.57, ZFL, 1)):
            o = G.box('black_stepriser_%s%s%d' % (tag, nm, k), Xe + 0.15, XN - 0.06, *sorted((sd * y0, sd * y1)), z0, z1); xform(o, rear)
        for xx in (Xe + 0.15, XN - 0.08):                                 # open step hangers (photo 16), not plates
            for yy in (hw + 0.04, hw - 0.30):
                o = G.box('black_stephanger_%s%s%.2f%.2f' % (tag, nm, xx, yy), xx, xx + 0.02, *sorted((sd * (yy - 0.015), sd * (yy + 0.015))), 0.27, 0.72); xform(o, rear)
    # headlamp, small lamps, signal lamps, sign, camera
    # headlamp (photos 13, 17): bolted base flange, a black drum flaring slightly forward, a black front ring with
    # screws, a silver reflector behind clear glass
    hz = M['zh']
    o = G.cyl('black_headflange_' + tag, (Xf + 0.008, 0, hz), (1, 0, 0), 0.15, 0.016, n=48); xform(o, rear)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        o = G.cyl('chrome_headbolt_%s%d' % (tag, k), (Xf + 0.018, 0.13 * math.cos(a), hz + 0.13 * math.sin(a)), (1, 0, 0), 0.009, 0.01, n=8); xform(o, rear)
    o = G.cyl('black_headlamp_' + tag, (Xf + 0.095, 0, hz), (1, 0, 0), 0.105, 0.16, n=48, r2=0.122); xform(o, rear)
    o = G.tube('black_headbezel_' + tag, [(Xf + 0.18, 0.116 * math.cos(2 * math.pi * k / 48), hz + 0.116 * math.sin(2 * math.pi * k / 48)) for k in range(49)], 0.016, n=8); xform(o, rear)
    for k in range(6):
        a = k * math.pi / 3
        o = G.cyl('chrome_bezelscrew_%s%d' % (tag, k), (Xf + 0.192, 0.118 * math.cos(a), hz + 0.118 * math.sin(a)), (1, 0, 0), 0.006, 0.006, n=8); xform(o, rear)
    o = G.cyl('reflector_head_' + tag, (Xf + 0.15, 0, hz), (1, 0, 0), 0.03, 0.05, n=40, r2=0.102); xform(o, rear)
    o = G.cyl('lens_head_' + tag, (Xf + 0.185, 0, hz), (1, 0, 0), 0.103, 0.006, n=48); xform(o, rear)
    for s in (1, -1):
        o = G.cyl('lens_amber_%s%d' % (tag, s > 0), (Xf + 0.035, s * M['yb'], M['zb']), (1, 0, 0), 0.045, 0.06, n=24); xform(o, rear)
        o = G.cyl('black_amberbase_%s%d' % (tag, s > 0), (Xf + 0.006, s * M['yb'], M['zb']), (1, 0, 0), 0.06, 0.012, n=24); xform(o, rear)
        hood = [(Xf + 0.01, s * M['yb'] + 0.06 * math.cos(a), M['zb'] + 0.06 * math.sin(a)) for a in [math.pi * k / 10 for k in range(11)]]
        hb = G.MB(); i0 = hb.add(hood); i1 = hb.add([(Xf + 0.085, y_, z_) for _, y_, z_ in hood])
        for k in range(10): hb.face([i0[k], i0[k + 1], i1[k + 1], i1[k]])
        o = hb.build('black_amberhood_%s%d' % (tag, s > 0), solid=0.004); xform(o, rear)
        o = G.box('black_siglamp_%s%d' % (tag, s > 0), M['xsl'] - 0.07, M['xsl'] + 0.07, s * M['ysl'] - 0.12, s * M['ysl'] + 0.12, M['zsl'] - 0.12, M['zsl'] + 0.12); xform(o, rear)
        o = G.cyl('lens_red_%s%d' % (tag, s > 0), (M['xsl'] + 0.075, s * M['ysl'], M['zsl']), (1, 0, 0), 0.095, 0.012, n=32); xform(o, rear)
        o = G.cyl('white_sigpost_%s%d' % (tag, s > 0), (M['xsl'], s * M['ysl'], (2.87 + M['zsl'] - 0.12) / 2), (0, 0, 1), 0.025, M['zsl'] - 0.12 - 2.87, n=12); xform(o, rear)
        o = G.box('black_cambox_%s%d' % (tag, s > 0), XN - 0.14, XN, s * hw - 0.07, s * hw + 0.07, 2.60, 2.72); xform(o, rear)
    xk = M['xk']
    o = G.box('sign_board_' + tag, xk - 0.02, xk + 0.02, -0.56, 0.56, 2.97, 3.14); xform(o, rear)
    mb = G.MB(); arc = [(0.085 * math.cos(a), 3.14 + 0.08 + 0.085 * math.sin(a)) for a in [math.pi * i / 16 for i in range(17)]]
    pts2 = [(0.085, 3.14)] + arc + [(-0.085, 3.14)]
    f = mb.add([(xk + 0.021, yy, zz) for yy, zz in pts2]); b = mb.add([(xk - 0.021, yy, zz) for yy, zz in pts2])
    mb.face(f); mb.face(b[::-1]); n = len(pts2)
    for i in range(n): mb.face([f[(i + 1) % n], f[i], b[i], b[(i + 1) % n]])
    o = mb.build('sign_tab_' + tag); xform(o, rear)
    for s in (1, -1):
        o = G.cyl('white_signpost_%s%d' % (tag, s > 0), (xk, s * 0.42, 2.92), (0, 0, 1), 0.015, 0.12, n=10); xform(o, rear)
    o = G.cyl('black_domecam_' + tag, (Xf + 0.0, 0, 2.80), (1, 0, 0), 0.05, 0.08, n=20); xform(o, rear)
    fender(tag, rear)

def decal_strip(name, s0, s1, z0, z1, rear, off=0.004):
    mb = G.MB(); strip(mb, s0, s1, z0, z1, off=off, uv=True); o = mb.build(name)
    uvl = o.data.uv_layers.new(name='UVMap')
    for pi, (ua, ub) in enumerate(mb.uvq):
        for li, (u, v) in zip(o.data.polygons[pi].loop_indices, ((ua, 0), (ub, 0), (ub, 1), (ua, 1))): uvl.data[li].uv = (u, v)
    for p in o.data.polygons: p.use_smooth = True
    xform(o, rear); return o

def doors(tag, nm, sd, rear):
    """photos 11, 12: a bi-fold pair of two tall leaves, each one pane of tinted glass in a thin black frame; six chrome
    hinge knuckles on the middle joint; a chrome grab bar on the front leaf"""
    y = sd * (hw - 0.01); x0, x1 = Xe + 0.15, XN - 0.06; n = 2; w = (x1 - x0) / n; zb, zt = 0.33, ZWT - 0.02; fw = 0.035
    for i in range(n):
        a = x0 + i * w; b = a + w
        for (xa, xb, za, zb_) in ((a, b, zb, zb + 0.06), (a, b, zt - fw, zt), (a, a + fw, zb, zt), (b - fw, b, zb, zt)):
            o = G.box('black_door_%s%s%d_%.2f%.2f' % (tag, nm, i, xa, za), xa, xb, *sorted((y, y - sd * 0.03)), za, zb_); xform(o, rear)
        mb = G.MB(); yy = y - sd * 0.015
        pts = [(a + fw, yy, zb + 0.06), (b - fw, yy, zb + 0.06), (b - fw, yy, zt - fw), (a + fw, yy, zt - fw)]
        mb.face(mb.add(pts if sd < 0 else pts[::-1])); o = mb.build('glass_door_%s%s%d' % (tag, nm, i)); xform(o, rear)
    xm = x0 + w
    for k in range(6):
        z = zb + 0.15 + k * (zt - zb - 0.30) / 5
        o = G.cyl('chrome_hinge_%s%s%d' % (tag, nm, k), (xm, y + sd * 0.004, z), (0, 0, 1), 0.012, 0.05, n=10); xform(o, rear)
    o = G.tube('chrome_handle_%s%s' % (tag, nm), [(x1 - 0.10, y + sd * 0.005, 1.55), (x1 - 0.10, y + sd * 0.035, 1.58), (x1 - 0.10, y + sd * 0.035, 2.15), (x1 - 0.10, y + sd * 0.005, 2.18)], 0.011, n=8); xform(o, rear)

def scissor_gate(tag, nm, sd, rear):
    """the collapsible gate behind the doors (photos 11, 12): vertical flat bars every ~15 cm, two bands of crossed
    links (diamonds) at z 1.65-1.91 and 0.77-1.11, top and bottom tracks"""
    y = sd * (hw - 0.13); x0, x1 = Xe + 0.16, XN - 0.08; nb = max(2, round((x1 - x0) / 0.15)); p = (x1 - x0) / nb
    bm = bmesh.new()
    def bar(A, B, wdt=0.012, dep=0.012):
        A = Vector(A); B = Vector(B); d = (B - A).normalized(); s = Vector((0, 1, 0)).cross(d).normalized() * wdt / 2; t = Vector((0, dep / 2, 0))
        q = [bm.verts.new(c) for c in (A - s - t, B - s - t, B + s - t, A + s - t, A - s + t, B - s + t, B + s + t, A + s + t)]
        for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)): bm.faces.new([q[j] for j in f])
    zlo, zhi = 0.36, ZWT - 0.12
    for i in range(nb + 1): bar((x0 + i * p, y, zlo), (x0 + i * p, y, zhi), 0.016)
    bar((x0, y, zhi), (x1, y, zhi), 0.03); bar((x0, y, zlo), (x1, y, zlo), 0.03)
    for z0, z1 in ((1.65, 1.91), (0.55, 0.95)):
        rows = 2; h = (z1 - z0) / rows
        for r in range(rows):
            for i in range(nb):
                xa, xb = x0 + i * p, x0 + (i + 1) * p; za, zb_ = z0 + r * h, z0 + (r + 1) * h
                bar((xa, y + 0.004, za), (xb, y + 0.004, zb_), 0.010, 0.006); bar((xa, y - 0.004, zb_), (xb, y - 0.004, za), 0.010, 0.006)
    me = bpy.data.meshes.new('black_gate_%s%s' % (tag, nm)); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(o); OBJS.append(o); xform(o, rear)

def fender(tag, rear):
    """photos 13, 17: the fender is a smooth oval in plan, widest at the front, fading to nothing at the side corners
    (no lip beside the doors, photo 20), its top edge rolled over; black bumper strip below"""
    segs, ts = nose(0.30, 0.10, 16); xs_ = xo - ts
    S = [(xs_ + 0.02, -hw)] + [s[1] for s in segs][:-1] + [(xs_ + 0.02, hw)]
    nr = []
    for i in range(len(S)):
        a, b = S[max(i - 1, 0)], S[min(i + 1, len(S) - 1)]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); nr.append((dy / L, -dx / L))
    def out(p):                                   # 0.22 m in front of the dash, fading round the corners to the side
        if p[0] >= Xf - 0.05: return 0.22
        t = max(0.0, min(1.0, (p[0] - (xo - ts)) / (Xf - 0.05 - (xo - ts))))
        return 0.005 + 0.215 * (t ** 1.4)
    PROF = [(0.0, 1.00), (0.80, 0.995), (0.95, 0.985), (1.0, 0.96), (1.0, 0.86), (0.97, 0.83)]   # (fraction of reach, z): flat top, small roll
    mb = G.MB(); R = []
    for f, z in PROF:
        R.append(mb.add([(p[0] + n[0] * (out(p) * f - (0.06 if f == 0 else 0)), p[1] + n[1] * (out(p) * f - (0.06 if f == 0 else 0)), z) for p, n in zip(S, nr)]))
    for r0, r1 in zip(R, R[1:]):
        for i in range(len(S) - 1): mb.face([r0[i], r0[i + 1], r1[i + 1], r1[i]])
    o = mb.build('paint_fender_' + tag, solid=0.008)
    for p in o.data.polygons: p.use_smooth = True
    xform(o, rear)
    mb = G.MB()
    a = mb.add([(p[0] + n[0] * (out(p) * 0.9 - 0.02), p[1] + n[1] * (out(p) * 0.9 - 0.02), 0.83) for p, n in zip(S, nr)])
    b = mb.add([(p[0] + n[0] * (out(p) * 0.9 - 0.02), p[1] + n[1] * (out(p) * 0.9 - 0.02), 0.62) for p, n in zip(S, nr)])
    for i in range(len(S) - 1): mb.face([a[i], a[i + 1], b[i + 1], b[i]])
    o = mb.build('black_bumper_' + tag, solid=0.08)
    for p in o.data.polygons: p.use_smooth = True
    xform(o, rear)

# ------------------------------------------------------------------ roof: white band all round, cove, deck, battery box
def roof():
    """white band, rolled hood and roof deck in one piece (photos 13, 17, 20): vertical white band from the window head,
    then a rounded roll inwards whose plan grows rounder with height, the deck towards the centre line"""
    # photo 13: the white band is vertical up to the roof edge, which turns over with a small radius; the roof behind is flat
    RINGS = [(0.035, None, RS, RF), (0.035, 2.83, RS, RF), (0.030, 2.865, RS + 0.02, RF + 0.04), (0.012, 2.89, RS + 0.05, RF + 0.08),
             (-0.015, 2.905, RS + 0.08, RF + 0.12), (-0.05, 2.915, RS + 0.10, RF + 0.15)]
    rings = []
    for off, z, rs, rf in RINGS:
        B = loop(rs, rf, 14); N = len(B)
        def zz(x):              # photo 13: the cab windows are taller, the white band starts higher over the noses
            if z is not None: return z
            d = max(x - XN, (2 * CX - XN) - x); w = min(1.0, max(0.0, (d + 0.05) / 0.10)); return ZWT + (ZWTE - ZWT) * w
        rings.append([(b[0] + nn[0] * off, b[1] + nn[1] * off, zz(b[0])) for b, nn in ((B[i], vnormal(B, i)) for i in range(N))])
    last = rings[-1]; Lc = (Xf - (2 * CX - Xf)) / 2 - hw
    for s, z in ((0.25, 2.94), (1.0, 2.97)):
        r = []
        for x, y, _ in last:
            c = (max(CX - Lc, min(CX + Lc, x)), 0.0); r.append((x + s * (c[0] - x), y + s * (c[1] - y), z))
        rings.append(r)
    N = len(rings[0]); mb = G.MB(); idx = [mb.add(r) for r in rings]
    for j in range(len(rings) - 1):
        for i in range(N):
            mb.f.append([idx[j][i], idx[j][(i + 1) % N], idx[j + 1][(i + 1) % N], idx[j + 1][i]]); mb.m.append(0)
    o = mb.build('roof_deck', solid=0.03)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
    # battery housing (photo 15): long flat-topped box, front end a little behind the sign
    x0, x1 = 2 * CX - 2.95, 2.95; yb = 0.66; z0, z1 = ZROOF - 0.04, ZROOF + 0.16
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), v.co.y * 2 * yb, (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges], offset=0.025, segments=2, affect='EDGES')
    me = bpy.data.meshes.new('roof_battery'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('roof_battery', me); bpy.context.scene.collection.objects.link(o); OBJS.append(o)
    for p in me.polygons: p.use_smooth = True

def perimeter(poly, n_per_m=30):
    out = []
    for i in range(len(poly)):
        p0, p1 = poly[i], poly[(i + 1) % len(poly)]; L = math.dist(p0, p1); n = max(2, int(L * n_per_m))
        for k in range(n): t = k / n; out.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))
    return out
def vnormal(pts, i): return G.vnormal(pts, i)

# ------------------------------------------------------------------ underframe (hidden mostly by the skirt)
def under():
    """photo 16: a riveted black solebar under the body; below it a weathered single truck: on each side a side frame
    (top and bottom bars joined at the axle boxes), pairs of tall coil springs carrying the body, long rusty brake rods,
    and curved lifeguard bars in front of the outer wheels. The wheels sit behind the frame."""
    xa, xb = 2 * CX - XN + 0.30, XN - 0.30
    G.box('black_floorpan', xa, xb, -hw + 0.14, hw - 0.14, 0.68, ZS + 0.01)
    r = 0.38; gy = 0.525; yf = hw - 0.065          # photo 16: the truck's side frame is nearly flush with the body side
    for sd in (1, -1):
        G.box('black_solebar_%d' % sd, xa, xb, *sorted((sd * (hw - 0.12), sd * (hw - 0.07))), 0.64, ZS + 0.005)
        G.box('black_solebarflange_%d' % sd, xa, xb, *sorted((sd * (hw - 0.12), sd * (hw - 0.04))), 0.64, 0.655)
        n = int((xb - xa) / 0.10)
        for i in range(n):                                                      # rivet row
            G.cyl('black_rivet_%d_%d' % (sd, i), (xa + 0.05 + i * 0.10, sd * (hw - 0.066), 0.69), (0, 1, 0), 0.007, 0.01, n=6)
        # truck side frame
        x0, x1 = CX - 1.5 - 0.55, CX + 1.5 + 0.55
        G.box('gear_topbar_%d' % sd, x0, x1, *sorted((sd * (yf - 0.03), sd * (yf + 0.03))), 0.44, 0.50)
        G.box('gear_botbar_%d' % sd, CX - 1.5, CX + 1.5, *sorted((sd * (yf - 0.025), sd * (yf + 0.025))), 0.27, 0.32)
        for ax in (CX - 1.5, CX + 1.5):
            a_ = '%.1f%d' % (ax, sd)
            G.box('gear_axlebox_' + a_, ax - 0.13, ax + 0.13, *sorted((sd * (yf - 0.06), sd * (yf + 0.06))), 0.25, 0.52)
            G.box('gear_boxlid_' + a_, ax - 0.06, ax + 0.06, *sorted((sd * (yf + 0.06), sd * (yf + 0.085))), 0.33, 0.43)
            sg = 1 if ax > CX else -1
            G.tube('gear_endbrace_' + a_, [(ax + sg * 0.12, sd * yf, 0.30), (ax + sg * 0.55, sd * yf, 0.47)], 0.022, n=6)
            for dx in (-0.30, 0.30):                                             # coil springs, a pair each side of the box
                for k in (0, 1):
                    xs = ax + dx + (k - 0.5) * 0.11
                    pts = [(xs + 0.04 * math.cos(t), sd * yf + 0.04 * math.sin(t), 0.50 + 0.14 * t / (2 * math.pi * 6)) for t in [2 * math.pi * 6 * j / 96 for j in range(97)]]
                    G.tube('steel_spring_%s_%.2f%d' % (a_, dx, k), pts, 0.010, n=6)
            # brake shoe and hanger on the wheel's tread (inside the frame)
            for s2 in (1, -1):
                xsh = ax + s2 * (r + 0.035)
                G.box('rust_brakeshoe_%s%d' % (a_, s2), xsh - 0.03, xsh + 0.03, sd * gy - 0.05, sd * gy + 0.05, r - 0.13, r + 0.13)
                G.tube('rust_hanger_%s%d' % (a_, s2), [(xsh + s2 * 0.02, sd * gy, r + 0.10), (xsh + s2 * 0.05, sd * gy, 0.44)], 0.014, n=6)
            # lifeguard: two curved bars ahead of the outer side of each wheelset, down towards the rail
            for k, dz in enumerate((0.0, 0.07)):
                pts = [(ax + sg * (0.42 + 0.30 * math.sin(t)), sd * (yf - 0.05), 0.46 - dz - 0.30 * (1 - math.cos(t))) for t in [math.pi / 2 * j / 12 for j in range(13)]]
                G.tube('rust_lifeguard_%s%d' % (a_, k), pts, 0.013, n=6)
        G.tube('rust_pullrod_%d' % sd, [(CX - 1.15, sd * (yf - 0.07), 0.33), (CX + 1.15, sd * (yf - 0.07), 0.33)], 0.016, n=6)
        G.tube('rust_pullrod2_%d' % sd, [(CX - 1.15, sd * (yf - 0.07), 0.33), (CX - 1.3, sd * (yf - 0.07), 0.44)], 0.012, n=6)
        G.tube('rust_pullrod3_%d' % sd, [(CX + 1.15, sd * (yf - 0.07), 0.33), (CX + 1.3, sd * (yf - 0.07), 0.44)], 0.012, n=6)
    for ax in (CX + 1.5, CX - 1.5):
        a_ = '%.1f' % ax
        for sd in (1, -1):
            G.cyl('steel_wheel_%s%d' % (a_, sd), (ax, sd * (gy + 0.03), r), (0, 1, 0), r, 0.09, n=40)
            G.cyl('steel_flange_%s%d' % (a_, sd), (ax, sd * (gy - 0.025), r), (0, 1, 0), r + 0.025, 0.02, n=40)
        G.cyl('steel_axle_%s' % a_, (ax, 0, r), (0, 1, 0), 0.06, 2 * (hw - 0.07), n=16)
        sgn = -1 if ax > CX else 1
        G.cyl('black_motor_%s' % a_, (ax + sgn * 0.33, 0, r + 0.02), (0, 1, 0), 0.20, 0.62, n=28)
        G.box('black_gearcase_%s' % a_, ax - 0.10, ax + 0.10, -0.36, -0.24, r - 0.10, r + 0.18)

# ------------------------------------------------------------------ floors
def floors():
    ins = [(x, max(-hw + 0.06, min(hw - 0.06, y))) for x, y in POLY]          # inside the doors' glass
    mb = G.MB(); mb.face(mb.add([(p[0], p[1], ZFL) for p in ins])); mb.build('wood_floor', solid=0.05)

def build_all(interior=True):
    G.clear(); OBJS.clear()
    saloon(); end(False); end(True); roof(); under(); floors()
    # saloon end walls (bulkheads) with a doorway; built in interior34
    if interior:
        import interior34; importlib.reload(interior34); interior34.build(sys.modules[__name__])
    return [o for o in bpy.data.objects if o.type == 'MESH']

if __name__ == '__main__':
    obs = build_all(); print('objects', len(obs), 'CX', round(CX, 3), 'Xr', round(Xr, 3), 'WW', round(WW, 3))
