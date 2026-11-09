# Detailed parts of the office, exec'd inside build.py (uses its helpers: box, plane, cyl, sphere, mat, srgb, M, R, COL, ROOT, T ...)
import random
CJ = json.load(open(T('corridor.json')))
tw = R.get('t_wall', 0.40)          # door-wall thickness (corridor photo solve)
YC = L + tw                         # corridor face of the door wall
YF = 7.98                           # far corridor wall
ZC = 3.0                            # corridor ceiling
CX0, CX1 = -0.24, 22.2              # end wall with the double glass door .. far end
OX0, OX1, OH = 0.275, 1.185, 2.065  # clear door opening
FRAME = mat('Steel door frame', (200, 201, 197), rough=0.45)
LEAFM = mat('Door leaf (photo)', img='door_leaf.jpg', rough=0.45)
LEAFE = mat('Door leaf edge', (205, 204, 198), rough=0.5)
BRONZE = mat('Door plate', (48, 44, 40), rough=0.35, metal=0.7)
GLASS = mat('Glass', (240, 245, 245), rough=0.02)
GLASS.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 1.0
GLASS.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.06
try: GLASS.surface_render_method = 'BLENDED'
except Exception: pass
PVC = mat('White PVC', (236, 236, 232), rough=0.35)
SILL = mat('Window sill', (230, 228, 222), rough=0.25)
blue, beige = CJ['blue_bgr'], CJ['beige_bgr']
OUT_EMIT = 4.0
lift = lambda bgr, k: tuple(min(255, int(v * k)) for v in bgr[::-1])
CBLUE = mat('Corridor paint (upper)', (222, 224, 222), rough=0.8)
CBEIGE = mat('Corridor paint beige', lift(beige, 1.49), rough=0.7)
TERRAZZO = mat('Terrazzo floor', img='terrazzo.jpg', rough=0.3)
CSKIRT = mat('Terrazzo skirting', (176, 176, 170), rough=0.35)
ALU = mat('Brushed aluminium', (205, 207, 210), rough=0.3, metal=1.0)
def emissive_img(name, img, strength):
    m = mat(name, img=img, rough=0.8)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; t_ = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    nt.links.new(t_.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = strength
    return m
def photo_plate(name, img, rough=0.35, metal=0.0):
    return mat(name, img=img, rough=rough, metal=metal)


def quad(name, P, m, col='Room', uv=((0, 0), (1, 0), (1, 1), (0, 1)), parent=None):
    bm = bmesh.new(); u = bm.loops.layers.uv.verify(); vs = [bm.verts.new(p) for p in P]
    f = bm.faces.new(vs)
    for lp in f.loops: lp[u].uv = uv[vs.index(lp.vert)]
    return obj_from_bm(name, bm, m, col, parent)


def tube(name, pts, r, m, seg=10, col='Furniture', parent=None, closed=False):
    """mesh tube along a polyline (parallel-transported rings, flat caps)."""
    P = [Vector(p) for p in pts]
    if closed: P = P + [P[0]]
    bm = bmesh.new(); rings = []
    tang = [(P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized() for i in range(len(P))]
    nrm = tang[0].orthogonal().normalized()
    for i, p in enumerate(P):
        if i: nrm = (nrm - tang[i] * nrm.dot(tang[i])).normalized()
        b2 = tang[i].cross(nrm)
        rings.append([bm.verts.new(p + r * (math.cos(2 * math.pi * k / seg) * nrm + math.sin(2 * math.pi * k / seg) * b2)) for k in range(seg)])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(seg): bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    if not closed:
        bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    return obj_from_bm(name, bm, m, col, parent)


def rbox(name, x0, x1, y0, y1, z0, z1, m, r=0.01, seg=3, col='Furniture', parent=None, deform=None, uvs=0.6):
    """box with rounded edges (bevel applied in the mesh), optional vertex deform f(Vector)->Vector."""
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1, uvs)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=r, segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)
    if deform:
        for v in bm.verts: v.co = deform(v.co.copy())
    return obj_from_bm(name, bm, m, col, parent)


def arc(c, r, a0, a1, n=16, plane='xz'):
    out = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        if plane == 'xz': out.append((c[0] + r * math.cos(a), c[1], c[2] + r * math.sin(a)))
        elif plane == 'yz': out.append((c[0], c[1] + r * math.cos(a), c[2] + r * math.sin(a)))
        else: out.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a), c[2]))
    return out


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); COL['Furniture'].objects.link(e); e.parent = parent or ROOT
    e.location = loc; e.rotation_euler = rot; return e


# =============================================================== door wall, frame and the hinged leaf
for nm, a in (('Door wall left', (-t, OX0 - 0.012, OH + 0.012 * 0)), ):
    pass
box('Door wall left', -0.6, OX0, L, YC, 0, ZC, M['paint'], col='Room')
box('Door wall right', OX1, CX1, L, YC, 0, ZC, M['paint'], col='Room')
box('Door wall header', OX0, OX1, L, YC, OH, ZC, M['paint'], col='Room')
# steel frame: casings on both faces + lining in the reveal + stops
cw_ = R['dx1'] - OX1                 # casing width (~6 cm)
for side, y0, y1 in (('room', L - 0.012, L), ('corridor', YC, YC + 0.012)):
    box(f'Frame casing {side} hinge', R['dx0'], OX0, y0, y1, 0, OH, FRAME, col='Room')
    box(f'Frame casing {side} lock', OX1, R['dx1'], y0, y1, 0, OH, FRAME, col='Room')
    box(f'Frame casing {side} head', R['dx0'], R['dx1'], y0, y1, OH, 2.12, FRAME, col='Room')
box('Frame lining hinge', OX0, OX0 + 0.004, L, YC, 0, OH - 0.004, FRAME, col='Room')
box('Frame lining lock', OX1 - 0.004, OX1, L, YC, 0, OH - 0.004, FRAME, col='Room')
box('Frame lining head', OX0, OX1, L, YC, OH - 0.004, OH, FRAME, col='Room')
for nm, xa, xb in (('hinge', OX0, OX0 + 0.018), ('lock', OX1 - 0.018, OX1)):
    box(f'Door stop {nm}', xa + (0.004 if nm == 'hinge' else 0), xb - (0.004 if nm == 'lock' else 0), L + 0.045, L + 0.060, 0.012, OH - 0.022, FRAME, col='Room')
box('Door stop head', OX0 + 0.004, OX1 - 0.004, L + 0.045, L + 0.060, OH - 0.022, OH - 0.004, FRAME, col='Room')
box('Threshold', OX0, OX1, L + 0.04, L + 0.10, 0, 0.012, ALU, col='Room')
plane('Corridor floor under door', (OX0, L + 0.10, 0.0), (1, 0, 0), (0, 1, 0), OX1 - OX0, YC + 0.012 - L - 0.10, TERRAZZO, uv_tile=(0.30, 0.30))

# leaf: pivot at the hinge, leaf along +x in the pivot's frame; rotate the pivot about z to open (negative = into the room)
LX0, LX1, LZ0, LZ1 = CJ['leaf']; LT = 0.04
piv = empty('Door pivot', (LX0, L + 0.003, 0))
lw = LX1 - LX0
bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
V = [bm.verts.new(v) for v in [(0, 0, LZ0), (lw, 0, LZ0), (lw, LT, LZ0), (0, LT, LZ0), (0, 0, LZ1), (lw, 0, LZ1), (lw, LT, LZ1), (0, LT, LZ1)]]
faces = [((0, 1, 5, 4), 0, lambda co: (co.x / lw, (co.z - LZ0) / (LZ1 - LZ0))),            # room face (photo)
         ((2, 3, 7, 6), 0, lambda co: (co.x / lw, (co.z - LZ0) / (LZ1 - LZ0))),            # corridor face (same photo; handle side matches)
         ((0, 3, 2, 1), 1, None), ((4, 5, 6, 7), 1, None), ((1, 2, 6, 5), 1, None), ((3, 0, 4, 7), 1, None)]
for idx, mi, fuv in faces:
    f = bm.faces.new([V[i] for i in idx]); f.material_index = mi
    for lp in f.loops: lp[uv].uv = fuv(lp.vert.co) if fuv else (0, 0)
leaf = obj_from_bm('Door leaf', bm, [LEAFM, LEAFE], parent=piv)
# lever handles + long backplates both sides, key in the lock (as in the inside-out photo)
hx, hz = 1.085 - LX0, 1.02
for side, yy, s in (('room', -0.002, -1), ('corridor', LT + 0.002, 1)):
    box(f'Handle plate {side}', hx - 0.022, hx + 0.022, min(yy, yy + s * 0.008), max(yy, yy + s * 0.008), hz - 0.17, hz + 0.05, BRONZE, parent=piv)
    cyl(f'Handle rose {side}', (hx, yy + s * 0.008, hz), (hx, yy + s * 0.030, hz), 0.011, M['chrome'], parent=piv)
    tube(f'Handle lever {side}', [(hx, yy + s * 0.030, hz), (hx, yy + s * 0.058, hz), (hx - 0.115, yy + s * 0.062, hz - 0.004)], 0.0085, M['chrome'], parent=piv)
    cyl(f'Lock cylinder {side}', (hx, yy, hz - 0.12), (hx, yy + s * 0.014, hz - 0.12), 0.009, M['chrome'], parent=piv)
cyl('Key', (hx, -0.016, hz - 0.12), (hx, -0.040, hz - 0.12), 0.004, ALU, parent=piv)
box('Key bow', hx - 0.012, hx + 0.012, -0.046, -0.040, hz - 0.15, hz - 0.12, ALU, parent=piv)
for zh in (0.25, 1.05, 1.85):
    cyl(f'Hinge {zh}', (OX0 + 0.004, L + 0.003, zh), (OX0 + 0.004, L + 0.003, zh + 0.10), 0.008, M['chrome'], col='Room')
piv.rotation_euler = (0, 0, math.radians(-75))        # open as in both door photos; the viewer opens/closes it

# =============================================================== corridor (measured: four photos near our door; the long view for the rest)
YF = 7.98; ZC = 3.0; CX0, CX1 = -0.24, 22.2
plane('Corridor floor', (CX0, YC, 0), (1, 0, 0), (0, 1, 0), CX1 - CX0, YF - YC, TERRAZZO, uv_tile=(0.30, 0.30))
plane('Corridor ceiling', (CX0, YC, ZC), (1, 0, 0), (0, 1, 0), CX1 - CX0, YF - YC, M['ceiling'], flip=True)
for k_, (xa, xb) in enumerate(((-0.24, 0.08), (3.76, 4.10), (9.93, 10.27), (16.1, 16.44))):
    box(f'Corridor beam {k_}', xa, xb, YC, YF, 2.45 if k_ else 2.50, ZC, M['ceiling'], col='Room')
