"""Blender: Tesan desk phone from one photo. Frame: +X front, +Y the phone's left (image right), +Z up; built in mm,
stored in metres. Every face the photo's camera sees (facing it, not hidden behind the handset or a key) takes the
photo itself through the solved camera (per-vertex projected UVs on a mesh cut every few mm); the rest take flat
colours sampled from the photo.
Run: Blender -b -P build.py -- --mode match|final --out DIR [--shots photo,...] [--res 1200] [--blend f] [--glb f]"""
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

A = sys.argv[sys.argv.index("--") + 1:]
arg = lambda k, d=None: A[A.index(k) + 1] if k in A else d
MODE = arg("--mode", "final"); OUT = arg("--out", "render"); RES = int(arg("--res", "1200"))
SHOTS = arg("--shots", "photo").split(",")
HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "cam.json")))
W, D, HF, HB, KH, KD = C["W"], C["D"], C["HF"], C["HB"], C["KH"], C["KD"]
AL = math.atan((HB - HF) / D)
X0, PX, Y0, PY = C["X0"], C["PX"], C["Y0"], C["PY"]
ZF, ZBK, TB = C["ZF"], C["ZBK"], C["T"]          # the band's top at the front / back, its thickness
IW, IH, F = C["IW"], C["IH"], C["f"]
IW2, IH2, F2 = C["IW2"], C["IH2"], C["f2"]
mm = 0.001
def rotm(rv):
    rv = np.array(rv, float); a = np.linalg.norm(rv)
    return np.array((Quaternion(Vector(rv / a), a) if a > 0 else Quaternion()).to_matrix())
RM = rotm(C["rv"]); T = np.array(C["t"]); CAM = np.array(C["cam"])          # front photo camera (OpenCV: x right, y down, z fwd)
RM2 = rotm(C["rv2"]); T2 = np.array(C["t2"]); CAM2 = np.array(C["cam2"])   # side photo camera
HSP = json.load(open(os.path.join(HERE, "handset.json")))                   # the handset's fit (hsfit.py)
def ztop(x): return HF + (D / 2 - x) * (HB - HF) / D
def zband(x): return ZBK + (ZF - ZBK) * (x + D / 2) / D
dvec = np.array([math.cos(AL), 0, -math.sin(AL)])   # along the top, towards the front (descending)
nvec = np.array([math.sin(AL), 0, math.cos(AL)])    # the top's normal
def slope_pt(x, y, w):
    """point at plan x,y on the top plane, raised w (perpendicular)"""
    return np.array([x, y, ztop(x)]) + w * nvec
def proj(P):
    X = RM @ np.asarray(P, float) + T
    return np.array([F * X[0] / X[2] + IW / 2, F * X[1] / X[2] + IH / 2])
def proj2(P):
    X = RM2 @ np.asarray(P, float) + T2
    return np.array([F2 * X[0] / X[2] + IW2 / 2, F2 * X[1] / X[2] + IH2 / 2])

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------- materials ----------
def srgb_to_lin(c): return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c)
PHOTO = bpy.data.images.load(os.path.join(HERE, "ref.jpg"))
PHOTO2 = bpy.data.images.load(os.path.join(HERE, "side_match.jpg"))   # the side photo, gain-matched to the front's beige
if MODE == "pbr":   # real materials: the photos' shading removed, printed matter kept (delight.py)
    PHOTO = bpy.data.images.load(os.path.join(HERE, "ref_albedo.jpg")); PHOTO2 = bpy.data.images.load(os.path.join(HERE, "side_albedo.jpg"))
    PHOTO_KEYS = bpy.data.images.load(os.path.join(HERE, "ref_keys.jpg"))
def mat_photo(name="photo", image=None, rough=0.55):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); t = nt.nodes.new("ShaderNodeTexImage"); t.image = image or PHOTO; t.interpolation = "Cubic"
    if MODE == "match":
        e = nt.nodes.new("ShaderNodeEmission"); nt.links.new(t.outputs[0], e.inputs[0]); nt.links.new(e.outputs[0], out.inputs[0])
    else:
        b = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(t.outputs[0], b.inputs["Base Color"])
        if MODE == "pbr":
            b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = 0.45
        else:
            nt.links.new(t.outputs[0], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 0.25
            b.inputs["Roughness"].default_value = 0.55; b.inputs["Specular IOR Level"].default_value = 0.3
        nt.links.new(b.outputs[0], out.inputs[0])
    return m
def mat_flat(name, srgb, rough=0.55):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); lin = srgb_to_lin(srgb)
    if MODE == "match":
        e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*lin, 1); nt.links.new(e.outputs[0], out.inputs[0])
    else:
        b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.inputs["Base Color"].default_value = (*lin, 1)
        b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = 0.3
        b.inputs["Emission Color"].default_value = (*lin, 1); b.inputs["Emission Strength"].default_value = 0.25 if MODE == "final" else 0
        if MODE == "pbr": b.inputs["Specular IOR Level"].default_value = 0.45
        nt.links.new(b.outputs[0], out.inputs[0])
    return m
