# blender -b bake/baked.blend -P novel.py -- TEXD PREFIX : photo-textured model from viewpoints no photo has -> out/<prefix>_<view>.png
import bpy, sys, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
a = sys.argv[sys.argv.index('--') + 1:]; TEXD = a[0] if a else 'tex'; PRE = a[1] if len(a) > 1 else 'nov'
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    m = bpy.data.materials.new('tx_' + o.name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = bpy.data.images.load(os.path.abspath('%s/%s.png' % (TEXD, o.name)))
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(tn.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0]); o.data.materials.clear(); o.data.materials.append(m)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = False
sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'; sc.render.film_transparent = False; sc.render.resolution_x = 1200; sc.render.resolution_y = 800
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True; sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.75, 0.78, 0.82, 1)
VIEWS = {'rear34': ((-11, -6, 2.2), (0, 0, 1.6), 35), 'rightside': ((0.3, -13, 1.7), (0.3, 0, 1.7), 35), 'leftside': ((0.3, 13, 1.7), (0.3, 0, 1.7), 35),
         'top34': ((8, 8, 7.5), (0, 0, 2.0), 35), 'rearend': ((-8.5, 0.0, 1.8), (-3, 0, 1.6), 40), 'front_close': ((5.6, 1.2, 1.4), (3.6, 0, 1.3), 40),
         'under_low': ((3, 4.2, 0.35), (0.5, 0, 0.45), 30), 'roof_top': ((0.5, 3.5, 6.5), (0.5, 0, 3.1), 30), 'platform_in': ((2.9, 0.15, 1.6), (0, 0, 1.6), 22)}
cd = bpy.data.cameras.new('nc'); co = bpy.data.objects.new('nc', cd); sc.collection.objects.link(co); sc.camera = co
for n, (p, t, lens) in VIEWS.items():
    co.location = p; d = Vector(t) - Vector(p); co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens
    sc.render.filepath = os.path.abspath('out/%s_%s.png' % (PRE, n)); bpy.ops.render.render(write_still=True)
