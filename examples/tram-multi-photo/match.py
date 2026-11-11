# blender -b bake/baked.blend -P match.py -- [cams] : photo-textured emission render from each photo camera -> out/match{k}.png
import bpy, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
import rig
REFD = os.environ.get('REF', 'ref')
TEXD = os.environ.get('TEXD', 'tex'); TAG = os.environ.get('TAG', 'match')
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    m = bpy.data.materials.new('tx_' + o.name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = bpy.data.images.load(os.path.abspath('%s/%s.png' % (TEXD, o.name))); tn.interpolation = 'Linear'
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(tn.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
    o.data.materials.clear(); o.data.materials.append(m)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = False
sc.cycles.pixel_filter_type = 'BOX'; sc.cycles.filter_width = 1.0; sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.render.dither_intensity = 0
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
ks = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 1 else list(rig.J['cams'])
for k in ks:
    rig.photo_camera(k); sc.render.filepath = os.path.abspath('out/%s%s.png' % (TAG, k)); bpy.ops.render.render(write_still=True)