M_PHOTO = mat_photo()
M_PHOTO2 = mat_photo("photo_side", PHOTO2)
if MODE == "pbr":
    M_PHOTO_KEYS = mat_photo("photo_keys", PHOTO_KEYS, rough=0.35)
    CREAM = (0.80, 0.76, 0.66)
    M_BODY = mat_flat("body_plastic", CREAM, rough=0.45); M_BODY_SIDE = M_BODY; M_BODY_KEYS = M_BODY
    M_RECESS = mat_flat("recess_plastic", (0.78, 0.74, 0.64), rough=0.5)
    M_BAND = mat_flat("band_dark", (0.10, 0.10, 0.10), rough=0.35)
    M_UNDER = mat_flat("underside", (0.35, 0.34, 0.32), rough=0.8)
    M_KEY = mat_flat("key_black", (0.05, 0.05, 0.05), rough=0.35)
    M_HANDSET = mat_flat("handset_plastic", CREAM, rough=0.45)
    M_CORD = mat_flat("cord_grey", (0.75, 0.74, 0.72), rough=0.6)
else:
    M_PHOTO_KEYS = M_PHOTO
    M_BODY = mat_flat("body_beige", (0.595, 0.564, 0.49))        # the lit top's beige
    M_BODY_SIDE = mat_flat("body_side", (0.536, 0.504, 0.429))   # the front face's shade
    M_RECESS = mat_flat("recess", (0.40, 0.385, 0.345))   # the pocket is in shadow in the photo
    M_BODY_KEYS = mat_flat("body_keypad", (0.47, 0.44, 0.365))
    M_BAND = mat_flat("band_dark", (0.216, 0.19, 0.148), rough=0.4)
    M_UNDER = mat_flat("underside", (0.30, 0.29, 0.27), rough=0.8)
    M_KEY = mat_flat("key_black", (0.10, 0.10, 0.10), rough=0.45)
    M_HANDSET = mat_flat("handset_beige", (0.635, 0.61, 0.53))   # its lit top, so photo and flat faces meet without a step
    M_CORD = mat_flat("cord_grey", (0.62, 0.61, 0.59), rough=0.6)

# ---------- helpers ----------
def rounded_rect(xa, xb, ya, yb, r, n=7):
    pts = []
    for (cx, cy, a0) in [(xb - r, yb - r, 0), (xa + r, yb - r, 90), (xa + r, ya + r, 180), (xb - r, ya + r, 270)]:
        for a in np.linspace(a0, a0 + 90, n, endpoint=False):
            pts.append((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))))
    return pts
def new_obj(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for v in me.vertices: v.co = v.co * mm
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); return o
def bisect_grid(bm, xs=(), ys=(), zs=()):
    for x in xs: bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4, plane_co=(x, 0, 0), plane_no=(1, 0, 0))
    for y in ys: bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4, plane_co=(0, y, 0), plane_no=(0, 1, 0))
    for z in zs: bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4, plane_co=(0, 0, z), plane_no=(0, 0, 1))
