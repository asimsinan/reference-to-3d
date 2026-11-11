# Blender helpers: photo cameras from cams.json, object-ID renders.
import bpy, json, os, math
import numpy as np
from mathutils import Matrix, Vector
HERE = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(HERE, os.environ.get('CAMS', 'cams.json'))))

def rotvec_to_matrix(rv):
    th = float(np.linalg.norm(rv))
    if th < 1e-12: return np.eye(3)
    k = np.asarray(rv) / th; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K

def photo_camera(k, name=None, scale=1.0):
    c = J['cams'][k]; W, H = J['sizes'][k]
    R = rotvec_to_matrix(c[:3]); C = c[3:6]; f = c[6]; cx, cy = (c[7], c[8]) if len(c) > 7 else (W / 2, H / 2)
    cd = bpy.data.cameras.get(name or ('cam' + k)) or bpy.data.cameras.new(name or ('cam' + k))
    cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36.0; cd.lens = f * 36.0 / W
    cd.shift_x = -(cx - W / 2) / W; cd.shift_y = (cy - H / 2) / W
    cd.clip_start = 0.1; cd.clip_end = 200
    ob = bpy.data.objects.get(name or ('cam' + k))
    if ob is None:
        ob = bpy.data.objects.new(name or ('cam' + k), cd); bpy.context.scene.collection.objects.link(ob)
    M = np.stack([R[0], -R[1], -R[2]], 1)       # columns: camera axes in world
    mw = Matrix(((M[0, 0], M[0, 1], M[0, 2], C[0]), (M[1, 0], M[1, 1], M[1, 2], C[1]), (M[2, 0], M[2, 1], M[2, 2], C[2]), (0, 0, 0, 1)))
    ob.matrix_world = mw
    sc = bpy.context.scene; sc.render.resolution_x = int(W * scale); sc.render.resolution_y = int(H * scale)
    sc.render.resolution_percentage = 100; sc.render.pixel_aspect_x = sc.render.pixel_aspect_y = 1
    sc.camera = ob
    return ob

def emission_mat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (*rgb, 1); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs[0]); return m

def id_colors(objs):
    cols = {}
    rs = np.random.RandomState(7)
    for i, o in enumerate(objs):
        c = tuple(float(v) for v in (rs.randint(20, 255, 3) / 255.0)); cols[o.name] = c
    return cols
