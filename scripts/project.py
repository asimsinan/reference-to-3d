"""Blender: the reference views projected onto the mesh(es) as their texture, then rendered, saved, or baked and
exported for a game engine.

Each surface point takes the colour of the one view that faces it best (the views' weights are the normal's share to
the --power, 16 by default: in effect a choice, not a blend, so no doubled features where two views disagree). Each
view's texture is fitted to the model's own outline from that side (box to box), so small scale differences between
views do not matter. The colour is emitted as it is and rendered with the Standard view transform, so a view rendered
from its own direction gives back the reference's pixels.

The object's frame: +X front, +Y left, +Z up (see hull.py). Views: front, rear, left, right, top. With one side view,
it serves both sides (mirrored). Meshes are OBJ files written in that frame (hull.py, loft.py), imported as they are.

Run: Blender -b -P project.py -- --mesh body.obj[,wheel_fl.obj,...] --tex TEXDIR --views front,left,rear,top
       [--top-front left] [--top-min-nz 0] [--power 16] [--under dark|side] [--smooth 0] [--mirror on|off]
       [--persp "rear=12,1.0;front=8,1.0"]   (views that were perspective shots: camera D m beyond the object, H m up)
       [--render OUTDIR [--res 1400] [--shots front,left,rear,top,front34,rear34,front34r] [--mask]]
       [--blend out.blend [--pack]]
       [--export out.glb [--tex-size 4096] [--emission] [--decimate 0.1]]
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


MESHES = [m for m in arg("--mesh", "").split(",") if m]
TEX = arg("--tex")
VIEWS = [v for v in arg("--views", "").split(",") if v]
TOP_FRONT = arg("--top-front", "left")
TOP_MIN_NZ = float(arg("--top-min-nz", "0"))
POWER = float(arg("--power", "16"))
UNDER = arg("--under", "dark")
SMOOTH = int(arg("--smooth", "0"))
PERSP = {}
for item in [s for s in arg("--persp", "").split(";") if s]:
    k, v = item.split("=")
    PERSP[k] = tuple(float(x) for x in v.split(","))
MASK = "--mask" in ARGS
MIRROR = arg("--mirror", "on") != "off"  # one side view for both sides (only right for objects symmetric left-right)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
objs = []
for path in MESHES:
    bpy.ops.wm.obj_import(filepath=os.path.abspath(path), forward_axis="Y", up_axis="Z")
    for o in bpy.context.selected_objects:
        o.name = os.path.splitext(os.path.basename(path))[0]
        for p in o.data.polygons:
            p.use_smooth = True
        if SMOOTH:
            cs = o.modifiers.new("smooth", "CORRECTIVE_SMOOTH")
            cs.iterations, cs.smooth_type, cs.use_only_smooth = SMOOTH, "LENGTH_WEIGHTED", True
        objs.append(o)
if not objs:
    raise SystemExit("no --mesh")
bpy.context.view_layer.update()


def world_verts():
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        out += [o.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return out


VS = world_verts()
X0, X1 = min(v.x for v in VS), max(v.x for v in VS)
Y0, Y1 = min(v.y for v in VS), max(v.y for v in VS)
Z0, Z1 = min(v.z for v in VS), max(v.z for v in VS)
SIZE = max(X1 - X0, Y1 - Y0, Z1 - Z0)
print(f"model box x {X0:.3f}..{X1:.3f}, y {Y0:.3f}..{Y1:.3f}, z {Z0:.3f}..{Z1:.3f}")
DIRS = {"front": Vector((1, 0, 0)), "rear": Vector((-1, 0, 0)), "left": Vector((0, 1, 0)), "right": Vector((0, -1, 0)),
        "top": Vector((0, 0, 1))}


def persp_cam(view):
    """The fitted camera of a perspective view: its place and its image axes (right, up) as functions."""
    D, H = PERSP[view]
    c = {"front": Vector((X1 + D, 0, H)), "rear": Vector((X0 - D, 0, H)), "left": Vector((0, Y1 + D, H)),
         "right": Vector((0, Y0 - D, H))}[view]
    return c


def persp_box(view):
    c = persp_cam(view)
    xs, ys = [], []
    for v in VS:
        dep, xi, yi = persp_xy(view, c, v.x, v.y, v.z)
        xs.append(xi)
        ys.append(yi)
    return min(xs), max(xs), min(ys), max(ys)


def persp_xy(view, c, x, y, z):
    if view == "front":
        dep = c.x - x
        return dep, y / dep, (z - c.z) / dep
    if view == "rear":
        dep = x - c.x
        return dep, -y / dep, (z - c.z) / dep
    if view == "left":
        dep = c.y - y
        return dep, -x / dep, (z - c.z) / dep
    dep = y - c.y
    return dep, x / dep, (z - c.z) / dep


# ------------------------------------------------------------------ the projection material
def projection_material(name="projected"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    pos = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], pos.inputs["Vector"])
    nrm = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], nrm.inputs["Vector"])
    PX, PY, PZ = pos.outputs["X"], pos.outputs["Y"], pos.outputs["Z"]
    NX, NY, NZ = nrm.outputs["X"], nrm.outputs["Y"], nrm.outputs["Z"]

    def op(kind, a_, b_=None):
        mt = nt.nodes.new("ShaderNodeMath")
        mt.operation = kind
        for k, v in enumerate((a_, b_)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                mt.inputs[k].default_value = float(v)
            else:
                nt.links.new(v, mt.inputs[k])
        return mt.outputs["Value"]

    def lin(sock, a0, a1):  # (sock - a0) / (a1 - a0)
        return op("DIVIDE", op("SUBTRACT", sock, a0), a1 - a0)

    def sample(view, u, v):
        img = bpy.data.images.load(os.path.join(TEX, view + ".png"))
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image, tx.extension, tx.interpolation = img, "EXTEND", "Linear"
        uv = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(u, uv.inputs["X"])
        nt.links.new(v, uv.inputs["Y"])
        nt.links.new(uv.outputs["Vector"], tx.inputs["Vector"])
        return tx.outputs["Color"]

    def uv_of(view):
        if view in PERSP:
            c = persp_cam(view)
            bx0, bx1, by0, by1 = persp_box(view)
            if view in ("front", "rear"):
                dep = op("SUBTRACT", c.x, PX) if view == "front" else op("SUBTRACT", PX, c.x)
                xi = op("DIVIDE", PY if view == "front" else op("MULTIPLY", PY, -1.), dep)
            else:
                dep = op("SUBTRACT", c.y, PY) if view == "left" else op("SUBTRACT", PY, c.y)
                xi = op("DIVIDE", op("MULTIPLY", PX, -1.) if view == "left" else PX, dep)
            yi = op("DIVIDE", op("SUBTRACT", PZ, c.z), dep)
            return lin(xi, bx0, bx1), lin(yi, by0, by1)
        if view == "front":
            return lin(PY, Y0, Y1), lin(PZ, Z0, Z1)
        if view == "rear":
            return lin(op("MULTIPLY", PY, -1.), -Y1, -Y0), lin(PZ, Z0, Z1)
        if view == "left":
            return lin(op("MULTIPLY", PX, -1.), -X1, -X0), lin(PZ, Z0, Z1)
        if view == "right":
            return lin(PX, X0, X1), lin(PZ, Z0, Z1)
        # the top: u along the image's width, v up the image (1 - from its top)
        u, vt = {"left": (lin(op("MULTIPLY", PX, -1.), -X1, -X0), lin(PY, Y0, Y1)),
                 "right": (lin(PX, X0, X1), lin(op("MULTIPLY", PY, -1.), -Y1, -Y0)),
                 "up": (lin(op("MULTIPLY", PY, -1.), -Y1, -Y0), lin(op("MULTIPLY", PX, -1.), -X1, -X0)),
                 "down": (lin(PY, Y0, Y1), lin(PX, X0, X1))}[TOP_FRONT]
        return u, op("SUBTRACT", 1., vt)

    have = set(VIEWS)
    # one side view serves both sides; one of front/rear serves both ends only if asked for nothing better
    tex_for = {}
    for d in DIRS:
        if d in have:
            tex_for[d] = d
        elif d == "left" and "right" in have and MIRROR:
            tex_for[d] = "right"
        elif d == "right" and "left" in have and MIRROR:
            tex_for[d] = "left"
    colours = {}
    for d, t in tex_for.items():
        if d in ("left", "right") and t != d:  # the mirror: the same image, mapped by length and height
            colours[d] = colours.get(t) or sample(t, *uv_of(t))
        else:
            colours[d] = sample(t, *uv_of(t))
    weights = {}
    for d, c in colours.items():
        n_ = DIRS[d]
        dot = op("ADD", op("ADD", op("MULTIPLY", NX, n_.x), op("MULTIPLY", NY, n_.y)), op("MULTIPLY", NZ, n_.z))
        w = op("POWER", op("MAXIMUM", dot, 0.), POWER)
        if d == "top" and TOP_MIN_NZ > 0:
            mr = nt.nodes.new("ShaderNodeMapRange")
            mr.interpolation_type = "SMOOTHSTEP"
            mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = TOP_MIN_NZ - .03, TOP_MIN_NZ + .03
            nt.links.new(NZ, mr.inputs["Value"])
            w = op("MULTIPLY", w, mr.outputs["Result"])
        weights[d] = w
    under_w = op("POWER", op("MAXIMUM", op("MULTIPLY", NZ, -1.), 0.), POWER)
    if UNDER == "dark":
        rgb = nt.nodes.new("ShaderNodeRGB")
        rgb.outputs["Color"].default_value = (.004, .005, .007, 1)
        colours["_under"], weights["_under"] = rgb.outputs["Color"], under_w
    total = None
    for w in weights.values():
        total = w if total is None else op("ADD", total, w)
    total = op("ADD", total, 1e-9)
    acc = None
    for d, w in weights.items():
        s_ = nt.nodes.new("ShaderNodeVectorMath")
        s_.operation = "SCALE"
        nt.links.new(colours[d], s_.inputs[0])
        nt.links.new(op("DIVIDE", w, total), s_.inputs["Scale"])
        if acc is None:
            acc = s_.outputs["Vector"]
        else:
            ad = nt.nodes.new("ShaderNodeVectorMath")
            ad.operation = "ADD"
            nt.links.new(acc, ad.inputs[0])
            nt.links.new(s_.outputs["Vector"], ad.inputs[1])
            acc = ad.outputs["Vector"]
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(acc, em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])
    return m


PM = projection_material()
for o in objs:
    o.data.materials.clear()
    o.data.materials.append(PM)

# ------------------------------------------------------------------ render settings
r = sc.render
r.engine = "CYCLES"
sc.cycles.samples = 8 if MASK else 24
sc.cycles.use_denoising = False
r.film_transparent = True
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGBA"
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for dev in prefs.devices:
        dev.use = True
    sc.cycles.device = "GPU"
except Exception as e:  # noqa: BLE001  (the CPU then)
    print("no GPU:", e)
cam_d = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
CTR = Vector(((X0 + X1) / 2, (Y0 + Y1) / 2, (Z0 + Z1) / 2))


def shoot(name, out, res):
    r.resolution_x = r.resolution_y = res
    if name in ("front", "rear", "left", "right", "top"):
        d = DIRS[name]
        if name in PERSP:
            c = persp_cam(name)
            cam.location = c
            look = Vector((0, 0, c.z)) if name != "top" else CTR
            cam.rotation_euler = (look - c).to_track_quat("-Z", "Y").to_euler()
            cam_d.type = "PERSP"
            cam_d.lens = 36. * (PERSP[name][0] + SIZE / 2) / (SIZE * 1.15)
        else:
            cam.location = CTR + d * SIZE * 3
            if name == "top":
                rot = {"left": math.pi, "right": 0., "up": math.pi / 2, "down": -math.pi / 2}[TOP_FRONT]
                cam.rotation_euler = (0., 0., rot)
            else:
                cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
            cam_d.type = "ORTHO"
            cam_d.ortho_scale = SIZE * 1.1
    else:  # three quarters: front34 (front-left), front34r (front-right), rear34 (rear-left), rear34r
        az = {"front34": 35, "front34r": -35, "rear34": 145, "rear34r": -145}.get(name, 35)
        a_, e_ = math.radians(az), math.radians(8)
        cam.location = CTR + Vector((math.cos(a_) * math.cos(e_), math.sin(a_) * math.cos(e_), math.sin(e_))) * SIZE * 2.4
        cam.rotation_euler = (CTR - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam_d.type, cam_d.lens = "PERSP", 40
    r.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("SHOT", name, flush=True)


# ------------------------------------------------------------------ the game asset
def bake_and_export(path):
    sc.cycles.samples = 1
    tdir = os.path.join(os.path.dirname(os.path.abspath(path)), "textures")
    os.makedirs(tdir, exist_ok=True)
    big = int(arg("--tex-size", "4096"))
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in objs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
        me.transform(o.matrix_world)
        g = bpy.data.objects.new(o.name + "_game", me)
        sc.collection.objects.link(g)
        o.hide_render = True
        bpy.ops.object.select_all(action="DESELECT")
        g.select_set(True)
        bpy.context.view_layer.objects.active = g
        if arg("--decimate"):  # (a visual hull is dense: a game wants far fewer triangles; the bake keeps the look)
            dm = g.modifiers.new("lighter", "DECIMATE")
            dm.ratio = float(arg("--decimate"))
            bpy.ops.object.modifier_apply(modifier="lighter")
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=.003)
        bpy.ops.object.mode_set(mode="OBJECT")
        ext = max(g.dimensions)
        size = max(512, 2 ** round(math.log2(max(big * ext / SIZE, 1))))
        img = bpy.data.images.new(o.name + "_color", size, size, alpha=False)
        nd = PM.node_tree.nodes.new("ShaderNodeTexImage")
        nd.image = img
        PM.node_tree.nodes.active = nd
        bpy.ops.object.bake(type="EMIT", margin=6, use_clear=True)
        PM.node_tree.nodes.remove(nd)
        img.filepath_raw, img.file_format = os.path.join(tdir, img.name + ".png"), "PNG"
        img.save()
        gm = bpy.data.materials.new(o.name)
        gm.use_nodes = True
        p = gm.node_tree.nodes["Principled BSDF"]
        t = gm.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = img
        gm.node_tree.links.new(t.outputs["Color"], p.inputs["Base Color"])
        p.inputs["Roughness"].default_value, p.inputs["Metallic"].default_value = .45, 0.
        if "--emission" in ARGS:  # the lit parts (bright, saturated pixels) as the material's glow
            import numpy as np
            n = size * size * 4
            a = np.empty(n, np.float32)
            img.pixels.foreach_get(a)
            q = a.reshape(-1, 4)
            mx, mn = q[:, :3].max(1), q[:, :3].min(1)
            on = ((mx > .55) & ((mx - mn) / np.maximum(mx, 1e-4) > .45)) | (mn > .9)
            e = np.zeros_like(q)
            e[on] = q[on]
            e[:, 3] = 1.
            em = bpy.data.images.new(o.name + "_emit", size, size, alpha=False)
            em.pixels.foreach_set(e.ravel())
            em.filepath_raw, em.file_format = os.path.join(tdir, em.name + ".png"), "PNG"
            em.save()
            te = gm.node_tree.nodes.new("ShaderNodeTexImage")
            te.image = em
            gm.node_tree.links.new(te.outputs["Color"], p.inputs["Emission Color"])
            p.inputs["Emission Strength"].default_value = 3.
        g.data.materials.clear()
        g.data.materials.append(gm)
        g.name = o.name  # (the exported node keeps the part's name: body, wheel_fl, ...)
        out.append(g)
        print(f"BAKED {o.name}: {size} px")
    bpy.ops.object.select_all(action="DESELECT")
    for g in out:
        g.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(path), export_format="GLB", use_selection=True, export_apply=True)
    print("EXPORT", path, sum(len(p.vertices) - 2 for g in out for p in g.data.polygons), "triangles")


if arg("--render"):
    od = os.path.abspath(arg("--render"))
    os.makedirs(od, exist_ok=True)
    for s in arg("--shots", "front,left,rear,top,front34,rear34,front34r").split(","):
        if s:
            shoot(s, od, int(arg("--res", "1400")))
def frame_viewports():
    """The saved file opens on the model: every 3D view framed on the meshes, in Material Preview (a view saved as
    Rendered reopens as Solid, all grey), the clip start small enough for small objects."""
    from mathutils import Vector as V
    pts = [o.matrix_world @ V(c) for o in sc.objects if o.type == "MESH" for c in o.bound_box]
    if not pts:
        return
    lo = V([min(p[i] for p in pts) for i in range(3)]); hi = V([max(p[i] for p in pts) for i in range(3)])
    centre, size = (lo + hi) / 2, (hi - lo).length
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type == "VIEW_3D":
                sp = area.spaces[0]
                sp.shading.type = "MATERIAL"; sp.clip_start = size / 1000; sp.clip_end = size * 100
                r3 = sp.region_3d
                r3.view_location = centre; r3.view_distance = size * 1.6; r3.view_perspective = "PERSP"
                r3.view_rotation = V((1.0, -0.75, 0.55)).to_track_quat("Z", "Y")


if arg("--blend"):
    frame_viewports()
    if "--pack" in ARGS:
        bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(arg("--blend")))
    print("SAVED", arg("--blend"))
if arg("--export"):
    bake_and_export(arg("--export"))