END = emissive_img('Corridor end wall (photo)', 'endwall_raw.jpg', 0.55)
box('Corridor end wall body', CX0 - 0.25, CX0, YC, YF, 0, ZC, CBLUE, col='Room')
quad('Corridor end wall', [(CX0 + 0.002, YC, 0), (CX0 + 0.002, YC + 2.25, 0), (CX0 + 0.002, YC + 2.25, ZC), (CX0 + 0.002, YC, ZC)], END)
quad('Corridor end wall rest', [(CX0 + 0.002, YC + 2.25, 0), (CX0 + 0.002, YF, 0), (CX0 + 0.002, YF, ZC), (CX0 + 0.002, YC + 2.25, ZC)], CBLUE)
box('Corridor far end', CX1, CX1 + 0.25, YC, YF, 0, ZC, CBLUE, col='Room')
box('Far end door frame', CX1 - 0.012, CX1, 6.30, 7.46, 0, 2.18, PVC, col='Room')
box('Far end door', CX1 - 0.03, CX1 - 0.012, 6.36, 7.40, 0.01, 2.12, PVC, col='Room')
box('Far end door glass', CX1 - 0.032, CX1 - 0.03, 6.50, 7.26, 1.05, 1.95, GLASS, col='Room')
# far wall: plain to x 5.55 (white over a beige dado), then the window band: deep white sill at 0.97-1.0, windows 1.0-2.5 set in
WX0, WX1, WS, WT_ = 5.55, 21.5, 1.0, 2.50
box('Far wall plain', CX0, WX0, YF, YF + 0.30, 0, ZC, CBLUE, col='Room')
box('Far wall below windows', WX0, WX1, YF, YF + 0.30, 0, WS, CBLUE, col='Room')
box('Far wall above windows', WX0, WX1, YF, YF + 0.30, WT_, ZC, CBLUE, col='Room')
box('Far wall end piece', WX1, CX1, YF, YF + 0.30, 0, ZC, CBLUE, col='Room')
box('Far wall dado', CX0, CX1, YF - 0.004, YF, 0, 0.97 if False else 1.05, CBEIGE, col='Room')
box('Far wall skirting', CX0, CX1, YF - 0.015, YF, 0, 0.09, CSKIRT, col='Room')
box('Corridor window sill', WX0 - 0.03, WX1 + 0.03, YF - 0.16, YF + 0.10, WS - 0.03, WS, SILL, col='Room')
CORR_OUT = mat('Corridor outdoor glow', (238, 240, 236), rough=0.9, emit=(236, 240, 236), emit_strength=1.3)
plane('Corridor outdoor', (WX0, YF + 0.45, WS - 0.2), (1, 0, 0), (0, 0, 1), WX1 - WX0, WT_ - WS + 0.4, CORR_OUT, col='Room')
CGLASS = mat('Corridor window glass', (150, 160, 165), rough=0.04, metal=0.2)
CGLASS.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 0.55
nwin = int((WX1 - WX0) // 1.22)
for k_ in range(nwin):
    xw = WX0 + k_ * (WX1 - WX0) / nwin; ww = (WX1 - WX0) / nwin
    for nm2, a in (('L', (xw, xw + 0.06, WS, WT_)), ('B', (xw + 0.06, xw + ww - 0.06, WS, WS + 0.06)), ('T', (xw + 0.06, xw + ww - 0.06, WT_ - 0.07, WT_)),
                   ('M', (xw + ww / 2 - 0.035, xw + ww / 2 + 0.035, WS + 0.06, WT_ - 0.07)), ('R', (xw + ww - 0.06, xw + ww, WS, WT_))):
        box(f'Corridor window {k_} frame {nm2}', a[0], a[1], YF + 0.10, YF + 0.17, a[2], a[3], PVC, col='Room')
    for s_, (a0, a1) in enumerate(((xw + 0.06, xw + ww / 2 - 0.035), (xw + ww / 2 + 0.035, xw + ww - 0.06))):
        quad(f'Corridor window {k_} glass {s_}', [(a1, YF + 0.14, WS + 0.06), (a0, YF + 0.14, WS + 0.06), (a0, YF + 0.14, WT_ - 0.07), (a1, YF + 0.14, WT_ - 0.07)], CGLASS)
    box(f'Corridor window {k_} handle', xw + ww / 2 - 0.06, xw + ww / 2 - 0.045, YF + 0.075, YF + 0.10, 1.70, 1.84, PVC, col='Room')
# door wall towards the long corridor: two-tone paint, moulding over our door only, skirting
for nm, (xa, xb) in (('door L', (CX0, R['dx0'])), ('door R', (R['dx1'], CX1))):
    box(f'Dado {nm}', xa, xb, YC, YC + 0.004, 0, 1.10, CBEIGE, col='Room')
    box(f'Corridor skirting {nm}', xa, xb, YC, YC + 0.015, 0, 0.09, CSKIRT, col='Room')
box('Door wall corridor blue L', CX0, R['dx0'], YC, YC + 0.002, 1.10, ZC, CBLUE, col='Room')
box('Door wall corridor blue R', R['dx1'], CX1, YC, YC + 0.002, 1.10, ZC, CBLUE, col='Room')
box('Door wall corridor blue head', R['dx0'], R['dx1'], YC, YC + 0.002, 2.16, ZC, CBLUE, col='Room')
box('Door wall moulding L', CX0, R['dx0'], YC, YC + 0.018, 2.12, 2.16, PVC, col='Room')
box('Door wall moulding R', R['dx1'], CX1, YC, YC + 0.018, 2.12, 2.16, PVC, col='Room')
box('Door wall moulding head', R['dx0'], R['dx1'], YC + 0.0121, YC + 0.018, 2.1201, 2.16, PVC, col='Room')
# fire cabinet from the long view: 0.61 x 0.69, a shallow red steel box, label, round lock, two bar handles
FC = json.load(open(T('firecab.json')))
FIRE = mat('Fire cabinet red', (150, 18, 24), rough=0.35)
fx0, fx1, fz0, fz1, fd = FC['x0'], FC['x1'], FC['z0'], FC['z1'], 0.07
rbox('Fire cabinet', fx0, fx1, YC, YC + fd, fz0, fz1, FIRE, r=0.006)
box('Fire cabinet door seam', fx0 + 0.015, fx1 - 0.015, YC + fd, YC + fd + 0.001, fz0 + 0.015, fz0 + 0.017, M['fabric'])
LBL = mat('Fire cabinet label', img='firecab_label.png', rough=0.4)
lx1, lx0 = fx1 - 0.24 * (fx1 - fx0), fx1 - 0.82 * (fx1 - fx0); lz1, lz0 = fz1 - 0.40 * (fz1 - fz0), fz1 - 0.57 * (fz1 - fz0)
quad('Fire cabinet label', [(lx1, YC + fd + 0.002, lz0), (lx0, YC + fd + 0.002, lz0), (lx0, YC + fd + 0.002, lz1), (lx1, YC + fd + 0.002, lz1)], LBL,
     uv=((0, 0), (1, 0), (1, 1), (0, 1)))
cyl('Fire cabinet lock', (fx1 - 0.075, YC + fd, (lz0 + lz1) / 2), (fx1 - 0.075, YC + fd + 0.012, (lz0 + lz1) / 2), 0.016, M['chrome'])
for zh0, zh1 in ((fz1 - 0.30 * (fz1 - fz0), fz1 - 0.12 * (fz1 - fz0)), (fz1 - 0.85 * (fz1 - fz0), fz1 - 0.68 * (fz1 - fz0))):
    tube('Fire cabinet handle', [(fx0 + 0.035, YC + fd, zh0), (fx0 + 0.035, YC + fd + 0.025, zh0 + 0.01), (fx0 + 0.035, YC + fd + 0.025, zh1 - 0.01), (fx0 + 0.035, YC + fd, zh1)], 0.006, M['chrome'])
# riser pipe and the next office door (just past the pipe), further doors along our wall
cyl('Corridor riser pipe', (3.45, YC + 0.06, 0), (3.45, YC + 0.06, ZC), 0.035, M['white_plastic'])
for k_, xd in enumerate((3.65, 8.3, 12.9, 17.4)):
    box(f'Office door {k_} casing', xd - 0.06, xd + 1.10, YC, YC + 0.012, 0, 2.12, FRAME, col='Room')
    box(f'Office door {k_} leaf', xd, xd + 1.04, YC + 0.012, YC + 0.03, 0.01, 2.06, LEAFE, col='Room')
    tube(f'Office door {k_} handle', [(xd + 0.95, YC + 0.03, 1.02), (xd + 0.95, YC + 0.08, 1.02), (xd + 0.83, YC + 0.085, 1.02)], 0.009, M['chrome'])
# blue recycling box by the glass door (in both views of that end)
BLUEB = mat('Recycling box blue', (40, 140, 215), rough=0.4)
rbox('Recycling box', 0.32, 0.78, 7.52, 7.97, 0.0, 0.55, BLUEB, r=0.01)
cyl('Recycling box opening', (0.55, 7.745, 0.551), (0.55, 7.745, 0.553), 0.10, M['fabric'])
# fluorescent battens along the corridor
for k_, xl in enumerate((2.39, 5.8, 9.16, 12.6, 16.0, 19.4)):
    rbox(f'Corridor light {k_} channel', xl - 0.62, xl + 0.62, 6.57, 6.69, ZC - 0.045, ZC, M['white_plastic'], r=0.004)
    cyl(f'Corridor light {k_} tube', (xl - 0.6, 6.63, ZC - 0.06), (xl + 0.6, 6.63, ZC - 0.06), 0.013, M['tube'])
# name plate, notice board, room sign (photo textures on proud plates)
def wall_plate(name, key, depth, m):
    x0_, x1_, z0_, z1_ = CJ[key]
    box(name + ' body', x0_, x1_, YC + 0.004, YC + depth - 0.001, z0_, z1_, ALU, col='Room')
    quad(name, [(x1_, YC + depth, z0_), (x0_, YC + depth, z0_), (x0_, YC + depth, z1_), (x1_, YC + depth, z1_)], m)
wall_plate('Name plate', 'nameplate', 0.008, photo_plate('Name plate (photo)', 'nameplate.jpg', 0.3, 0.6))
wall_plate('Notice board', 'noticeboard', 0.014, photo_plate('Notice board (photo)', 'noticeboard.jpg', 0.4, 0.3))
wall_plate('Room sign', 'roomsign', 0.007, photo_plate('Room sign (photo)', 'roomsign.jpg', 0.5))
# =============================================================== window wall with real openings, frames, glass, blinds
WT = 0.35; ZS, ZT = 1.02, 2.30
WINS = {'A': (1.46, 2.50), 'B': (0.20, 1.24)}
xs = sorted([v for p in WINS.values() for v in p])
for nm, xa, xb in (('Window wall left', -0.12, xs[0]), ('Window wall pier', xs[1], xs[2]), ('Window wall right', xs[3], W + 0.12)):
    box(nm, xa, xb, -WT, 0, 0, H, M['paint'], col='Room')
for k, (x0_, x1_) in WINS.items():
    box(f'Window {k} below', x0_, x1_, -WT, 0, 0, ZS, M['paint'], col='Room')
    box(f'Window {k} above', x0_, x1_, -WT, 0, ZT, H, M['paint'], col='Room')
    box(f'Window {k} sill', x0_ - 0.02, x1_ + 0.02, -0.13, 0.035, ZS - 0.02, ZS + 0.005, SILL, col='Room')
    # PVC frame 7 cm in the reveal at y=-0.13..-0.20, two casements split in the middle
    yf0, yf1 = -0.20, -0.13
    fw = 0.065
    for nm2, a in (('L', (x0_, x0_ + fw, ZS, ZT)), ('R', (x1_ - fw, x1_, ZS, ZT)), ('B', (x0_ + fw, x1_ - fw, ZS, ZS + fw)), ('T', (x0_ + fw, x1_ - fw, ZT - fw, ZT))):
        box(f'Window {k} frame {nm2}', a[0], a[1], yf0, yf1, a[2], a[3], PVC, col='Room')
    xm = (x0_ + x1_) / 2
    box(f'Window {k} mullion', xm - 0.04, xm + 0.04, yf0, yf1 + 0.01, ZS + fw, ZT - fw, PVC, col='Room')
    for s_, (a0, a1) in enumerate(((x0_ + fw, xm - 0.04), (xm + 0.04, x1_ - fw))):
        for nm3, b in (('l', (a0, a0 + 0.06, ZS + fw, ZT - fw)), ('r', (a1 - 0.06, a1, ZS + fw, ZT - fw)),
                       ('b', (a0 + 0.06, a1 - 0.06, ZS + fw, ZS + fw + 0.07)), ('t', (a0 + 0.06, a1 - 0.06, ZT - fw - 0.07, ZT - fw))):
            box(f'Window {k} sash {s_}{nm3}', b[0], b[1], yf1 - 0.005, yf1 + 0.012, b[2], b[3], PVC, col='Room')
        quad(f'Window {k} glass {s_}', [(a0 + 0.06, yf0 + 0.03, ZS + fw + 0.07), (a1 - 0.06, yf0 + 0.03, ZS + fw + 0.07),
                                        (a1 - 0.06, yf0 + 0.03, ZT - fw - 0.07), (a0 + 0.06, yf0 + 0.03, ZT - fw - 0.07)], GLASS)
        hxk = a1 - 0.03 if s_ == 0 else a0 + 0.03
        box(f'Window {k} handle {s_}', hxk - 0.012, hxk + 0.012, yf1 + 0.012, yf1 + 0.03, 1.55, 1.62, PVC, col='Room')
        box(f'Window {k} handle grip {s_}', hxk - 0.008, hxk + 0.008, yf1 + 0.03, yf1 + 0.045, 1.43, 1.55, PVC, col='Room')
    # roller blind: fabric photo from 1.51 to the roller, bottom bar, roller box
    BL = mat(f'Blind {k} (photo)', img=f'blind_{k}.jpg', rough=0.9)
    nt = BL.node_tree; b_ = nt.nodes['Principled BSDF']; ti = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    nt.links.new(ti.outputs['Color'], b_.inputs['Emission Color']); b_.inputs['Emission Strength'].default_value = 0.9
    quad(f'Blind {k}', [(x1_, -0.03, 1.49), (x0_, -0.03, 1.49), (x0_, -0.03, 2.30), (x1_, -0.03, 2.30)], BL,
         uv=((0, 0), (1, 0), (1, 1), (0, 1)))
    cyl(f'Blind {k} bar', (x0_ + 0.02, -0.03, 1.495), (x1_ - 0.02, -0.03, 1.495), 0.009, M['white_plastic'])
    cyl(f'Blind {k} roller', (x0_ + 0.01, -0.035, 2.27), (x1_ - 0.01, -0.035, 2.27), 0.022, M['white_plastic'])
    tube(f'Blind {k} chain', [(x0_ + 0.03, -0.01, 2.26), (x0_ + 0.03, -0.01, 1.30)], 0.002, M['white_plastic'])
# outdoor: behind each clear pane, the view that pane shows in the window photo (glows like daylight)
for k_, pn in enumerate(json.load(open(T('outdoor_panes.json')))):
    quad(f'Outdoor view {k_}', [(pn['x1'], pn['y'], pn['z0']), (pn['x0'], pn['y'], pn['z0']), (pn['x0'], pn['y'], pn['z1']), (pn['x1'], pn['y'], pn['z1'])],
         emissive_img(f'Outdoor pane {k_} (photo)', pn['file'], OUT_EMIT), uv=((1, 0), (0, 0), (0, 1), (1, 1)))
# heating pipes in the corner by the chase and the radiator feed
for xp in (0.135, 0.17):
    cyl(f'Riser pipe {xp}', (xp, 0.035, 0), (xp, 0.035, H), 0.016, M['enamel'])

# =============================================================== bookcase as a real carcass, books and objects in 3D
BCJ = json.load(open(T('bookcols.json')))
bx0_, by0_, bw_ = W - R['bd'], R['b0'], R['bw']
BTOP = 1.83 - 22 / 400.0
FRONT = mat('Bookcase front (photo)', img='bookcase_front.jpg', rough=0.5)
PPM = 400.0
def front_uv(o):
    """faces looking at the room (-x) take the photo by their y,z; everything else stays maple."""
    me = o.data
    if FRONT.name not in [m.name for m in me.materials if m]: me.materials.append(FRONT)
    fi = [m.name for m in me.materials].index(FRONT.name)
    uvl = me.uv_layers.active or me.uv_layers.new()
    mw = o.matrix_world
    for poly in me.polygons:
        n = (mw.to_3x3() @ poly.normal).normalized()
        if n.x < -0.7:
            poly.material_index = fi
            for li in poly.loop_indices:
                co = mw @ me.vertices[me.loops[li].vertex_index].co
                uvl.data[li].uv = (((by0_ + bw_) - co.y) / bw_, co.z / 1.83)
bc = empty('Bookcase', (0, 0, 0))
pt = 0.018
parts = [box('Bookcase side L', bx0_, W, by0_ + bw_ - pt, by0_ + bw_, 0.03, BTOP, M['maple'], parent=bc),
         box('Bookcase side R', bx0_, W, by0_, by0_ + pt, 0.03, BTOP, M['maple'], parent=bc),
         box('Bookcase top', bx0_, W, by0_, by0_ + bw_, BTOP - pt, BTOP, M['maple'], parent=bc),
         box('Bookcase back', W - 0.012, W, by0_ + pt, by0_ + bw_ - pt, 0.03, BTOP - pt, mat('Bookcase back panel', (224, 220, 212), rough=0.5), parent=bc),
         box('Bookcase plinth', bx0_ + 0.02, W - 0.012, by0_ + pt, by0_ + bw_ - pt, 0.0, 0.05, M['steel'], parent=bc)]
SHELVES = {'s1': 1.4725, 's2': 1.105, 's3': 0.7525, 'bottom': 0.07}
for nm, zt in SHELVES.items():
    parts.append(box(f'Bookcase shelf {nm}', bx0_ + 0.006, W - 0.012, by0_ + pt, by0_ + bw_ - pt, zt - pt, zt, M['maple'], parent=bc))
# lower cabinet doors with handles
dmid = by0_ + bw_ / 2
for nm, ya, yb in (('left', dmid + 0.002, by0_ + bw_ - 0.002), ('right', by0_ + 0.002, dmid - 0.002)):
    parts.append(box(f'Bookcase door {nm}', bx0_ - 0.004, bx0_ + 0.014, ya, yb, 0.055, 0.735, M['maple'], parent=bc))
    yh = ya + 0.04 if nm == 'left' else yb - 0.04
    tube(f'Bookcase handle {nm}', [(bx0_ - 0.004, yh, 0.58), (bx0_ - 0.03, yh, 0.585), (bx0_ - 0.03, yh, 0.645), (bx0_ - 0.004, yh, 0.65)], 0.004, M['chrome'], parent=bc)
for p_ in parts:
    if 'back' not in p_.name: front_uv(p_)
# books: one sheared prism per book (the photo's spine on its front, its cover colour on the sides, cream page block on top)
BK = json.load(open(T('books.json')))
import numpy as _np
PAGES = mat('Book pages', (226, 220, 204), rough=0.85)
comp_floor = {'c1': SHELVES['s1'], 'c2': SHELVES['s2'], 'c3': SHELVES['s3']}
comp_ceiling = {'c1': BTOP - pt, 'c2': SHELVES['s1'] - pt, 'c3': SHELVES['s2'] - pt}
YF_ = by0_ + bw_
def lin(bgr):
    return srgb((bgr[2], bgr[1], bgr[0]))
def prism(name, ya, yb, zf, hgt, k, xa, xb, side_m, top_m, parent):
    """book prism: bottom edge ya>yb at z=zf, top edge shifted by -k*hgt in y (leaning), x from xa (front) to xb."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    pts = [(ya, zf), (yb, zf), (yb - k * hgt, zf + hgt), (ya - k * hgt, zf + hgt)]
    F = [bm.verts.new((xa, y, z)) for y, z in pts]; B = [bm.verts.new((xb, y, z)) for y, z in pts]
    faces = [(F[::-1], 2), ([B[0], B[1], B[2], B[3]], 0), ([F[0], F[1], B[1], B[0]], 0), ([F[1], F[2], B[2], B[1]], 0),
             ([F[2], F[3], B[3], B[2]], 1), ([F[3], F[0], B[0], B[3]], 0)]
    for vs, mi in faces:
        f = bm.faces.new(vs); f.material_index = mi
    o = obj_from_bm(name, bm, [side_m, top_m, FRONT], parent=parent)
    me = o.data; uvl = me.uv_layers.active
    for poly in me.polygons:
        if poly.material_index == 2:
            for li in poly.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                uvl.data[li].uv = ((YF_ - co.y) / bw_, co.z / 1.83)
    return o
rnd = random.Random(11)
for ck, dct in BK.items():
    s_, (r0, r1) = dct['shear'], dct['rows']; zf = comp_floor[ck]
    for j, b in enumerate(dct['books']):
        k = -b.get('shear', s_)
        ya, yb = YF_ - b['c0'] / PPM, YF_ - b['c1'] / PPM
        hgt = min((r1 - b['top']) / PPM, comp_ceiling[ck] - zf - 0.004)
        if hgt < 0.03: continue
        dep = rnd.uniform(0.15, 0.22); off = rnd.uniform(0.0, 0.012)
        cover = mat(f'Book cover {ck} {j}', tuple(int(v) for v in b['bgr'][::-1]), rough=0.55)
        prism(f'Book {ck} {j}', ya, yb + 0.0008, zf, hgt, k, bx0_ + 0.022 + off, bx0_ + 0.022 + off + dep, cover, PAGES, bc)
# objects on the shelves: each one is its photo silhouette (GrabCut mask) built as a solid whose front bulges like the
# real object (rounded by the distance to its outline); every face takes the frontal photo, so from the front it is the photo
ITM = json.load(open(T('items.json')))
SPEC = {   # name: (front x offset from the bookcase front, base depth, bulge radius)
    'balloon': (0.06, 0.03, 0.03), 'football': (0.035, 0.03, 0.065), 'cat_apple': (0.06, 0.02, 0.025), 'gears': (0.012, 0.03, 0.012),
    'trays': (0.02, 0.30, 0.0), 'pen_box': (0.03, 0.07, 0.0), 'green_box': (0.28, 0.05, 0.0), 'phone': (0.04, 0.07, 0.05),
    'name_set': (0.012, 0.012, 0.004)}
def item_solid(name, it, xfront, base, rad):
    mk = _np.array(it['mask'], bool); dist = _np.array(it['dist']); st = it['step']
    h_, w_ = mk.shape
    def world(i, j):   # grid row i, col j -> (y, z)
        c_ = it['X0'] + j * st; r_ = it['Y0'] + i * st
        return YF_ - c_ / 1000.0, 1.83 - r_ / 1000.0
    def bulge(i, j):
        if rad <= 0: return 0.0
        dd = min(dist[min(i, h_ - 1)][min(j, w_ - 1)], rad)
        return rad * math.sqrt(max(0.0, 1 - (1 - dd / rad) ** 2))
    xback = bx0_ + xfront + base + rad
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    FV, BV = {}, {}
    def fv(i, j):
        if (i, j) not in FV:
            y, z = world(i, j); FV[(i, j)] = bm.verts.new((xback - base - bulge(i, j), y, z)); BV[(i, j)] = bm.verts.new((xback, y, z))
        return FV[(i, j)], BV[(i, j)]
    cells = [(i, j) for i in range(h_ - 1) for j in range(w_ - 1) if mk[i, j] and mk[i + 1, j] and mk[i, j + 1] and mk[i + 1, j + 1]]
    cellset = set(cells); edges = {}
    for i, j in cells:
        q = [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]
        bm.faces.new([fv(*p)[0] for p in q][::-1]); bm.faces.new([fv(*p)[1] for p in q])
        for a, b in zip(q, q[1:] + q[:1]):
            k_ = tuple(sorted((a, b))); edges[k_] = edges.get(k_, 0) + 1
    for (a, b), n in edges.items():          # outline edges: side walls from the bulged front to the flat back
        if n == 1:
            fa, ba = fv(*a); fb, bb_ = fv(*b)
            try: bm.faces.new((fa, fb, bb_, ba))
            except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        for lp in f.loops:
            co = lp.vert.co; lp[uvl].uv = ((YF_ - co.y) / bw_, co.z / 1.83)
    return obj_from_bm(name, bm, FRONT, parent=bc)
for nm, it in ITM.items():
    if nm not in ('pen_box', 'green_box'): continue        # boxes: their photo silhouette is exact; the rest is modelled below
    xf, base, rad = SPEC[nm]
    o = item_solid(f'Shelf {nm}', it, xf, base, rad)
    o.data.materials[0] = FRONT
# --- red rotary telephone (Western Electric 500 type): body from its side profile, extruded, tapered toward the top and
#     rounded; the photo's dial on the 33 deg slope; cradle posts; handset with round ear/mouth cups and a curved handle
REDP = mat('Telephone red gloss', (168, 16, 24), rough=0.14)
try: REDP.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 0.6
except Exception: pass
DIAL = mat('Rotary dial (photo)', img='dial.jpg', rough=0.2)
tp = empty('Rotary telephone', (bx0_ + 0.16, YF_ - 107 / PPM, SHELVES['s3']), (0, 0, 0), parent=bc)
PROF = [(-0.112, 0.004), (-0.112, 0.014), (-0.066, 0.116), (-0.046, 0.124), (0.080, 0.124), (0.112, 0.084), (0.112, 0.004)]
HW = 0.1075
bm = bmesh.new(); A = [bm.verts.new((x, -HW, z)) for x, z in PROF]; B = [bm.verts.new((x, HW, z)) for x, z in PROF]
bm.faces.new(A[::-1]); bm.faces.new(B)
n = len(PROF)
for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.016, segments=6, profile=0.5, affect='EDGES', clamp_overlap=True)
for v in bm.verts:
    t = max(0.0, min(1.0, v.co.z / 0.116)); v.co.y *= (1 - 0.03 * t)
body = obj_from_bm('Phone body', bm, REDP, parent=tp)
for poly in body.data.polygons: poly.use_smooth = True
for sx in (-0.085, 0.085):
    for sy in (-0.08, 0.08):
        cyl('Phone foot', (sx, sy, 0), (sx, sy, 0.005), 0.009, M['fabric'], parent=tp)
# dial on the slope (from (-0.112, 0.024) to (-0.062, 0.098))
d_ = Vector((0.046, 0, 0.102)).normalized(); _n = Vector((-d_.z, 0, d_.x)); _u = Vector((0, -1, 0)); _v = d_
_c = Vector((-0.088, 0.0, 0.066)) + _n * 0.004
bm = bmesh.new(); uvl = bm.loops.layers.uv.verify(); ctr = bm.verts.new(_c); ring = []
for k in range(48):
    a = 2 * math.pi * k / 48; ring.append(bm.verts.new(_c + 0.054 * (math.cos(a) * _u + math.sin(a) * _v)))
for k in range(48):
    f = bm.faces.new((ctr, ring[k], ring[(k + 1) % 48]))
    for lp in f.loops:
        q = lp.vert.co - _c; lp[uvl].uv = (0.5 + q.dot(_u) / 0.108, 0.5 + q.dot(_v) / 0.108)
obj_from_bm('Phone dial', bm, DIAL, parent=tp)
tube('Phone dial rim', [(_c + 0.0555 * (math.cos(a) * _u + math.sin(a) * _v))[:] for a in [2 * math.pi * k / 48 for k in range(48)]], 0.0032, REDP, parent=tp, closed=True)
_fs = _c + _n * 0.003 + 0.036 * (math.cos(-0.6) * _u + math.sin(-0.6) * _v)
tube('Phone finger stop', [_fs[:], (_fs + 0.012 * (math.cos(-0.6) * _u + math.sin(-0.6) * _v) + _n * 0.004)[:]], 0.0025, M['chrome'], parent=tp)
# cradle: two rounded posts on the top, the plunger recess between them
for s_ in (-1, 1):
    rbox(f'Phone cradle post {s_}', -0.010, 0.030, s_ * 0.052 - 0.012, s_ * 0.052 + 0.012, 0.118, 0.132, REDP, r=0.010, seg=4, parent=tp)
box('Phone cradle recess', -0.008, 0.028, -0.038, 0.038, 0.122, 0.125, mat('Phone recess', (70, 8, 12), rough=0.4), parent=tp)
# handset lying across: cups (ear left, mouth right) resting on the posts, flattened curved handle between them
for s_ in (-1, 1):
    cc = Vector((0.000, s_ * 0.088, 0.130))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1.0)
    for v in bm.verts:
        z = v.co.z; v.co = Vector((v.co.x * 0.036, v.co.y * 0.036, (z * 0.016 if z > 0 else z * 0.016)))
    bmesh.ops.transform(bm, matrix=Matrix.Translation(cc + Vector((0, 0, 0.012))), verts=bm.verts)
    cup = obj_from_bm(f'Phone handset cup {s_}', bm, REDP, parent=tp)
    for poly in cup.data.polygons: poly.use_smooth = True
    cyl(f'Phone handset cup wall {s_}', cc - Vector((0, 0, 0.004)), cc + Vector((0, 0, 0.012)), 0.036, REDP, seg=28, parent=tp)
hp = [(0.000, -0.092, 0.146), (0.000, -0.065, 0.155), (0.000, -0.030, 0.159), (0.000, 0.0, 0.160), (0.000, 0.030, 0.159), (0.000, 0.065, 0.155), (0.000, 0.092, 0.146)]
hg = tube('Phone handset handle', hp, 0.019, REDP, seg=18, parent=tp)
for v in hg.data.vertices: v.co.x = v.co.x * 1.35
for poly in hg.data.polygons: poly.use_smooth = True
# coiled cord from the ear cup down the viewer's left side, then along the shelf behind the phone
coil = [(-0.005 + 0.010 * math.cos(k * 0.55), 0.122 + 0.010 * math.sin(k * 0.55), 0.115 - 0.107 * k / 260) for k in range(261)]
tube('Phone coiled cord', coil, 0.0034, REDP, seg=8, parent=tp)
tube('Phone line cord', [(0.112, 0.06, 0.010), (0.16, 0.05, 0.004), (0.20, 0.0, 0.004)], 0.003, REDP, seg=8, parent=tp)

# --- three stacked clear letter trays with paper stacks (cols 6-126, rows 214-290 of the front photo)
ACR = mat('Clear acrylic', (244, 247, 248), rough=0.06)
ACR.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.30
try: ACR.surface_render_method = 'BLENDED'
except Exception: pass
PAPER = mat('Paper', (240, 240, 236), rough=0.85)
ty0, ty1 = YF_ - 124 / PPM, YF_ - 8 / PPM; tx0 = bx0_ + 0.025; tz = SHELVES['s2']
for k in range(3):
    zb = tz + 0.004 + k * 0.064
    box(f'Tray {k} bottom', tx0, tx0 + 0.33, ty0, ty1, zb, zb + 0.004, ACR, parent=bc)
    for nm2, a in (('back', (tx0 + 0.325, tx0 + 0.33, ty0, ty1)), ('left', (tx0, tx0 + 0.33, ty1 - 0.004, ty1)), ('right', (tx0, tx0 + 0.33, ty0, ty0 + 0.004))):
        box(f'Tray {k} {nm2}', a[0], a[1], a[2], a[3], zb, zb + 0.055, ACR, parent=bc)
    for s_ in (ty0 + 0.002, ty1 - 0.006):
        box(f'Tray {k} foot {s_:.2f}', tx0 + 0.01, tx0 + 0.02, s_, s_ + 0.004, zb - 0.004 if k else zb - 0.004, zb, M['steel'], parent=bc)
    nst = (8, 5, 14)[k]
    for j in range(nst):
        o = box(f'Tray {k} paper {j}', -0.105, 0.105, -0.148, 0.148, 0, 0.0012, PAPER, parent=bc)
        o.location = (tx0 + 0.15 - (0.035 if (k == 1 and j == nst - 1) else 0.0) + random.uniform(-0.006, 0.006), (ty0 + ty1) / 2 + random.uniform(-0.006, 0.006), zb + 0.005 + j * 0.0016)
        o.rotation_euler = (0, 0, math.radians(90 + random.uniform(-3, 3)))

# --- objects modelled from the frontal photo: every face takes the photo by its (y, z) like the books, so the front is the photo
def photo_uv(o):
    me = o.data; uvl = me.uv_layers.active or me.uv_layers.new(); mw = o.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = ((YF_ - co.y) / bw_, co.z / 1.83)
    me.materials.clear(); me.materials.append(FRONT)
    return o
ZC_ = lambda row: 1.83 - row / PPM; YC_ = lambda col: YF_ - col / PPM
s1, s3 = SHELVES['s1'], SHELVES['s3']
# American football: pointed prolate leather ball (long axis toward the room), pebbled leather, four seams, white laces
LEATHER = mat('Football leather', img='leather.jpg', rough=0.55)
fbc = Vector((bx0_ + 0.14, YC_(80), s1 + 0.0645))
bm = bmesh.new(); uvl = bm.loops.layers.uv.verify(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=28, radius=1.0, calc_uvs=True)
for f in bm.faces:
    for lp in f.loops: lp[uvl].uv = (lp[uvl].uv[0] * 4.0, lp[uvl].uv[1] * 2.0)
FBP = lambda t, a: fbc + Vector((t * 0.112, 0.070 * (max(0.0, 1 - t * t) ** 0.78) * math.cos(a), 0.0645 * (max(0.0, 1 - t * t) ** 0.78) * math.sin(a)))
for v in bm.verts:
    t = max(-1.0, min(1.0, v.co.x)); rr = math.sqrt(max(1e-6, 1 - t * t)); k = (max(0.0, 1 - t * t) ** 0.78) / rr
    v.co = fbc + Vector((t * 0.112, v.co.y * k * 0.070, v.co.z * k * 0.0645))
obj_from_bm('Football', bm, LEATHER, parent=bc)
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    tube(f'Football seam {k}', [FBP(t, a)[:] for t in [i / 20 - 1 for i in range(1, 40)]], 0.0009, mat('Seam dark', (70, 34, 18), rough=0.8) if k == 0 else bpy.data.materials['Seam dark'], seg=5, parent=bc)
lace_a = math.pi / 4 + 0.02
for k in range(7):
    t = -0.27 + k * 0.09
    p0 = FBP(t, lace_a - 0.10); p1 = FBP(t, lace_a + 0.10); nrm = (FBP(t, lace_a) - fbc).normalized()
    tube(f'Football stitch {k}', [(p0 + nrm * 0.001)[:], (FBP(t, lace_a) + nrm * 0.0025)[:], (p1 + nrm * 0.001)[:]], 0.0016, M['white_plastic'], seg=5, parent=bc)
# Cappadocia souvenir: rock-house base and the striped hot-air balloon (and the small one at its side)
photo_uv(rbox('Cappadocia houses', bx0_ + 0.04, bx0_ + 0.09, YC_(50), YC_(27), s1, ZC_(112), FRONT, r=0.008, parent=bc,
              deform=lambda v: Vector((v.x, v.y, v.z + 0.006 * math.sin(v.y * 140) * (1 if v.z > s1 + 0.05 else 0)))))
photo_uv(sphere('Hot-air balloon', (bx0_ + 0.065, YC_(39), ZC_(104)), 1.0, FRONT, parent=bc, scale=(0.026, 0.028, 0.031)))
photo_uv(sphere('Small balloon', (bx0_ + 0.05, YC_(28.5), ZC_(123)), 1.0, FRONT, parent=bc, scale=(0.009, 0.009, 0.011)))
# gift box (red, blue lid) with the small black figurine on it, and the onyx apple in front
GREDM = mat('Gift box red', (150, 30, 36), rough=0.5); GBLUE = mat('Gift box blue', (40, 60, 150), rough=0.5)
rbox('Gift box', bx0_ + 0.07, bx0_ + 0.12, YC_(123), YC_(104), s1, ZC_(118) - 0.01, GREDM, r=0.002, parent=bc)
rbox('Gift box lid', bx0_ + 0.067, bx0_ + 0.123, YC_(124), YC_(103), ZC_(118) - 0.01, ZC_(118), GBLUE, r=0.002, parent=bc)
FIGM = mat('Black figurine', (20, 20, 22), rough=0.3)
rbox('Black figurine', bx0_ + 0.08, bx0_ + 0.11, YC_(123), YC_(107), ZC_(118), ZC_(103), FIGM, r=0.006, seg=3, parent=bc,
     deform=lambda v: Vector((v.x, v.y, v.z + 0.004 * math.sin((v.y - YC_(115)) * 400))))
photo_uv(sphere('Onyx apple', (bx0_ + 0.055, YC_(124), ZC_(133.5)), 1.0, FRONT, parent=bc, scale=(0.026, 0.0265, 0.025)))
# the mechanical-gears ornament in front of the leaning books: grey metal gears on two bars, on a small base
GEARM = mat('Gear metal', (118, 118, 122), rough=0.35, metal=0.85)
def gear(name, c, r, teeth, th=0.004):
    bm = bmesh.new(); n = teeth * 4; F = []; B = []
    for k in range(n):
        a = 2 * math.pi * k / n; rr = r if (k % 4) in (1, 2) else r * 0.86
        F.append(bm.verts.new((c[0] - th / 2, c[1] + rr * math.cos(a), c[2] + rr * math.sin(a))))
        B.append(bm.verts.new((c[0] + th / 2, c[1] + rr * math.cos(a), c[2] + rr * math.sin(a))))
    bm.faces.new(F[::-1]); bm.faces.new(B)
    for k in range(n): bm.faces.new((F[k], F[(k + 1) % n], B[(k + 1) % n], B[k]))
    o = obj_from_bm(name, bm, GEARM, parent=bc)
    cyl(name + ' hub', (c[0] - 0.006, c[1], c[2]), (c[0] + 0.006, c[1], c[2]), r * 0.22, GEARM, parent=bc)
    return o
gx_ = bx0_ + 0.035
for k, (col, row, r, n_) in enumerate(((236, 124, 0.022, 14), (256, 128, 0.018, 12), (272, 122, 0.024, 16), (288, 127, 0.017, 11))):
    gear(f'Gear {k}', (gx_ + (0.006 if k % 2 else 0.0), YC_(col), ZC_(row)), r, n_)
tube('Gear frame low', [(gx_ + 0.008, YC_(228), s1 + 0.012), (gx_ + 0.008, YC_(296), s1 + 0.012)], 0.003, GEARM, parent=bc)
tube('Gear frame high', [(gx_ + 0.008, YC_(228), s1 + 0.042), (gx_ + 0.008, YC_(296), s1 + 0.046)], 0.003, GEARM, parent=bc)
box('Gear base', gx_ - 0.01, gx_ + 0.03, YC_(298), YC_(226), s1, s1 + 0.006, GEARM, parent=bc)
# the marbled pen lying at the foot of the leaning books
MARB = mat('Marbled pen', (40, 42, 46), rough=0.25)
cyl('Marbled pen', (bx0_ + 0.045, YC_(148), s1 + 0.0065), (bx0_ + 0.045, YC_(201), s1 + 0.0065), 0.0065, MARB, parent=bc)
# desk name set: black marble base, clear plate holder with the card (photo), two silver pens in their sockets
NBASE = mat('Black marble', (22, 22, 24), rough=0.2)
rbox('Name set base', bx0_ + 0.02, bx0_ + 0.09, YC_(306), YC_(229), s3, s3 + 0.022, NBASE, r=0.012, seg=4, parent=bc)
photo_uv(box('Name set card', bx0_ + 0.045, bx0_ + 0.05, YC_(292), YC_(244), s3 + 0.022, ZC_(395), FRONT, parent=bc))
box('Name set holder', bx0_ + 0.043, bx0_ + 0.058, YC_(293), YC_(243), s3 + 0.020, ZC_(392), ACR, parent=bc)
for col, lean in ((234, 0.025), (300, -0.012)):
    yp = YC_(col)
    cyl(f'Pen socket {col}', (bx0_ + 0.05, yp, s3 + 0.02), (bx0_ + 0.05, yp, s3 + 0.035), 0.008, M['chrome'], parent=bc)
    tube(f'Desk set pen {col}', [(bx0_ + 0.05, yp, s3 + 0.03), (bx0_ + 0.06, yp + lean, s3 + 0.165)], 0.0042, M['chrome'], parent=bc)

# =============================================================== visitor chairs (ISO): thick cushions, ribbed back connectors, black oval tube frame
CHAIR = mat('Chair fabric black', img='chair_fabric.jpg', rough=0.95)
def ribbed(name, p0, p1, r, n, m, parent):
    p0, p1 = Vector(p0), Vector(p1)
    for i in range(n):
        a = p0 + (p1 - p0) * (i / n); b = p0 + (p1 - p0) * ((i + 0.62) / n)
        cyl(f'{name} rib {i}', a, b, r, m, seg=12, parent=parent)
    cyl(f'{name} core', p0, p1, r * 0.8, m, seg=12, parent=parent)
def iso_chair(name, cx, cy, face, m):
    e = empty(name, (cx, cy, 0), (0, 0, 0 if face > 0 else math.pi))
    def seat_def(v):
        fy = 1 + 0.07 * (v.x + 0.20) / 0.43                      # a little wider at the front
        dome = 0.012 * max(0.0, 1 - (v.y / 0.24) ** 2) * max(0.0, 1 - ((v.x - 0.02) / 0.25) ** 2) if v.z > 0.45 else 0
        return Vector((v.x, v.y * fy, v.z + dome))
    rbox(name + ' seat', -0.205, 0.235, -0.225, 0.225, 0.40, 0.472, m, r=0.034, seg=5, parent=e, deform=seat_def)
    rbox(name + ' seat shell', -0.185, 0.215, -0.205, 0.205, 0.385, 0.402, M['fabric'], r=0.008, parent=e)
    bend = lambda v: Vector((v.x + 0.32 * (v.y ** 2), v.y, v.z))
    b = rbox(name + ' back', -0.026, 0.026, -0.222, 0.222, 0.0, 0.265, m, r=0.032, seg=5, parent=e, deform=bend)
    b.location = (-0.262, 0, 0.585); b.rotation_euler = (0, math.radians(-9), 0)
    for sy in (-0.185, 0.185):
        ribbed(f'{name} bellows {sy}', (-0.165, sy, 0.44), (-0.255, sy, 0.62), 0.017, 9, M['fabric'], e)
        tube(name + ' leg front', [(0.215, sy * 1.12, 0.012), (0.205, sy * 1.12, 0.20), (0.195, sy * 1.12, 0.395)], 0.0105, M['steel'], parent=e)
        tube(name + ' leg rear', [(-0.27, sy * 1.12, 0.012), (-0.225, sy * 1.12, 0.20), (-0.175, sy * 1.12, 0.395)], 0.0105, M['steel'], parent=e)
        tube(name + ' rail', [(0.195, sy * 1.12, 0.395), (-0.175, sy * 1.12, 0.395)], 0.0095, M['steel'], parent=e)
        for xg in (0.215, -0.27):
            cyl(name + ' glide', (xg, sy * 1.12, 0), (xg, sy * 1.12, 0.014), 0.012, M['fabric'], parent=e)
    tube(name + ' cross rear', [(-0.17, -0.207, 0.39), (-0.17, 0.207, 0.39)], 0.008, M['steel'], parent=e)
    tube(name + ' cross front', [(0.17, -0.207, 0.39), (0.17, 0.207, 0.39)], 0.008, M['steel'], parent=e)
    return e
for i, y in enumerate((1.88, 2.40, 2.93)):   # first chair clears the desk front (y 1.60)
    iso_chair(f'Chair left {i + 1}', 0.42, y, 1, CHAIR)
for i, y in enumerate((1.98, 2.53, 3.08)):
    iso_chair(f'Chair right {i + 1}', W - 0.34, y, -1, CHAIR)

# =============================================================== office chair with the jacket over its back
oc = empty('Office chair', (0.98, 0.52, 0), (0, 0, math.radians(8)))
for k5 in range(5):
    a = 2 * math.pi * k5 / 5 + 0.3
    ex, ey = 0.31 * math.cos(a), 0.31 * math.sin(a)
    tube(f'Office chair leg {k5}', [(0, 0, 0.10), (ex * 0.6, ey * 0.6, 0.085), (ex, ey, 0.07)], 0.020, M['steel'], parent=oc)
    for s_ in (-1, 1):
        cyl(f'Office chair caster {k5}{s_}', (ex - s_ * 0.012 * math.sin(a), ey + s_ * 0.012 * math.cos(a), 0.028),
            (ex - s_ * 0.030 * math.sin(a), ey + s_ * 0.030 * math.cos(a), 0.028), 0.028, M['steel'], parent=oc)
    cyl(f'Office chair caster stem {k5}', (ex, ey, 0.05), (ex, ey, 0.075), 0.008, M['chrome'], parent=oc)
cyl('Office chair hub', (0, 0, 0.06), (0, 0, 0.13), 0.045, M['steel'], parent=oc)
cyl('Office chair gas lift', (0, 0, 0.13), (0, 0, 0.40), 0.026, M['steel'], parent=oc)
box('Office chair mechanism', -0.10, 0.10, -0.12, 0.12, 0.40, 0.44, M['steel'], parent=oc)
rbox('Office chair seat', -0.25, 0.25, -0.25, 0.25, 0.44, 0.52, M['fabric'], r=0.035, parent=oc,
     deform=lambda v: Vector((v.x, v.y, v.z - 0.015 * (v.x / 0.25) ** 2)))
tube('Office chair back spine', [(0, -0.20, 0.43), (0, -0.30, 0.47), (0, -0.30, 0.62)], 0.02, M['steel'], parent=oc)
back_bend = lambda v: Vector((v.x, v.y - 0.10 * (v.x ** 2) / 0.06, v.z))
rbox('Office chair back', -0.235, 0.235, -0.33, -0.27, 0.58, 1.13, M['fabric'], r=0.04, parent=oc, deform=back_bend)
for s_ in (-1, 1):
    tube(f'Office chair arm {s_}', [(s_ * 0.24, -0.16, 0.44), (s_ * 0.27, -0.16, 0.50), (s_ * 0.27, -0.10, 0.66), (s_ * 0.27, 0.12, 0.66)], 0.016, M['steel'], parent=oc)
    rbox(f'Office chair arm pad {s_}', s_ * 0.27 - 0.035, s_ * 0.27 + 0.035, -0.13, 0.14, 0.655, 0.685, M['grey_plastic'], r=0.01, parent=oc)
# jacket: a draped shell over the backrest (shoulders on top, hanging down both faces) with folds
random.seed(3)
JACKET = mat('Jacket wool', (22, 22, 24), rough=0.9)
def jacket_deform(v):
    fold = 0.008 * math.sin(v.x * 38) + 0.004 * math.sin(v.x * 91 + 1.3)
    hang = max(0.0, 1.0 - (v.z - 0.55) / 0.6)
    return Vector((v.x * (1 + 0.06 * hang), v.y + fold * (0.4 + hang) - 0.10 * (v.x ** 2) / 0.06, v.z))
rbox('Jacket', -0.255, 0.255, -0.355, -0.245, 0.50, 1.16, JACKET, r=0.05, seg=4, parent=oc, deform=jacket_deform)
for s_ in (-1, 1):
    tube(f'Jacket sleeve {s_}', [(s_ * 0.25, -0.33, 1.05), (s_ * 0.28, -0.36, 0.80), (s_ * 0.27, -0.38, 0.55)], 0.045, JACKET, parent=oc)

# =============================================================== flower tricycle with the clock as its front wheel
random.seed(7)
fc = empty('Flower cart', (1.30, 2.00, 0.42), (0, 0, math.radians(8)))
WIRE = M['steel']
# clock wheel: black drum, dial on both faces, chrome bezel, bells-style top loop
cyl('Clock drum', (-0.038, 0.13, 0.072), (0.038, 0.13, 0.072), 0.068, WIRE, parent=fc)
CF = mat('Clock dial', img='clockface.png', rough=0.3)
for s_ in (-1, 1):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    ctr = bm.verts.new((s_ * 0.0395, 0.13, 0.072)); ring = []
    for k in range(32):
        a = 2 * math.pi * k / 32; ring.append(bm.verts.new((s_ * 0.0395, 0.13 + 0.056 * math.cos(a), 0.072 + 0.056 * math.sin(a))))
    for k in range(32):
        f = bm.faces.new((ctr, ring[k], ring[(k + 1) % 32]) if s_ > 0 else (ctr, ring[(k + 1) % 32], ring[k]))
        for lp in f.loops:
            co = lp.vert.co; lp[uvl].uv = (0.5 + s_ * (co.y - 0.13) / 0.112 * -1, 0.5 + (co.z - 0.072) / 0.112)
    obj_from_bm(f'Clock dial {s_}', bm, CF, parent=fc)
    tube(f'Clock bezel {s_}', arc((s_ * 0.040, 0.13, 0.072), 0.058, 0, 2 * math.pi, 40, 'yz'), 0.004, M['chrome'], parent=fc, closed=True)
# rear scroll wheels
for s_ in (-1, 1):
    c = (s_ * 0.055, -0.11, 0.045)
    tube(f'Rear wheel rim {s_}', arc(c, 0.043, 0, 2 * math.pi, 28, 'yz'), 0.0025, WIRE, parent=fc, closed=True)
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        pts = [(c[0], c[1] + 0.004 * math.cos(a), c[2] + 0.004 * math.sin(a))]
        for q in range(1, 9):
            rr = 0.006 + 0.036 * q / 8; aa = a + 0.55 * math.sin(q / 8 * math.pi)
            pts.append((c[0], c[1] + rr * math.cos(aa), c[2] + rr * math.sin(aa)))
        tube(f'Rear wheel scroll {s_}{k}', pts, 0.0018, WIRE, seg=6, parent=fc)
tube('Rear axle', [(-0.06, -0.11, 0.045), (0.06, -0.11, 0.045)], 0.0025, WIRE, parent=fc)
# basket: oval wire bowl over the rear axle, frame to the clock fork, handlebar
for zz, scl in ((0.07, 0.7), (0.10, 0.95), (0.135, 1.0)):
    tube(f'Basket ring {zz}', [(0.062 * scl * math.cos(a), -0.03 + 0.10 * scl * math.sin(a), zz) for a in [2 * math.pi * k / 30 for k in range(30)]], 0.0022, WIRE, parent=fc, closed=True)
for k in range(10):
    a = 2 * math.pi * k / 10
    tube(f'Basket rib {k}', [(0.043 * math.cos(a), -0.03 + 0.07 * math.sin(a), 0.07), (0.059 * math.cos(a), -0.03 + 0.095 * math.sin(a), 0.10),
                             (0.062 * math.cos(a), -0.03 + 0.10 * math.sin(a), 0.135)], 0.0018, WIRE, seg=6, parent=fc)
tube('Cart frame', [(0, -0.11, 0.045), (0, -0.03, 0.065), (0, 0.07, 0.09), (0, 0.13, 0.15)], 0.003, WIRE, parent=fc)
for s_ in (-1, 1):
    tube(f'Fork {s_}', [(s_ * 0.045, 0.13, 0.072), (s_ * 0.045, 0.13, 0.15), (0, 0.13, 0.17)], 0.003, WIRE, parent=fc)
tube('Handlebar stem', [(0, 0.13, 0.15), (0, 0.12, 0.26)], 0.003, WIRE, parent=fc)
tube('Handlebar', [(-0.06, 0.10, 0.27), (-0.03, 0.12, 0.26), (0, 0.12, 0.26), (0.03, 0.12, 0.26), (0.06, 0.10, 0.27)], 0.003, WIRE, parent=fc)
# flowers: red petunias (5-lobed trumpets), white and yellow daisies, leaves
RED = mat('Petunia red', (190, 25, 55), rough=0.6); WHT = mat('Daisy white', (246, 245, 238), rough=0.7)
YEL = mat('Daisy yellow', (238, 196, 30), rough=0.7); CEN = mat('Flower centre', (90, 60, 20), rough=0.8)
LEAF = mat('Leaf green', (52, 92, 46), rough=0.6); STEM = mat('Stem green', (70, 110, 50), rough=0.6)
def orient(dirv):
    return Vector(dirv).normalized().to_track_quat('Z', 'Y').to_matrix()
def petunia(name, pos, dirv, r=0.022):
    bm = bmesh.new(); n = 20; rings = []
    for j, (rad, h) in enumerate(((0.002, 0.0), (0.008, 0.012), (r, 0.018))):
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n; lob = 1 + (0.18 * math.cos(5 * a) if j == 2 else 0)
            ring.append(bm.verts.new((rad * lob * math.cos(a), rad * lob * math.sin(a), h)))
        rings.append(ring)
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for k in range(n): bm.faces.new((a_[k], a_[(k + 1) % n], b_[(k + 1) % n], b_[k]))
    M3 = orient(dirv).to_4x4(); bmesh.ops.transform(bm, matrix=Matrix.Translation(pos) @ M3, verts=bm.verts)
    return obj_from_bm(name, bm, RED, parent=fc)
def daisy(name, pos, dirv, petal_m, r=0.02, npet=16):
    bm = bmesh.new()
    for k in range(npet):
        a = 2 * math.pi * k / npet; ca, sa = math.cos(a), math.sin(a)
        w = 0.0035
        P = [(0.004 * ca - w * sa, 0.004 * sa + w * ca, 0.002), (r * ca - w * 0.6 * sa, r * sa + w * 0.6 * ca, -0.002),
             (r * ca + w * 0.6 * sa, r * sa - w * 0.6 * ca, -0.002), (0.004 * ca + w * sa, 0.004 * sa - w * ca, 0.002)]
        bm.faces.new([bm.verts.new(p) for p in P])
    M3 = orient(dirv).to_4x4(); bmesh.ops.transform(bm, matrix=Matrix.Translation(pos) @ M3, verts=bm.verts)
    o = obj_from_bm(name, bm, petal_m, parent=fc)
    sphere(name + ' centre', Vector(pos) + Vector(dirv).normalized() * 0.002, 0.006 if petal_m == WHT else 0.005, YEL if petal_m == WHT else CEN, parent=fc, scale=(1, 1, 0.6))
    return o
def leaf(name, pos, dirv, ln=0.05):
    d_ = Vector(dirv).normalized(); side = d_.cross(Vector((0, 0, 1))).normalized() * 0.012
    p0 = Vector(pos); P = [p0, p0 + d_ * ln * 0.5 + side, p0 + d_ * ln, p0 + d_ * ln * 0.5 - side]
    bm = bmesh.new(); bm.faces.new([bm.verts.new(p) for p in P]); return obj_from_bm(name, bm, LEAF, parent=fc)
for k in range(26):       # red petunias: front and both sides of the basket
    a = random.uniform(0, 2 * math.pi); rr = random.uniform(0.04, 0.085)
    pos = (rr * math.cos(a) * 0.9, -0.03 + rr * math.sin(a) * 1.25, 0.14 + random.uniform(0, 0.08))
    out_ = Vector((pos[0], pos[1] + 0.03, 0.06 + random.uniform(0, 0.08)))
    petunia(f'Petunia {k}', pos, out_)
for k in range(22):       # white daisies: the -x / rear side
    pos = (random.uniform(-0.09, -0.01), random.uniform(-0.13, 0.03), 0.17 + random.uniform(0, 0.07))
    daisy(f'White daisy {k}', pos, (pos[0] - 0.02, pos[1] + 0.03, 0.10), WHT, 0.016)
for k in range(14):       # yellow daisies on long stems above
    base = (random.uniform(-0.03, 0.05), random.uniform(-0.08, 0.04), 0.16)
    top = (base[0] + random.uniform(-0.05, 0.05), base[1] + random.uniform(-0.06, 0.06), 0.24 + random.uniform(0, 0.09))
    tube(f'Stem {k}', [base, top], 0.0015, STEM, seg=5, parent=fc)
    daisy(f'Yellow daisy {k}', top, (top[0] - base[0], top[1] - base[1], 0.12), YEL, 0.015, 12)
for k in range(24):
    a = random.uniform(0, 2 * math.pi)
    p = (0.05 * math.cos(a), -0.03 + 0.08 * math.sin(a), 0.15 + random.uniform(0, 0.05))
    leaf(f'Leaf {k}', p, (math.cos(a), math.sin(a), random.uniform(0.0, 0.8)))

# =============================================================== desk items
dz = 0.745
# laptop: MacBook Air M2 (midnight), 304 x 215 x 11.3 mm, open toward the door as in the window photos
MID = mat('MacBook midnight', (46, 50, 60), rough=0.32, metal=0.6)
KB = mat('MacBook keyboard', img='mac_keyboard.png', rough=0.5)
SCR = mat('MacBook screen', (10, 12, 16), rough=0.08, emit=(30, 40, 60), emit_strength=0.35)
BEZ = mat('MacBook bezel', (6, 6, 7), rough=0.15)
lap = empty('Laptop', (0.48, 0.43, dz), (0, 0, math.radians(185)))
rbox('Laptop base', -0.152, 0.152, -0.1075, 0.1075, 0, 0.0113, MID, r=0.004, seg=3, parent=lap)
quad('Laptop keyboard', [(-0.137, -0.006, 0.0114), (0.137, -0.006, 0.0114), (0.137, 0.094, 0.0114), (-0.137, 0.094, 0.0114)], KB,
     uv=((0, 0), (1, 0), (1, 1), (0, 1)), parent=lap)
box('Laptop trackpad', -0.0775, 0.0775, -0.100, -0.016, 0.0113, 0.01135, mat('MacBook trackpad', (52, 56, 66), rough=0.25, metal=0.4), parent=lap)
lid = empty('Laptop lid hinge', (0, 0.1065, 0.0113), (math.radians(-24), 0, 0), parent=lap)
rbox('Laptop lid', -0.152, 0.152, -0.0045, 0.0, 0, 0.212, MID, r=0.003, seg=3, parent=lid)
quad('Laptop bezel', [(-0.150, -0.0047, 0.003), (0.150, -0.0047, 0.003), (0.150, -0.0047, 0.209), (-0.150, -0.0047, 0.209)], BEZ, parent=lid)
quad('Laptop screen', [(-0.144, -0.0049, 0.009), (0.144, -0.0049, 0.009), (0.144, -0.0049, 0.198), (-0.144, -0.0049, 0.198)], SCR, parent=lid)
tube('Laptop cable', [(0.155, 0.02, 0.006), (0.20, 0.05, 0.002), (0.32, 0.12, 0.002), (0.42, 0.24, 0.002)], 0.0022, M['fabric'], seg=6, parent=lap)
box('Laptop notch', -0.016, 0.016, -0.0052, -0.0049, 0.198, 0.206, BEZ, parent=lid)

# mug (white, lathe with a handle)
mug = empty('Mug', (0.19, 0.63, dz))
cyl('Mug body', (0, 0, 0), (0, 0, 0.095), 0.041, M['mug'], seg=28, parent=mug)
cyl('Mug inside', (0, 0, 0.088), (0, 0, 0.0952), 0.037, M['fabric'], seg=28, parent=mug)
tube('Mug handle', arc((0.045, 0, 0.05), 0.026, -math.pi / 2, math.pi / 2, 12, 'xz'), 0.006, M['mug'], parent=mug)
# desk phone (Panasonic KX-TS500 type, from the window photos): low warm-grey wedge, handset lying across the back,
# 4 x 3 black keypad front-right, two small keys at the left, coiled cord to the left, line cord at the back
PHM = mat('Telephone grey', (162, 157, 145), rough=0.42)
PHD = mat('Telephone grey dark', (128, 124, 116), rough=0.5)
ph = empty('Desk phone', (0.26, 1.31, dz), (0, 0, math.radians(172)))
TB = 0.070
slope = lambda y: 0.45 + 0.55 * (y + 0.095) / 0.19
rbox('Phone body', -0.115, 0.115, -0.095, 0.095, 0.006, TB, PHM, r=0.012, seg=4, parent=ph,
     deform=lambda v: Vector((v.x, v.y, 0.006 + (v.z - 0.006) * slope(v.y))))
rbox('Phone base plinth', -0.100, 0.100, -0.090, 0.090, 0.0, 0.008, PHD, r=0.004, parent=ph)
rbox('Phone cradle step', 0.055, 0.105, 0.015, 0.090, TB * slope(0.05) - 0.01, TB * slope(0.05) + 0.010, PHM, r=0.008, parent=ph)
zt = TB * slope(0.055)
hs = [(-0.105, 0.052, zt + 0.004), (-0.08, 0.052, zt + 0.010), (-0.04, 0.052, zt + 0.015), (0.0, 0.052, zt + 0.016), (0.04, 0.052, zt + 0.015), (0.08, 0.052, zt + 0.010), (0.105, 0.052, zt + 0.004)]
hg = tube('Phone handset grip', hs, 0.012, PHM, seg=16, parent=ph)
for v in hg.data.vertices: v.co.y = 0.052 + (v.co.y - 0.052) * 1.45
for s_ in (-1, 1):
    rbox(f'Phone handset end {s_}', s_ * 0.092 - 0.024, s_ * 0.092 + 0.024, 0.026, 0.078, zt - 0.006, zt + 0.012, PHM, r=0.010, seg=4, parent=ph)
KEYM = mat('Phone keys black', (18, 18, 20), rough=0.35)
for r_ in range(4):
    for c_ in range(3):
        yk = -0.072 + r_ * 0.017; xk = 0.012 + c_ * 0.024; zk = 0.006 + (TB - 0.006) * slope(yk)
        rbox(f'Phone key {r_}{c_}', xk - 0.0085, xk + 0.0085, yk - 0.0058, yk + 0.0058, zk - 0.001, zk + 0.0045, KEYM, r=0.002, seg=2, parent=ph)
for k_, xk in enumerate((-0.052, -0.030)):
    yk = -0.080; zk = 0.006 + (TB - 0.006) * slope(yk)
    rbox(f'Phone small key {k_}', xk - 0.008, xk + 0.008, yk - 0.003, yk + 0.003, zk - 0.001, zk + 0.003, KEYM, r=0.0015, seg=2, parent=ph)
yk = -0.025; zk = 0.006 + (TB - 0.006) * slope(yk)
box('Phone label window', -0.078, -0.018, -0.040, -0.012, zk - 0.001, zk + 0.0005, PHD, parent=ph)
coil = [(-0.112 - 0.06 * k / 360 + 0.007 * math.cos(k * 0.5), 0.05 - 0.11 * k / 360 + 0.007 * math.sin(k * 0.5), max(0.006, 0.05 - 0.05 * k / 120) + 0.006 * math.sin(k * 0.25)) for k in range(361)]
tube('Phone coiled cord', coil, 0.0022, PHM, seg=6, parent=ph)
tube('Phone line cord', [(0.09, 0.095, 0.01), (0.12, 0.16, 0.003), (0.25, 0.30, 0.003)], 0.0022, PHM, seg=6, parent=ph)

# phone stand (folding black), spray bottle, mesh pencil cup with pens, kettle on the floor
STM = mat('Stand aluminium', (180, 182, 186), rough=0.3, metal=1.0)
stc = (0.30, 1.13, dz)
box('Phone stand base', stc[0] - 0.035, stc[0] + 0.035, stc[1] - 0.06, stc[1] + 0.02, dz, dz + 0.004, STM)
for sx in (-0.03, 0.03):
    tube(f'Phone stand arm {sx}', [(stc[0] + sx, stc[1] - 0.05, dz + 0.004), (stc[0] + sx, stc[1] + 0.005, dz + 0.075)], 0.003, STM)
box('Phone stand rest', stc[0] - 0.035, stc[0] + 0.035, stc[1] + 0.0, stc[1] + 0.012, dz + 0.068, dz + 0.082, STM)
BOT = mat('Bottle plastic', (232, 236, 238), rough=0.15)
BOT.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 0.85
cyl('Spray bottle', (1.86, 1.30, 0.60), (1.86, 1.30, 0.72), 0.022, BOT, seg=24)
cyl('Spray bottle shoulder', (1.86, 1.30, 0.72), (1.86, 1.30, 0.745), 0.012, BOT, seg=24)
cyl('Spray label', (1.86, 1.30, 0.62), (1.86, 1.30, 0.70), 0.0225, M['white_plastic'], seg=24)
cyl('Spray head', (1.86, 1.30, 0.745), (1.86, 1.30, 0.785), 0.011, M['fabric'])
box('Spray nozzle', 1.84, 1.86, 1.295, 1.305, 0.77, 0.782, M['fabric'])
pc = empty('Pencil cup', (1.70, 1.50, 0.60))
for k in range(16):
    a = 2 * math.pi * k / 16
    tube(f'Pencil cup mesh {k}', [(0.035 * math.cos(a), 0.035 * math.sin(a), 0), (0.040 * math.cos(a + 0.3), 0.040 * math.sin(a + 0.3), 0.10)], 0.0012, M['steel'], seg=4, parent=pc)
for zz in (0.003, 0.05, 0.098):
    tube(f'Pencil cup ring {zz}', arc((0, 0, zz), 0.035 + 0.05 * zz, 0, 2 * math.pi, 24, 'xy'), 0.0015, M['steel'], seg=4, parent=pc, closed=True)
cyl('Pencil cup base', (0, 0, 0), (0, 0, 0.003), 0.035, M['steel'], parent=pc)
for k, (dx_, dy_, ang, mm) in enumerate(((0.01, 0.0, 12, 'fabric'), (-0.012, 0.008, -8, 'red'), (0.0, -0.012, 5, 'steel'), (0.015, 0.012, 15, 'fabric'))):
    tube(f'Pen {k}', [(dx_, dy_, 0.004), (dx_ + 0.14 * math.sin(math.radians(ang)), dy_, 0.14)], 0.004, M[mm], seg=8, parent=pc)
kt = empty('Kettle', (1.98, 0.72, 0))
cyl('Kettle base', (0, 0, 0), (0, 0, 0.02), 0.085, M['steel'], parent=kt)
cyl('Kettle body', (0, 0, 0.02), (0, 0, 0.22), 0.075, M['chrome'], seg=28, parent=kt)
cyl('Kettle band', (0, 0, 0.16), (0, 0, 0.22), 0.077, M['steel'], seg=28, parent=kt)
cyl('Kettle lid', (0, 0, 0.22), (0, 0, 0.235), 0.06, M['steel'], parent=kt)
tube('Kettle handle', [(0.07, 0, 0.06), (0.10, 0, 0.09), (0.10, 0, 0.18), (0.07, 0, 0.215)], 0.012, M['steel'], parent=kt)

# =============================================================== printer: Canon i-SENSYS MF724Cdw from the three close-up photos
PX, PY, PZ, PW, PD = 2.06, 0.08, 0.50, 0.43, 0.484          # front plane x, side y0, cabinet top z, width (y), depth (x)
PWH = mat('Printer white', (226, 226, 222), rough=0.4)
def pmat(name, f): return mat(name, img=f, rough=0.4)
def pbox(name, x0, x1, y0, y1, z0, z1, faces):
    """box in printer coordinates (x from the front face backwards); faces: {'front': (mat, z0, z1), 'side': (mat, x0, x1, z0, z1)}
    the textured faces take the photo by planar mapping in the given extents."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    X = lambda x: PX + x; Y = lambda y: PY + y; Z = lambda z: PZ + z
    V = [bm.verts.new((X(a), Y(b), Z(c))) for a, b, c in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    mats = [PWH]; F = {'front': (0, 3, 7, 4), 'side': (2, 3, 7, 6)}
    for key, idx in (('bottom', (0, 3, 2, 1)), ('top', (4, 5, 6, 7)), ('y0', (0, 1, 5, 4)), ('back', (1, 2, 6, 5)), ('side', (2, 3, 7, 6)), ('front', (3, 0, 4, 7))):
        f = bm.faces.new([V[i_] for i_ in idx]); mi = 0
        if key in faces:
            spec = faces[key]
            if spec[0] not in mats: mats.append(spec[0])
            mi = mats.index(spec[0])
            for lp in f.loops:
                co = lp.vert.co; lx, ly, lz = co.x - PX, co.y - PY, co.z - PZ
                if key == 'front': lp[uvl].uv = ((PW - ly) / PW, (lz - spec[1]) / (spec[2] - spec[1]))
                else: lp[uvl].uv = ((spec[2] - lx) / (spec[2] - spec[1]), (lz - spec[3]) / (spec[4] - spec[3]))
        f.material_index = mi
    return obj_from_bm(name, bm, mats)
SIDE_B = pmat('Printer side (photo)', 'pr_side_body.jpg'); SIDE_T = pmat('Printer side top (photo)', 'pr_side_top.jpg')
pbox('Printer base', 0, PD, 0, PW, 0, 0.285, {'front': (pmat('Printer front (photo)', 'pr_front_base.jpg'), 0.0, 0.235), 'side': (SIDE_B, 0, PD, 0, 0.36)})
pbox('Printer upper body', 0.12, PD, 0, PW, 0.285, 0.36, {'front': (pmat('Printer bay (photo)', 'pr_front_bay.jpg'), 0.235, 0.36), 'side': (SIDE_B, 0, PD, 0, 0.36)})
box('Printer bay floor', PX + 0.01, PX + 0.12, PY + 0.02, PY + PW - 0.02, PZ + 0.284, PZ + 0.286, M['fabric'])
pbox('Printer scanner', -0.005, PD - 0.01, -0.004, PW + 0.004, 0.36, 0.395, {'front': (pmat('Printer scanner (photo)', 'pr_front_scan.jpg'), 0.36, 0.395), 'side': (SIDE_T, -0.005, PD - 0.01, 0.36, 0.49)})
pbox('Printer document feeder', 0.03, PD - 0.04, 0.01, PW - 0.01, 0.395, 0.49, {'front': (pmat('Printer feeder (photo)', 'pr_front_adf.jpg'), 0.39, 0.49), 'side': (SIDE_T, -0.005, PD - 0.01, 0.36, 0.49)})
# control panel: slanted slab under the scanner at the front right, photo on its face
PANEL = pmat('Printer panel (photo)', 'pr_panel.jpg')
bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
py0, py1 = 0.04, 0.275
P_ = [(PX - 0.035, PY + py1, PZ + 0.29), (PX - 0.035, PY + py0, PZ + 0.29), (PX + 0.02, PY + py0, PZ + 0.358), (PX + 0.02, PY + py1, PZ + 0.358)]
vs = [bm.verts.new(q) for q in P_]; f = bm.faces.new(vs)
for lp, uvq in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uvq
obj_from_bm('Printer panel face', bm, PANEL)
box('Printer panel body', PX - 0.03, PX + 0.12, PY + py0, PY + py1, PZ + 0.285, PZ + 0.29, PWH)
# laptop bag on top (as in the room photos) with its strap down the door-facing side
rbox('Laptop bag', PX + 0.02, PX + 0.44, PY + 0.02, PY + 0.41, PZ + 0.49, PZ + 0.55, M['fabric'], r=0.022, deform=lambda v: Vector((v.x, v.y, v.z + 0.005 * math.sin(v.y * 30))))
tube('Bag strap', [(PX + 0.30, PY + 0.41, PZ + 0.53), (PX + 0.33, PY + 0.437, PZ + 0.47), (PX + 0.22, PY + 0.437, PZ + 0.25), (PX + 0.06, PY + 0.437, PZ + 0.02),
                   (PX + 0.02, PY + 0.437, PZ - 0.02)], 0.011, M['fabric'], seg=8)

# =============================================================== ceiling fittings: channel, end caps, two tubes
for nm, xc, yc in (('Light door', R['xl'], (R['yl0'] + R['yl1']) / 2), ('Light window', 1.40, 1.15)):
    rbox(nm + ' channel', xc - 0.06, xc + 0.06, yc - 0.63, yc + 0.63, H - 0.045, H, M['white_plastic'], r=0.004)
    for s_ in (-1, 1):
        box(nm + f' cap {s_}', xc - 0.05, xc + 0.05, yc + s_ * 0.63 - 0.015, yc + s_ * 0.63 + 0.015, H - 0.085, H - 0.045, M['white_plastic'])
    for s in (-0.03, 0.03):
        cyl(nm + ' tube', (xc + s, yc - 0.615, H - 0.068), (xc + s, yc + 0.615, H - 0.068), 0.013, M['tube'])
# double socket on the right wall by the chairs
box('Socket', W - 0.012, W, 3.42, 3.56, 0.25, 0.32, M['white_plastic'])

# corridor and room lights for rendering
for k_, xl in enumerate((2.39, 5.8, 9.16, 12.6, 16.0, 19.4)):
    area(f'Corridor lamp {k_}', (xl, 6.63, ZC - 0.08), (0, 0, 0), 1.2, 260, (1, 0.98, 0.94), 'RECTANGLE', 0.15)
for k_ in range(6):   # daylight through the corridor windows
    area(f'Corridor window light {k_}', (6.5 + k_ * 2.6, YF + 0.30, 1.75), (math.radians(90), 0, 0), 2.4, 700, (1, 0.98, 0.95), 'RECTANGLE', 1.4)
area('Glass door daylight', (CX0 + 0.05, 6.9, 1.4), (0, math.radians(-90), 0), 2.0, 600, (1, 0.98, 0.95), 'RECTANGLE', 2.4)

for o in bpy.data.objects:
    if o.type == 'MESH' and len(o.data.polygons) > 24 and not o.name.startswith(('Book ', 'Bookcase', 'Wall', 'Floor', 'Corridor floor', 'Desk ')):
        for poly in o.data.polygons: poly.use_smooth = True
