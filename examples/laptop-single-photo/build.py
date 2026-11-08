"""Blender: MacBook Pro 14 model from one photo.
Run: Blender -b -P build.py -- --mode match|final --out DIR [--blend f.blend] [--glb f.glb] [--res 1000] [--shots photo,...]
Frame: +X front, +Y the laptop's left, +Z up, metres. Camera solved in solve.py (cam.json).
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Matrix, Vector

A = sys.argv[sys.argv.index("--") + 1:]
arg = lambda k, d=None: A[A.index(k) + 1] if k in A else d
MODE = arg("--mode", "final"); OUT = arg("--out", "render"); RES = int(arg("--res", "1000"))
SHOTS = arg("--shots", "photo").split(",")
HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "cam.json")))
mm = 0.001
W, D, HB, HL, HX, LL, PHI = (C[k] * (mm if k not in ("phi",) else 1) for k in ("W", "D", "HB", "HL", "HX", "LL", "phi"))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


# ---------- materials ----------
def img(name):
    return bpy.data.images.load(os.path.join(HERE, "tex", name + ".png"))


def mat_tex(name, image, kind):
    """kind: screen (emits), surface (photo colour, lit), for MODE=match all are pure emission."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = image; t.extension = "EXTEND"; t.interpolation = "Cubic"
    if MODE == "match":
        e = nt.nodes.new("ShaderNodeEmission"); nt.links.new(t.outputs[0], e.inputs[0])
        nt.links.new(e.outputs[0], out.inputs[0]); return m
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    if kind == "screen":
        b.inputs["Base Color"].default_value = (0, 0, 0, 1)
        nt.links.new(t.outputs[0], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 1.0
        b.inputs["Roughness"].default_value = 0.3; b.inputs["Specular IOR Level"].default_value = 0.12
    else:
        nt.links.new(t.outputs[0], b.inputs["Base Color"])
        nt.links.new(t.outputs[0], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 0.7
        b.inputs["Roughness"].default_value = 0.6; b.inputs["Specular IOR Level"].default_value = 0.15
    nt.links.new(b.outputs[0], out.inputs[0]); return m


def mat_flat(name, rgb, metallic=0.0, rough=0.5, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if MODE == "match":
        e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*rgb, 1)
        nt.links.new(e.outputs[0], out.inputs[0]); return m
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = 3
    nt.links.new(b.outputs[0], out.inputs[0]); return m


M_DECK = mat_tex("deck", img("deck"), "surface")
M_SCREEN = mat_tex("screen", img("screen"), "screen")
BODY_RGB = (0.032, 0.032, 0.035) if MODE == "match" else (0.06, 0.06, 0.065)  # space black anodised aluminium
M_BODY = mat_flat("space_black", BODY_RGB, metallic=0.85, rough=0.42)
M_PORT = mat_flat("port_black", (0.005, 0.005, 0.005), rough=0.6)
M_FOOT = mat_flat("foot_rubber", (0.01, 0.01, 0.01), rough=0.9)
M_LED = mat_flat("magsafe_led", (0.1, 0.9, 0.2), emit=(0.1, 1.0, 0.2))


# ---------- geometry ----------
def slab(name, x0, x1, w, h, r_plan, r_top, r_bot, seg=14):
    """Rounded-rectangle prism: x in [x0,x1], y in [-w/2,w/2], z in [0,h]."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), v.co.y * w, (v.co.z + 0.5) * h))
    vert_edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6]
    bmesh.ops.bevel(bm, geom=vert_edges, offset=r_plan, segments=seg, affect="EDGES", profile=0.5)
    if r_top > 0:
        top = [e for e in bm.edges if all(abs(v.co.z - h) < 1e-6 for v in e.verts)]
        bmesh.ops.bevel(bm, geom=top, offset=r_top, segments=3, affect="EDGES", profile=0.5)
    if r_bot > 0:
        bot = [e for e in bm.edges if all(abs(v.co.z) < 1e-6 for v in e.verts)]
        bmesh.ops.bevel(bm, geom=bot, offset=r_bot, segments=4, affect="EDGES", profile=0.5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    return o


def assign(o, rules):
    """rules: list of (material, test(normal, centre) -> bool, uv(co) -> (u,v) or None); last rule is the default."""
    me = o.data
    for m, _, _ in rules:
        me.materials.append(m)
    uv = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        n, c = p.normal, p.center
        for i, (m, test, f) in enumerate(rules):
            if test(n, c):
                p.material_index = i
                for li in p.loop_indices:
                    co = me.vertices[me.loops[li].vertex_index].co
                    uv.data[li].uv = f(co) if f else (0.5, 0.5)
                break
        p.use_smooth = True


# base: x in [-D/2, D/2]
base = slab("base", -D / 2, D / 2, W, HB, 11 * mm, 0.7 * mm, 2.6 * mm)
assign(base, [
    (M_DECK, lambda n, c: n.z > 0.6, lambda co: ((co.y + W / 2) / W, (D / 2 - co.x) / D)),
    # the front wall is body material like the sides: the photo's front strip (brownish with the table's reflection)
    # met the black sides in a visible step at both front corners
    (M_BODY, lambda n, c: True, None),
])

# key caps: rectangles fitted in the deck texture (keys_layout.py), raised KEY_UP above the deck. Each cap's top
# takes the deck texture at the point where the photo camera's ray through it meets the deck, so from the photo's
# viewpoint the labels stay exactly where they were.
KEY_UP, KEY_DOWN = 0.75 * mm, 0.4 * mm
CAMP = Vector(C["cam"]) * mm
TEXW, TEXH, PXMM = 1875, 1327, 6.0
M_KEYSIDE = mat_flat("key_side", (0.012, 0.012, 0.014), rough=0.5)
kb = bmesh.new()
for x0, y0, x1, y1 in json.load(open(os.path.join(HERE, "keys.json"))):
    # texture px -> model: column -> y, row -> x (row 0 = back)
    ya, yb = -W / 2 + x0 / TEXW * W, -W / 2 + x1 / TEXW * W
    xa, xb = -D / 2 + y0 / TEXH * D, -D / 2 + y1 / TEXH * D   # row 0 = back (x = -D/2); xa < xb
    t = bmesh.new()
    bmesh.ops.create_cube(t, size=1.0)
    for v in t.verts:
        v.co = Vector(((xa + xb) / 2 + v.co.x * (xb - xa), (ya + yb) / 2 + v.co.y * (yb - ya),
                       HB - KEY_DOWN + (v.co.z + 0.5) * (KEY_UP + KEY_DOWN)))
    ve = [e for e in t.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-7]
    bmesh.ops.bevel(t, geom=ve, offset=min(1.1 * mm, (xb - xa) / 3), segments=4, affect="EDGES", profile=0.5)
    te = [e for e in t.edges if all(abs(v.co.z - (HB + KEY_UP)) < 1e-7 for v in e.verts)]
    bmesh.ops.bevel(t, geom=te, offset=0.3 * mm, segments=2, affect="EDGES", profile=0.5)
    me_t = bpy.data.meshes.new("tmp"); t.to_mesh(me_t); t.free(); kb.from_mesh(me_t); bpy.data.meshes.remove(me_t)
me_k = bpy.data.meshes.new("keys"); kb.to_mesh(me_k); kb.free()
keys = bpy.data.objects.new("keys", me_k); sc.collection.objects.link(keys)


def deck_uv_through_camera(co):
    s = (HB - CAMP.z) / (co.z - CAMP.z)
    q = CAMP + (co - CAMP) * s
    return ((q.y + W / 2) / W, (D / 2 - q.x) / D)


assign(keys, [
    (M_DECK, lambda n, c: n.z > 0.5, deck_uv_through_camera),
    (M_KEYSIDE, lambda n, c: True, None),
])
for p in keys.data.polygons: p.use_smooth = False

# lid: local x from hinge along the lid, z=0 the screen face; rotated open by PHI about the hinge axis
lid = slab("lid", -3 * mm, LL, W, HL, 10 * mm, 0.8 * mm, 0.6 * mm)
assign(lid, [
    (M_SCREEN, lambda n, c: n.z < -0.6, lambda co: ((co.y + W / 2) / W, co.x / LL)),
    (M_BODY, lambda n, c: True, None),
])
lid.location = (HX, 0, HB); lid.rotation_euler = (0, -PHI, 0)

# hinge barrel (hidden in the photo, seen from behind)
bpy.ops.mesh.primitive_cylinder_add(radius=3.6 * mm, depth=W - 60 * mm, location=(-D / 2 + 4.5 * mm, 0, HB - 3.2 * mm),
                                    rotation=(math.pi / 2, 0, 0), vertices=48)
hinge = bpy.context.object; hinge.name = "hinge"; hinge.data.materials.append(M_BODY)
for p in hinge.data.polygons: p.use_smooth = True

# feet
for i, (fx, fy) in enumerate([(D / 2 - 20 * mm, W / 2 - 20 * mm), (D / 2 - 20 * mm, -W / 2 + 20 * mm),
                              (-D / 2 + 20 * mm, W / 2 - 20 * mm), (-D / 2 + 20 * mm, -W / 2 + 20 * mm)]):
    bpy.ops.mesh.primitive_cylinder_add(radius=6 * mm, depth=1.2 * mm, location=(fx, fy, -0.3 * mm), vertices=32)
    f = bpy.context.object; f.name = f"foot_{i}"; f.data.materials.append(M_FOOT)


# ports: thin black rounded slots set into the sides (laptop's left = +y: MagSafe, 2x Thunderbolt, headphone;
# right = -y: SDXC, Thunderbolt, HDMI). Positions along x (front = +D/2), from Apple's port layout.
def port(name, x, side, w, h, z=None, r=None):
    z = HB * 0.48 if z is None else z
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, side * (W / 2 - 0.25 * mm), z))
    o = bpy.context.object; o.name = name; o.scale = (w, 1.2 * mm, h)
    bev = o.modifiers.new("b", "BEVEL"); bev.width = (r or h * 0.45); bev.segments = 4
    o.data.materials.append(M_PORT); return o


port("magsafe", -D / 2 + 30 * mm, +1, 13.5 * mm, 3.2 * mm)
port("thunderbolt_l1", -D / 2 + 52 * mm, +1, 8.6 * mm, 3.0 * mm)
port("thunderbolt_l2", -D / 2 + 67 * mm, +1, 8.6 * mm, 3.0 * mm)
bpy.ops.mesh.primitive_cylinder_add(radius=1.8 * mm, depth=1.2 * mm, location=(D / 2 - 40 * mm, W / 2 - 0.25 * mm, HB * 0.48),
                                    rotation=(math.pi / 2, 0, 0), vertices=24)
bpy.context.object.name = "headphone"; bpy.context.object.data.materials.append(M_PORT)
port("sdxc", D / 2 - 45 * mm, -1, 24 * mm, 2.2 * mm, r=0.5 * mm)
port("thunderbolt_r", -D / 2 + 62 * mm, -1, 8.6 * mm, 3.0 * mm)
port("hdmi", -D / 2 + 35 * mm, -1, 14.5 * mm, 4.4 * mm, r=1 * mm)

# MagSafe status light on the plug is the cable's, not the laptop's: left out.

# ---------- camera from the photo ----------
cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("photo_camera", cam_d); sc.collection.objects.link(cam)
cam_d.sensor_fit = "HORIZONTAL"; cam_d.sensor_width = 36; cam_d.lens = C["f"] / 2000 * 36
cam_d.clip_start = 0.01
import numpy as np  # Blender ships numpy
from mathutils import Quaternion
rv = Vector(C["rotvec"]); ang = rv.length
Rm = Quaternion(rv.normalized(), ang).to_matrix() if ang > 0 else Matrix.Identity(3)
Mcw = Rm.transposed() @ Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1)))
cam.matrix_world = Matrix.Translation(Vector(C["cam"]) * mm) @ Mcw.to_4x4()
sc.camera = cam

# ---------- render setup ----------
sc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE_NEXT"
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x = RES; sc.render.resolution_y = RES * 3 // 4
sc.render.film_transparent = True
world = bpy.data.worlds.new("world"); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]
if MODE == "match":
    bg.inputs[1].default_value = 0.0
else:
    bg.inputs[0].default_value = (0.6, 0.6, 0.63, 1); bg.inputs[1].default_value = 0.25
    for nm, loc, en, sz in [("key", (0.6, -0.5, 0.8), 14, 0.8), ("fill", (0.3, 0.7, 0.5), 6, 1.0), ("rim", (-0.7, 0.2, 0.6), 12, 0.6)]:
        ld = bpy.data.lights.new(nm, "AREA"); ld.energy = en; ld.size = sz
        lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo); lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0.08)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, -0.0009))
    fl = bpy.context.object; fl.name = "floor"; fl.data.materials.append(mat_flat("floor", (0.22, 0.22, 0.23), rough=0.8))
    fl.is_holdout = False
    sc.render.film_transparent = False


def shoot(name, loc, target=(0, 0, 0.07), lens=50):
    if name == "photo":
        sc.camera = cam
    else:
        cd = bpy.data.cameras.new(name); co = bpy.data.objects.new(name, cd); sc.collection.objects.link(co)
        cd.lens = lens; cd.clip_start = 0.01; co.location = loc
        co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.camera = co
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)


VIEWS = {
    "photo": None,
    "front34": ((0.55, -0.42, 0.32), (0, 0, 0.07), 45),
    "front34r": ((0.55, 0.42, 0.32), (0, 0, 0.07), 45),
    "rear34": ((-0.55, -0.45, 0.35), (0, 0, 0.08), 45),
    "side": ((0, -0.7, 0.12), (0, 0, 0.08), 50),
    "keys": ((0.18, -0.12, 0.2), (0.02, 0, 0.01), 40),
    "ports": ((0.0, 0.32, 0.06), (-0.04, 0.15, 0.005), 50),
    "corner_r": ((0.2, -0.24, 0.07), (0.1, -0.15, 0.005), 50),
    "corner_l": ((0.2, 0.24, 0.07), (0.1, 0.15, 0.005), 50),
    "lidtop": ((0.42, 0.05, 0.13), (-0.15, 0.0, 0.21), 50),
}
_dl = Vector((math.cos(PHI), 0, math.sin(PHI))); _nl = Vector((math.sin(PHI), 0, -math.cos(PHI)))
_lc = Vector((HX, 0, HB)) + _dl * (LL / 2)
VIEWS["screen"] = (tuple(_lc + _nl * 0.55), tuple(_lc), 50)   # square on to the screen: is the menu bar level?
os.makedirs(OUT, exist_ok=True)
for s in SHOTS:
    if s == "photo":
        sc.render.resolution_x = 2000 if MODE == "match" else RES; sc.render.resolution_y = sc.render.resolution_x * 3 // 4
        shoot("photo", None)
    else:
        sc.render.resolution_x = RES; sc.render.resolution_y = RES * 3 // 4
        shoot(s, *VIEWS[s])
sc.camera = cam


def tidy_scene():
    """What the user sees on opening the file: only the laptop (one parent, in its own collection), a small floor,
    the lights and the photo's camera in a 'studio' collection, the view framed on the laptop and Rendered."""
    for o in [o for o in sc.objects if o.type == "CAMERA" and o != cam]:   # the render shots' cameras
        bpy.data.objects.remove(o)
    laptop_c = bpy.data.collections.new("MacBook_Pro_14"); sc.collection.children.link(laptop_c)
    studio_c = bpy.data.collections.new("studio"); sc.collection.children.link(studio_c)
    root = bpy.data.objects.new("MacBook_Pro_14", None); root.empty_display_size = 0.05
    laptop_c.objects.link(root)
    for o in list(sc.collection.objects):
        target = studio_c if (o.type in ("LIGHT", "CAMERA") or o.name == "floor") else laptop_c
        sc.collection.objects.unlink(o); target.objects.link(o)
        if target is laptop_c:
            o.parent = root
    cam.data.display_size = 0.06                                           # 1 m frustum lines crossed the laptop
    fl = bpy.data.objects.get("floor")
    if fl: fl.scale = (0.3, 0.3, 1)                                         # 1.2 m, not 4 m
    for o in sc.objects: o.select_set(False)
    root.select_set(True); bpy.context.view_layer.objects.active = root
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type != "VIEW_3D":
                continue
            sp = area.spaces[0]
            sp.clip_start = 0.001; sp.clip_end = 100
            sp.overlay.show_extras = False   # lights' ground lines and the camera crossed the laptop; Overlays > Extras shows them
            sp.shading.type = "MATERIAL"   # a file saved with RENDERED reopens in SOLID (grey); Material Preview stays
            r3 = sp.region_3d
            r3.view_location = (0, 0, 0.07); r3.view_distance = 0.75; r3.view_perspective = "PERSP"
            r3.view_rotation = (Vector((0.55, -0.42, 0.32)) - Vector((0, 0, 0.07))).to_track_quat("Z", "Y")


if arg("--blend"):
    tidy_scene()
    for i in bpy.data.images: i.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(arg("--blend")))
if arg("--glb"):
    for o in [o for o in sc.objects if o.type in ("LIGHT",) or o.name == "floor" or (o.type == "CAMERA" and o != cam)]:
        bpy.data.objects.remove(o)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(arg("--glb")), export_format="GLB", export_cameras=False,
                              export_apply=True)
print("DONE")
