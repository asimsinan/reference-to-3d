"""Render the built room from each photo's solved camera and from walking views.
  Blender -b oda_build.blend -P shots.py -- OUTDIR [names...] [--scale 0.33] [--samples 48]
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]; os.makedirs(out, exist_ok=True)
scale = float(argv[argv.index('--scale') + 1]) if '--scale' in argv else 0.33
samples = int(argv[argv.index('--samples') + 1]) if '--samples' in argv else 48
names = [a for i_, a in enumerate(argv[1:], 1) if not a.startswith('--') and not a.replace('.', '').isdigit() and argv[i_ - 1] != '--hide']
C = json.load(open(os.path.join(HERE, 'cams_final.json')))
R = json.load(open(os.path.join(HERE, 'room_final.json')))
sc = bpy.context.scene; sc.cycles.samples = samples
if '--exposure' in argv: sc.view_settings.exposure = float(argv[argv.index('--exposure') + 1])
if '--hide' in argv:
    for o in bpy.data.objects:
        if o.name.startswith(argv[argv.index('--hide') + 1]): o.hide_render = True

WALK = {  # name: (eye, look-at, horizontal fov deg, W, H)
    'walk_door_in': ((1.25, 5.0, 1.6), (1.2, 0.0, 1.0), 80, 1600, 1000),
    'walk_window_out': ((1.3, 1.2, 1.6), (1.3, 5.4, 1.1), 80, 1600, 1000),
    'walk_left_wall': ((2.2, 3.4, 1.6), (0.0, 2.8, 1.1), 80, 1600, 1000),
    'walk_right_wall': ((0.5, 3.0, 1.6), (2.55, 3.6, 1.0), 80, 1600, 1000),
    'walk_down_desk': ((1.2, 2.3, 1.7), (0.7, 0.6, 0.6), 75, 1600, 1000),
    'close_bookcase': ((1.2, 3.9, 1.35), (2.4, 3.92, 1.1), 60, 1200, 1000),
    'close_cart': ((1.75, 2.45, 0.95), (1.30, 2.0, 0.55), 45, 1200, 900),
    'close_desk': ((1.3, 1.9, 1.45), (0.5, 0.7, 0.75), 60, 1400, 900),
    'close_chairs': ((1.4, 2.4, 1.1), (0.4, 2.35, 0.5), 70, 1400, 900),
    'corridor_look': ((2.6, 6.9, 1.6), (0.7, 5.78, 1.2), 75, 1400, 1000),
    'corridor_far': ((0.7, 6.2, 1.6), (0.4, 7.9, 1.2), 70, 1000, 1200),
    'corridor_long': ((-0.05, 6.9, 1.6), (14.0, 6.9, 1.3), 70, 1000, 1300),
    'close_window': ((1.0, 1.2, 1.4), (1.0, 0.0, 1.35), 60, 1200, 900),
    'close_printer': ((1.45, 0.85, 1.35), (2.3, 0.3, 0.75), 50, 1200, 900),
    'printer_front': ((1.25, 0.30, 1.15), (2.3, 0.29, 0.75), 45, 1000, 1000),
    'chair_front': ((1.45, 2.53, 0.85), (2.2, 2.53, 0.55), 55, 900, 1100),
    'close_phone': ((0.75, 1.95, 1.2), (0.3, 1.2, 0.75), 50, 1200, 900),
    'close_shelf': ((1.4, 3.92, 1.15), (2.4, 3.92, 1.15), 55, 1200, 1000),
    'shelf_oblique': ((1.6, 3.2, 1.3), (2.3, 3.95, 1.05), 50, 1200, 1000),
    'bk_v1': ((1.85, 4.10, 1.30), (2.45, 3.90, 1.55), 60, 1400, 700),
    'bk_v2': ((1.25, 3.30, 1.05), (2.35, 3.90, 0.90), 55, 1400, 900),
    'bk_v3': ((1.75, 2.85, 1.75), (2.40, 3.60, 1.00), 55, 900, 1100),
    'bk_v4': ((1.55, 4.55, 1.10), (2.40, 3.85, 0.85), 55, 1200, 800),
    'rp_close': ((1.85, 4.05, 0.97), (2.33, 4.05, 0.84), 30, 1000, 900),
    'rp_side': ((1.95, 3.55, 0.98), (2.33, 3.80, 0.84), 32, 1000, 900),
    'fb_close': ((1.85, 4.16, 1.60), (2.31, 4.06, 1.54), 34, 1200, 700),
    'dp_close': ((0.50, 1.80, 1.12), (0.27, 1.32, 0.78), 30, 1000, 800),
    'lp_close': ((0.75, 1.10, 1.10), (0.47, 0.40, 0.85), 34, 1000, 900),
    'rp_front': ((1.70, 4.04, 1.00), (2.33, 4.04, 0.84), 26, 1000, 900),
    'rp_oblique': ((1.80, 3.80, 1.05), (2.33, 4.04, 0.84), 26, 1000, 900),
    'top': ((R['W'] / 2, R['L'] / 2, 9.0), (R['W'] / 2, R['L'] / 2 + 0.001, 0), 40, 900, 1500),
}


def add_cam(name, M_world, lens_mm, sensor, w, h):
    cd = bpy.data.cameras.new(name); cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = sensor; cd.lens = lens_mm
    cd.clip_start = 0.02; cd.clip_end = 50
    o = bpy.data.objects.new(name, cd); sc.collection.objects.link(o); o.matrix_world = M_world
    return o


for n in (names or list(C) + list(WALK)):
    if n in C:
        c = C[n]; Rm = c['R']
        right = Vector(Rm[0]); down = Vector(Rm[1]); fwd = Vector(Rm[2])
        rot = Matrix((right, -down, -fwd)).transposed()
        Mw = Matrix.Translation(c['pos']) @ rot.to_4x4()
        w, h = c['W'], c['H']; lens = c['f'] * 36 / w
        cam = add_cam('shot_' + n, Mw, lens, 36, w, h)
        cam.data.shift_x = -(c['cx'] - w / 2) / w; cam.data.shift_y = (c['cy'] - h / 2) / w
    else:
        eye, at, fov, w, h = WALK[n]
        fwd = (Vector(at) - Vector(eye)).normalized()
        upv = Vector((0, 0, 1)) if abs(fwd.z) < 0.99 else Vector((0, 1, 0))
        right = fwd.cross(upv).normalized(); up = right.cross(fwd)
        rot = Matrix((right, up, -fwd)).transposed()
        lens = 18 / math.tan(math.radians(fov) / 2)
        cam = add_cam('shot_' + n, Matrix.Translation(eye) @ rot.to_4x4(), lens, 36, w, h)
    sc.camera = cam
    sc.render.resolution_x = int(w * scale); sc.render.resolution_y = int(h * scale); sc.render.resolution_percentage = 100
    sc.render.filepath = os.path.join(out, n + '.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', n)