def slope_box(name, x0, x1, y0, y1, w0, w1, r_plan, r_top, seg=4, r_bot=0.0):
    """rounded box standing on the sloped top: plan x in [x0,x1], y in [y0,y1], from w0 to w1 perpendicular to it"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0), w0 + (v.co.z + 0.5) * (w1 - w0)))
    vert_e = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6]
    bmesh.ops.bevel(bm, geom=vert_e, offset=r_plan, segments=seg, affect="EDGES", profile=0.5)
    if r_top > 0:
        top_e = [e for e in bm.edges if all(abs(v.co.z - w1) < 1e-6 for v in e.verts)]
        bmesh.ops.bevel(bm, geom=top_e, offset=r_top, segments=2, affect="EDGES", profile=0.5)
    if r_bot > 0:
        bot_e = [e for e in bm.edges if all(abs(v.co.z - w0) < 1e-6 for v in e.verts)]
        bmesh.ops.bevel(bm, geom=bot_e, offset=r_bot, segments=2, affect="EDGES", profile=0.5)
    xc = (x0 + x1) / 2
    for v in bm.verts:                       # local z (perpendicular) -> world: lie on the slope
        x, y, w = v.co
        p = slope_pt(xc, y, w) + (x - xc) * dvec
        v.co = Vector(p)
    return bm

# ---------- body ----------
RC = 10.0
plan = rounded_rect(-D / 2, D / 2, -W / 2, W / 2, RC)
bm = bmesh.new()
vb = [bm.verts.new((x, y, 0.0)) for x, y in plan]
vt = [bm.verts.new((x, y, ztop(x))) for x, y in plan]
n = len(plan)
bm.faces.new(vb[::-1]); bm.faces.new(vt)
for i in range(n):
    bm.faces.new([vb[i], vb[(i + 1) % n], vt[(i + 1) % n], vt[i]])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
top_e = [e for e in bm.edges if all(v.co.z > 1 for v in e.verts) and e.is_boundary is False and all(v in vt for v in e.verts)]
bmesh.ops.bevel(bm, geom=top_e, offset=4.0, segments=3, affect="EDGES", profile=0.5)
bot_e = [e for e in bm.edges if all(abs(v.co.z) < 1e-6 for v in e.verts)]
bmesh.ops.bevel(bm, geom=bot_e, offset=0.5, segments=2, affect="EDGES", profile=0.5)
body = new_obj("body", bm)
# cradle recess: a pocket 6 mm deep, perpendicular to the top, where the handset lies
REC = dict(x0=-70.0, x1=82.0, y0=-63.0, y1=-11.0)
cutter = new_obj("cutter", slope_box("cutter", REC["x0"], REC["x1"], REC["y0"], REC["y1"], -6.0, 25.0, 9.0, 0.0))
mod = body.modifiers.new("rec", "BOOLEAN"); mod.operation = "DIFFERENCE"; mod.object = cutter; mod.solver = "EXACT"
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me2 = bpy.data.meshes.new_from_object(ev)
body.modifiers.clear(); old = body.data; body.data = me2; bpy.data.meshes.remove(old)
bpy.data.objects.remove(cutter)
# cut a grid (UVs are projected per vertex; big faces would slide) and the band's two heights
bm = bmesh.new(); bm.from_mesh(body.data)
for v in bm.verts: v.co = v.co / mm
bisect_grid(bm, xs=np.arange(-D / 2 + 8, D / 2, 8.0), ys=np.arange(-W / 2 + 8, W / 2, 8.0))
nb = Vector((-(ZF - ZBK) / D, 0, 1)).normalized()      # normal of the band's (sloped) planes
for dz in (0.0, -0.3, -TB):
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4, plane_co=(0, 0, zband(0) + dz), plane_no=nb)
STEP_IN = 2.0
for v in bm.verts:                                      # everything below the band's top edge moves 2 mm inward: a step, then a straight lower wall
    if v.co.z < zband(v.co.x) - 0.15 and (abs(abs(v.co.x) - D / 2) < 12 or abs(abs(v.co.y) - W / 2) < 12):
        h = Vector((v.co.x, v.co.y, 0))
        if h.length > 1: v.co -= h.normalized() * STEP_IN
# the band: a shallow groove round the walls -> pull its verts 0.7 mm in
for v in bm.verts:
    if zband(v.co.x) - TB - 1e-3 <= v.co.z <= zband(v.co.x) + 1e-3 and (abs(abs(v.co.x) - D / 2) < 12 or abs(abs(v.co.y) - W / 2) < 12):
        h = Vector((v.co.x, v.co.y, 0));
        if h.length > 1: v.co -= h.normalized() * 0.0   # flush: the inset tilted the lower wall
bm.to_mesh(body.data); bm.free()
for v in body.data.vertices: v.co = v.co * mm

# ---------- keys, FLASH / REDIAL ----------
KW = 0.75 * PY
keys = []
for i in range(4):
    for j in range(3):
        x = X0 + i * PX; y = Y0 + j * PY
        keys.append(new_obj(f"key_{i}{j}", slope_box("k", x - KD / 2 - 0.5, x + KD / 2 + 0.4, y - KW / 2 - 0.3, y + KW / 2 + 0.3, -1.0, KH + 0.3, 1.3, 0.4)))
BTN = [("flash", C["BFX"], C["BFY"]), ("redial", C["BRX"], C["BRY"])]   # from the joint solve (both photos)
for nm, bx, by in BTN:
    keys.append(new_obj(nm, slope_box(nm, bx - 3.2, bx + 3.2, by - 8.0, by + 8.0, -1.0, 2.6, 3.1, 0.6, seg=6)))

# ---------- handset ----------
HS = dict(xb=HSP["xb"], xf=HSP["xf"], zb=HSP["zb"], zf=HSP["zf"], yc=HSP["yc"], w_end=HSP["we"], w_grip=HSP["we"], top_quad=HSP["top_quad"],
          arch_x0=-9.0, arch_x1=45.0, arch_clear=5.0, floor=-5.5)
REC["x0"] = HS["xb"] - 6; REC["x1"] = HS["xf"] + 3; REC["y0"] = HS["yc"] - HS["w_end"] / 2 - 2; REC["y1"] = HS["yc"] + HS["w_end"] / 2 + 2
SEAM_G, SEAM_D = 0.6, 0.45
def seam_rect(xa, xb_, ya, yb, r, zs, n=5, g=SEAM_G, dpt=SEAM_D, dome=3.0):
    """rounded rectangle in (y, z), counter-clockwise, with a shallow groove (half-height g, depth dpt) cut into both
    straight sides at z = zs: the handset's parting line"""
    def arc(cx, cy, a0):
        return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in np.linspace(a0, a0 + 90, n + 2)[1:-1]]
    zs = min(max(zs, ya + r + g + 0.3), yb - r - g - 0.3)
    pts = [(xb_, ya + r), (xb_, yb - r)]
    pts += arc(xb_ - r, yb - r, 0)
    for t in np.linspace(0, 1, 9)[1:-1]:                           # the crown: a 3 mm dome between the top corners
        yy = (xb_ - r) + t * ((xa + r) - (xb_ - r)); pts.append((yy, yb + dome * math.sin(math.pi * t)))
    pts += arc(xa + r, yb - r, 90)
    pts += [(xa, yb - r), (xa, ya + r)]
    pts += arc(xa + r, ya + r, 180) + arc(xb_ - r, ya + r, 270)
    return pts
