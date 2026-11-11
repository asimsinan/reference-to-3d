# close views of the door and lower panels for side-by-side with photos 11 / 12
import bpy, sys, os
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.argv = sys.argv[:sys.argv.index('--') + 1] + ['real']; sys.path.insert(0, HERE)
exec(open(os.path.join(HERE, 'final34.py')).read().split("for a in ACTS:")[0])
cd = bpy.data.cameras.new('cl'); co = bpy.data.objects.new('cl', cd); col_s.objects.link(co); sc.camera = co
sc.render.film_transparent = False; sc.render.resolution_x, sc.render.resolution_y = 1400, 900; sc.cycles.samples = int(os.environ.get('SAMPLES', '48'))
root.location = (0, 0, 0)
X = T.Xe; V = {'front': ((T.Xf + 3.2, 0.0, 1.75), (T.Xf, 0, 1.9), 30), 'logos': ((T.CX, -4.2, 1.15), (T.CX, -T.hw, 1.15), 30), 'p20B': ((2 * T.CX - T.Xe + 0.5, -3.3, 1.6), (2 * T.CX - T.Xe - 0.6, -T.hw, 1.55), 26), 'p20F': ((T.Xe - 0.5, 3.3, 1.6), (T.Xe + 0.6, T.hw, 1.55), 26), 'p17': ((T.Xe - 1.4, -3.6, 1.45), (T.Xe + 1.1, -T.hw, 1.35), 24), 'p16': ((T.CX + 2.6, -3.6, 1.35), (T.CX - 0.4, -T.hw, 0.55), 30), 'lamp': ((T.Xf + 1.2, -0.9, 1.4), (T.Xf, 0, 1.3), 40), 'sign': ((T.M['xk'] + 2.2, 0.0, 3.1), (T.M['xk'], 0, 3.05), 50), 'door_L': ((X + 0.2, 3.3, 1.6), (X + 0.75, T.hw, 1.45), 26), 'door_R': ((X - 0.6, -3.0, 1.5), (X + 0.8, -T.hw, 1.45), 24),
     'side_L': ((X - 1.6, 4.0, 1.4), (X - 1.4, T.hw, 1.3), 28)}
for n, (p, t, lens) in V.items():
    if os.environ.get('ONLYV') and n not in os.environ['ONLYV'].split(','): continue
    place(co, cd, p, t, lens); sc.render.filepath = os.path.abspath('out/cl34_%s.png' % n); bpy.ops.render.render(write_still=True)
