# blender -b bake/geom.blend -P match.py -- [r1 r5 ...] : photo-projected textures as emission, rendered from the photo cameras
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); os.chdir(os.path.dirname(os.path.abspath(__file__)))
import geom
sc = bpy.context.scene
FLAT = {'flag': (0.75, 0.03, 0.05), 'balcony_rail': (0.25, 0.27, 0.3), 'ubalcony_rail': (0.3, 0.32, 0.35): (0.8, 0.8, 0.8), 'sea': (0.03, 0.12, 0.22)}
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    o.hide_render = False
    m = bpy.data.materials.new('m_' + o.name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], out.inputs[0])
    p = os.path.abspath('tex/%s_photo.png' % o.name)
    if os.path.exists(p) and o.name not in FLAT:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(p); nt.links.new(t.outputs[0], em.inputs[0])
    else:
        em.inputs[0].default_value = (*FLAT.get(o.name, (1, 0, 1)), 1)
    o.data.materials.clear(); o.data.materials.append(m)
for o in [o for o in bpy.data.objects if o.type == 'CAMERA']: bpy.data.objects.remove(o)
sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.cycles.use_denoising = False; sc.cycles.pixel_filter_type = 'BLACKMAN_HARRIS'; sc.cycles.filter_width = 1.5
sc.render.film_transparent = False; sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
os.makedirs('out', exist_ok=True)
names = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
for n in (names or ['r%d' % i for i in range(1, 7)]):
    geom.set_camera(n); sc.render.filepath = os.path.abspath('out/match_%s.png' % n); bpy.ops.render.render(write_still=True)