def handset():
    """Arched handset: ear and mouth pieces in the pocket, the grip lifted clear of the body between them (the side
    photo: the arch from arch_x0 to arch_x1, its sides sloping), the top a straight line from zb (back) to zf (front),
    every end rounded. Heights are absolute z (mm) on the handset's left-flank silhouette."""
    xb, xf = HS["xb"], HS["xf"]; L = xf - xb
    ss = np.arange(0, L + 1e-6, 1.25)
    def arch(x):   # 0 on the end pieces, 1 along the grip, an 8 mm blend at each end of the arch
        t = min(x - HS["arch_x0"], HS["arch_x1"] - x)
        return 0.0 if t < -1.5 else (1.0 if t > 1.5 else 0.5 + 0.5 * math.sin(math.pi * t / 3))
    def endscale(s):
        e = min(s, L - s); R = 10.0
        return 1.0 if e >= R else max(0.12, math.sqrt(max(0.0, 1 - ((R - e) / R) ** 2)))
    bm = bmesh.new(); rings = []
    for s_ in ss:
        x = xb + s_; a = arch(x); k = endscale(s_)
        w = (HS["w_end"] - (HS["w_end"] - HS["w_grip"]) * a) * k
        top = float(np.polyval(HS["top_quad"], x))             # the side photo's arc: flat at the back, dipping to the front
        base = ztop(x) + HS["floor"] + (HS["arch_clear"] - HS["floor"]) * a
        h = (top - base) * (0.25 + 0.75 * k)                      # the ends round off at the top, their base stays on the floor
        r = min(w * 0.42, h * 0.3)                              # keeps the seam clear of the lower corner arcs on the thin grip
        ring = []
        zs = h - 11.0                                             # the parting seam: a constant 11 mm below the top, so it follows the top's arc
        for (yy, zz) in seam_rect(-w / 2, w / 2, 0, h, r, zs):
            ring.append(bm.verts.new(Vector((x, HS["yc"] + yy, base + zz))))
        rings.append(ring)
    m = len(rings[0])
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for i in range(m):
            bm.faces.new([a_[i], a_[(i + 1) % m], b_[(i + 1) % m], b_[i]])
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm
hs = new_obj("handset", handset())
def seam_ribbon():
    xb, xf = HS["xb"], HS["xf"]; L = xf - xb; ss = np.arange(0, L + 1e-6, 1.25)
    def endscale(s_):
        e = min(s_, L - s_); R = 10.0
        return 1.0 if e >= R else max(0.12, math.sqrt(max(0.0, 1 - ((R - e) / R) ** 2)))
    def arch(x):
        t = min(x - HS["arch_x0"], HS["arch_x1"] - x)
        return 0.0 if t < -1.5 else (1.0 if t > 1.5 else 0.5 + 0.5 * math.sin(math.pi * t / 3))
    left, right = [], []
    for s_ in ss:
        x = xb + s_; k = endscale(s_); w = HS["w_end"] * k
        top = float(np.polyval(HS["top_quad"], x)); base = ztop(x) + HS["floor"] + (HS["arch_clear"] - HS["floor"]) * arch(x)
        h = (top - base) * (0.25 + 0.75 * k)
        zs = min(top - 11.0, base + 0.6 * h)
        left.append((x, HS["yc"] - w / 2 - 0.12, zs)); right.append((x, HS["yc"] + w / 2 + 0.12, zs))
    loop = left + right[::-1]                                   # closed outline at seam height
    bm = bmesh.new(); T_ = 0.25
    lo = [bm.verts.new(Vector((p[0], p[1], p[2] - T_))) for p in loop]
    hi = [bm.verts.new(Vector((p[0], p[1], p[2] + T_))) for p in loop]
    n = len(loop)
    for i in range(n):
        bm.faces.new([lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm
seam = new_obj("handset_seam", seam_ribbon()); seam.data.materials.append(M_BAND)
# cord exit: a short grey stub under the mouthpiece's front (the curly cord itself is left out)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=2.2, radius2=2.2, depth=14)
for v in bm.verts:
    p = slope_pt(0, HS["yc"] - 8, -2.0 + v.co.z) + (HS["xf"] - 10 + v.co.x) * dvec + np.array([0, v.co.y, 0])
    v.co = Vector(p)
cord = new_obj("cord_stub", bm); bpy.data.objects.remove(cord); cord = None
def cord_curve():
    """the cord leaves the BASE through a hole low on the left wall (side photo: x ~14 mm, 4 mm up), curls out to the table"""
    x0, yw, z0 = 13.9, -W / 2 + STEP_IN, 4.4
    pts = [(x0, yw + 3, z0), (x0, yw - 4, z0), (x0 + 3, yw - 12, 3.0), (x0 + 12, yw - 22, 2.0), (x0 + 30, yw - 34, 2.0)]
    cu = bpy.data.curves.new("cord", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 2.0 * mm; cu.bevel_resolution = 6; cu.resolution_u = 16
    sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (q[0] * mm, q[1] * mm, q[2] * mm, 1.0)
    sp.use_endpoint_u = True; sp.order_u = 4
    o = bpy.data.objects.new("handset_cord", cu); sc.collection.objects.link(o); o.data.materials.append(M_CORD)
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    bpy.data.objects.remove(o); mo = bpy.data.objects.new("handset_cord", me); sc.collection.objects.link(mo); return mo
cordm = cord_curve()
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=3.2, radius2=3.2, depth=1.0)   # the hole's dark rim, flush on the wall
for v in bm.verts: v.co = Vector((13.9 + v.co.x, -W / 2 + STEP_IN - 0.2 + v.co.z, 4.4 + v.co.y))
sock = new_obj("cord_hole", bm); sock.data.materials.append(M_KEY)
M_SLOT = mat_flat("grille_slot", (0.25, 0.24, 0.22) if MODE == "pbr" else (0.30, 0.29, 0.26), rough=0.8)
def hit2(u, v, P0, n):
    """side-photo pixel -> the point of plane (P0, n) on its ray"""
    d = RM2.T @ np.array([(u - IW2 / 2) / F2, (v - IH2 / 2) / F2, 1.0]); P0 = np.array(P0, float); n = np.array(n, float)
    return CAM2 + (n @ (P0 - CAM2)) / (n @ d) * d
floor_P0 = [0, 0, ztop(0) - 6 / math.cos(AL)]
g_bl = hit2(500, 745, floor_P0, nvec); g_fl = hit2(540, 810, floor_P0, nvec); g_fr = hit2(820, 820, floor_P0, nvec)
GX0, GX1 = float(min(g_bl[0], g_fl[0])), float(g_fr[0]) ; GX0 = max(GX0, HS["arch_x0"] - 2); GX1 = min(GX1, HS["arch_x1"] + 2)
print("GRILLE x %.1f..%.1f" % (GX0, GX1))
extras = []
NSLOT = 11; pitch = (GX1 - GX0) / NSLOT
for i in range(NSLOT):
    gx = GX0 + (i + 0.5) * pitch
    o = new_obj(f"grille_{i}", slope_box("g", gx - 0.6, gx + 0.6, HS["yc"] - 11, HS["yc"] + 11, -7.8, -5.9, 0.4, 0.0, seg=2))
    o.data.materials.append(M_SLOT); extras.append(o)
for j, gy in enumerate((HS["yc"] - 8, HS["yc"] + 8)):
    o = new_obj(f"hook_{j}", slope_box("h", GX0 - 12.0, GX0 - 5.0, gy - 2.0, gy + 2.0, -6.0, -1.5, 1.2, 0.5, seg=3))
    o.data.materials.append(M_KEY); extras.append(o)

# ---------- materials by visibility from the photo's camera ----------
def smooth(o, on=True):
    for p in o.data.polygons: p.use_smooth = on
objs_all = [body, hs, None] + keys
trees = []
for o in objs_all:
    if o is None: trees.append(None); continue
    me = o.data; trees.append(BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons]))
CAMV = Vector(CAM * mm)
THR = {}
SIDE_OK = set() if MODE == "pbr" else {0}   # pbr: the left wall is plain plastic; photo: the body takes the side photo
CORD = np.array([[492,1395],[485,1450],[470,1500],[445,1535],[405,1560],[350,1580],[290,1590]], float)   # the straight cord in the photo
def on_cord(q, r=17.0):
    for a, b in zip(CORD[:-1], CORD[1:]):
        ab = b - a; t = np.clip(np.dot(q - a, ab) / np.dot(ab, ab), 0, 1)
        if np.linalg.norm(a + t * ab - q) < r: return True
    return False
HS_POLY = np.array([[455,795],[640,795],[660,830],[655,1000],[642,1300],[640,1400],[610,1422],[340,1422],[330,1380],[345,1250],[400,1000],[430,850]], float)
def in_poly(q, P):
    inside = False; j = len(P) - 1
    for i in range(len(P)):
        if (P[i,1] > q[1]) != (P[j,1] > q[1]) and q[0] < (P[j,0]-P[i,0]) * (q[1]-P[i,1]) / (P[j,1]-P[i,1]) + P[i,0]: inside = not inside
        j = i
    return inside
CAMV2 = Vector(CAM2 * mm)
SIDE_POLY = np.array([[140,690],[1140,880],[1140,1075],[140,870]], float)   # the left wall in the side photo (+ handset above it)
def side_ok(q):
    """side-photo pixel usable: on the phone, not on the cords (the coil hanging over the wall, the straight cord at the front)"""
    if 455 < q[0] < 580 and q[1] > 880: return False
    if q[0] > 1085 and 850 < q[1] < 1030: return False
    return 130 < q[0] < 1150 and 560 < q[1] < 1090
def visible2(c, n, self_i):
    if n.y > -0.5: return False          # the side photo only for the left wall; on the top it carried the wall/table behind
    to = CAMV2 - c; dist = to.length; d = to / dist
    if n.dot(d) < 0.3: return False
    if not side_ok(proj2(np.array(c) / mm)): return False
    for t in trees:
        if t is not None and t.ray_cast(c + d * 0.0003, d, dist - 0.0002)[0] is not None: return False
    return True
def visible(c, n, self_i):
    to = CAMV - c; dist = to.length; d = to / dist
    if n.dot(d) < THR.get(self_i, 0.08): return False
    if self_i == 0:
        q = proj(np.array(c) / mm); cm = np.array(c) / mm
        if on_cord(q, 20.0) or (q[0] < 338 and q[1] > 1488) or q[0] < 312: return False
        if REC["x0"] - 1 < cm[0] < REC["x1"] + 1 and REC["y0"] - 1 < cm[1] < REC["y1"] + 1 and cm[2] < ztop(cm[0]) + 0.2: return False
    for i, t in enumerate(trees):
        if t is None: continue
        hit = t.ray_cast(c + d * 0.0003, d, dist - 0.0002)
        if hit[0] is not None: return False
    return True
def assign(o, self_i, flat_rule, force_photo=False, photo_mat=None):
    photo_mat = photo_mat or M_PHOTO
    """flat_rule(normal, centre_mm) -> material for faces the photo cannot give"""
    me = o.data; mats = [M_PHOTO]; idx = {M_PHOTO.name: 0}
    me.materials.clear()                      # the boolean's evaluated mesh carried an empty slot: every index was off by one
    while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
    uv = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        c = p.center; nrm = p.normal
        cmm = np.array(c) / mm
        if MODE == "pbr" and self_i == 0 and zband(cmm[0]) - TB - 0.2 <= cmm[2] <= zband(cmm[0]) + 0.2 and nrm.z < 0.6:
            m = M_BAND
            for li in p.loop_indices: uv.data[li].uv = (0.5, 0.5)
        elif MODE == "pbr" and self_i == 0 and cmm[1] < REC["y1"] + 6:   # the body's handset side: plain plastic (the photo's handset shadow read as a dent there)
            m = flat_rule(nrm, cmm)
            for li in p.loop_indices: uv.data[li].uv = (0.5, 0.5)
        elif MODE == "pbr" and self_i in (1, 2):      # the handset and cord stub: plain plastic, nothing printed on them
            m = flat_rule(nrm, cmm)
            for li in p.loop_indices: uv.data[li].uv = (0.5, 0.5)
        elif MODE == "pbr" and self_i >= 3 and float(np.dot(np.array(nrm), nvec)) < 0.5:
            m = M_KEY
            for li in p.loop_indices: uv.data[li].uv = (0.5, 0.5)
        elif self_i == 1 and flat_rule(nrm, cmm) is M_BAND:
            m = M_BAND
            for li in p.loop_indices: uv.data[li].uv = (0.5, 0.5)
        elif visible(c, nrm, self_i) and (not force_photo or (in_poly(proj(np.array(c) / mm), HS_POLY) and (float(np.dot(np.array(nrm), nvec)) > 0.55 or nrm.dot((CAMV - c).normalized()) > 0.6))):
            m = photo_mat
            for li in p.loop_indices:
                q = proj(np.array(me.vertices[me.loops[li].vertex_index].co) / mm)
                uv.data[li].uv = (q[0] / IW, 1 - q[1] / IH)
        elif self_i in SIDE_OK and visible2(c, nrm, self_i):
            m = M_PHOTO2
            for li in p.loop_indices:
                q = proj2(np.array(me.vertices[me.loops[li].vertex_index].co) / mm)
                uv.data[li].uv = (q[0] / IW2, 1 - q[1] / IH2)
        else:
            m = flat_rule(nrm, np.array(c) / mm)
            for li in p.loop_indices: uv.data[li].uv = (0.5, 0.5)
        if m.name not in idx: idx[m.name] = len(mats); mats.append(m)
        p.material_index = idx[m.name]
    for m in mats: me.materials.append(m)
    from collections import Counter
    print("MATS", o.name, Counter(me.materials[p.material_index].name for p in me.polygons).most_common(6), "nverts", len(me.vertices))
def body_rule(nrm, c):
    if nrm.z < -0.5: return M_UNDER
    if zband(c[0]) - TB - 0.2 <= c[2] <= zband(c[0]) + 0.2 and nrm.z < 0.6: return M_BAND   # the band and the step's underside
    inside = REC["x0"] - 1 < c[0] < REC["x1"] + 1 and REC["y0"] - 1 < c[1] < REC["y1"] + 1 and c[2] < ztop(c[0]) - 0.3
    if inside: return M_RECESS
    if X0 - 12 < c[0] < X0 + 3 * PX + 12 and Y0 - 14 < c[1] < Y0 + 2 * PY + 14: return M_BODY_KEYS
    return M_BODY if nrm.z > 0.5 else M_BODY_SIDE
assign(body, 0, body_rule)
THR[1] = 0.3
def hs_rule(nrm, c):
    t = min(c[0] - HS["arch_x0"], HS["arch_x1"] - c[0]); a = 0.0 if t < -1.5 else (1.0 if t > 1.5 else 0.5 + 0.5 * math.sin(math.pi * t / 3))
    base = ztop(c[0]) + HS["floor"] + (HS["arch_clear"] - HS["floor"]) * a
    top = float(np.polyval(HS["top_quad"], c[0])); zs = top - 11.0
    return M_HANDSET
assign(hs, 1, hs_rule, force_photo=True)
for i, k in enumerate(keys): assign(k, 3 + i, lambda nrm, c: M_KEY, photo_mat=M_PHOTO_KEYS)
smooth(body); smooth(hs); smooth(seam); smooth(cordm); smooth(sock)
for o in extras: smooth(o)
for k in keys: smooth(k)
for o in objs_all:
    if o is None: continue
    for p in o.data.polygons:
        if o is body and p.normal.z < -0.9: p.use_smooth = False
# the body: flat shading on its planar faces (top, rim, pocket floor and walls, outer walls); only the bevels smooth.
# Smoothing across the boolean's slivers dented the rim beside the pocket.
for p in body.data.polygons:
    nz = abs(p.normal.z); p.use_smooth = 0.08 < nz < 0.92
for o in [o for o in objs_all if o is not None and o is not body] + [seam]:   # smooth only edges under 50 deg (Blender 4.1+: auto smooth is a modifier/attribute)
    try:
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
        o.select_set(False)
    except Exception as e:
        print("smooth_by_angle failed", e)

# ---------- photo camera ----------
cam_d = bpy.data.cameras.new("photo_cam"); cam = bpy.data.objects.new("photo_camera", cam_d); sc.collection.objects.link(cam)
cam_d.sensor_fit = "HORIZONTAL"; cam_d.sensor_width = 36.0; cam_d.lens = F / IW * 36.0; cam_d.clip_start = 0.01
Mcw = Matrix(RM.T.tolist()) @ Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1)))
cam.matrix_world = Matrix.Translation(CAMV) @ Mcw.to_4x4()
sc.camera = cam

# ---------- render setup ----------
eng = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
sc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in eng else "BLENDER_EEVEE_NEXT"
sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
if MODE == "pbr": sc.view_settings.exposure = float(arg("--exposure", "-1.35"))   # measured: the top rendered 1.6-2x the photo and clipped
sc.eevee.taa_render_samples = 16 if MODE == "match" else 48
if arg("--engine") == "cycles":                       # showcase stills
    sc.render.engine = "CYCLES"; sc.cycles.samples = int(arg("--samples", "96")); sc.cycles.use_denoising = True
    try:
        bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "METAL"; sc.cycles.device = "GPU"
    except Exception: pass
sc.render.film_transparent = True
world = bpy.data.worlds.new("world"); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]
if MODE == "match":
    bg.inputs[1].default_value = 0.0
else:
    bg.inputs[0].default_value = (0.7, 0.7, 0.72, 1); bg.inputs[1].default_value = 0.3 if MODE == "pbr" else 0.22
    for nm, loc, en, sz in [("key", (0.45, -0.35, 0.55), 9.0 if MODE == "pbr" else 5.0, 0.7), ("fill", (0.2, 0.5, 0.4), 4.0 if MODE == "pbr" else 2.2, 0.9), ("rim", (-0.5, 0.1, 0.45), 4.0 if MODE == "pbr" else 2.5, 0.5)]:
        ld = bpy.data.lights.new(nm, "AREA"); ld.energy = en; ld.size = sz
        lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo); lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0.03)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.mesh.primitive_plane_add(size=0.8, location=(0, 0, -0.0005))
    fl = bpy.context.object; fl.name = "floor"; fl.data.materials.append(mat_flat("floor", (0.42, 0.37, 0.31), rough=0.7))
    sc.render.film_transparent = False

cam2_d = bpy.data.cameras.new("side_cam"); cam2o = bpy.data.objects.new("side_camera", cam2_d); sc.collection.objects.link(cam2o)
cam2_d.sensor_fit = "HORIZONTAL"; cam2_d.sensor_width = 36.0; cam2_d.lens = F2 / IW2 * 36.0; cam2_d.clip_start = 0.01
cam2o.matrix_world = Matrix.Translation(CAMV2) @ (Matrix(RM2.T.tolist()) @ Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1)))).to_4x4()
def shoot(name, loc=None, target=(0, 0, 0.03), lens=50):
    if name == "photo":
        sc.camera = cam; sc.render.resolution_x = IW if MODE == "match" else RES; sc.render.resolution_y = IH if MODE == "match" else RES * 4 // 3
    elif name == "sidephoto":
        sc.camera = cam2o; sc.render.resolution_x = IW2 if MODE == "match" else RES; sc.render.resolution_y = IH2 if MODE == "match" else RES * 4 // 3
    else:
        cd = bpy.data.cameras.new(name); co = bpy.data.objects.new(name, cd); sc.collection.objects.link(co)
        cd.lens = lens; cd.clip_start = 0.01; co.location = loc
        co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.camera = co; sc.render.resolution_x = RES; sc.render.resolution_y = RES * 3 // 4
    sc.render.filepath = os.path.join(OUT, name + ".png"); bpy.ops.render.render(write_still=True)
VIEWS = {
    "front34": ((0.42, -0.30, 0.26), (0, 0, 0.025), 45),
    "front34r": ((0.42, 0.30, 0.26), (0, 0, 0.025), 45),
    "rear34": ((-0.42, -0.32, 0.28), (0, 0, 0.03), 45),
    "left": ((0.0, -0.55, 0.12), (0, 0, 0.03), 50),
    "top": ((0.0, 0.0, 0.6), (0, 0, 0.0), 50),
    "keys": ((0.17, 0.0, 0.17), (0.02, 0.05, 0.02), 50),
    "handset": ((0.25, -0.2, 0.14), (0.0, -0.037, 0.04), 50),
    "front": ((0.5, 0.0, 0.07), (0, 0, 0.025), 60),
    "show_q": ((0.36, -0.26, 0.22), (0.0, 0.0, 0.025), 50),
    "show_rear": ((-0.38, 0.22, 0.24), (0.0, 0.0, 0.025), 50),
    "show_top": ((0.04, 0.0, 0.5), (0.0, 0.0, 0.0), 50),
    "show_left": ((0.02, -0.42, 0.12), (0.0, 0.0, 0.025), 50),
    "pocket_fl": ((0.11, -0.13, 0.07), (0.04, -0.06, 0.02), 60),
}
os.makedirs(OUT, exist_ok=True)
for s in SHOTS:
    shoot(s) if s in ("photo", "sidephoto") else shoot(s, *VIEWS[s])
sc.camera = cam

def tidy_scene():
    for o in [o for o in sc.objects if o.type == "CAMERA" and o not in (cam, cam2o)]: bpy.data.objects.remove(o)
    cam2o.data.display_size = 0.05
    pc = bpy.data.collections.new("Tesan_phone"); sc.collection.children.link(pc)
    stc = bpy.data.collections.new("studio"); sc.collection.children.link(stc)
    root = bpy.data.objects.new("Tesan_phone", None); root.empty_display_size = 0.03; pc.objects.link(root)
    for o in list(sc.collection.objects):
        tgt = stc if (o.type in ("LIGHT", "CAMERA") or o.name == "floor") else pc
        sc.collection.objects.unlink(o); tgt.objects.link(o)
        if tgt is pc: o.parent = root
    cam.data.display_size = 0.05
    for o in sc.objects: o.select_set(False)
    root.select_set(True); bpy.context.view_layer.objects.active = root
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type != "VIEW_3D": continue
            sp = area.spaces[0]; sp.clip_start = 0.001; sp.clip_end = 100; sp.overlay.show_extras = False
            sp.shading.type = "MATERIAL"; r3 = sp.region_3d
            r3.view_location = (0, 0, 0.03); r3.view_distance = 0.5; r3.view_perspective = "PERSP"
            r3.view_rotation = (Vector((0.42, -0.30, 0.26)) - Vector((0, 0, 0.025))).to_track_quat("Z", "Y")
if arg("--blend"):
    tidy_scene()
    for im in bpy.data.images: im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(arg("--blend")))
if arg("--glb"):
    for o in [o for o in sc.objects if o.type in ("LIGHT", "CAMERA") or o.name == "floor"]: bpy.data.objects.remove(o)
    for o in sc.objects: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(arg("--glb")), export_format="GLB", export_cameras=False, export_lights=False, export_apply=True, export_yup=True)
print("DONE")
