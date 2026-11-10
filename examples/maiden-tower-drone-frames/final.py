# blender -b bake/geom.blend -P final.py -- [views] [--blend path] : real materials (albedo from the photos, light divided out), sun + sky
import bpy, sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
import rig, geom
X = json.load(open('extra.json')); sc = bpy.context.scene
ROUGH = {'terrace': 0.45, 'parapet': 0.45, 'fort': 0.88, 'merlons': 0.88, 'shaft': 0.85, 'court': 0.9, 'quay': 0.8, 'rocks': 0.9, 'annex': 0.6, 'porch': 0.6,
         'annex_roof': 0.75, 'room': 0.5, 'cornice': 0.5, 'corbel': 0.55, 'balcony': 0.55, 'dome': 0.38, 'ubalcony': 0.45, 'pole': 0.35, 'beacon': 0.4}
def principled(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    return m, nt, nt.nodes['Principled BSDF']
def build_materials():
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:
        o.hide_render = False; m, nt, b = principled(o.name)
        p = os.path.abspath('tex/%s_alb.png' % o.name)
        if o.name == 'finial':
            b.inputs['Base Color'].default_value = (*X['gold'], 1); b.inputs['Metallic'].default_value = 1; b.inputs['Roughness'].default_value = 0.28
        elif o.name in ('balcony_rail', 'ubalcony_rail', 'beacon_cage'):
            c = X['rail'] if o.name == 'balcony_rail' else [0.75, 0.75, 0.75]
            b.inputs['Base Color'].default_value = (*c, 1); b.inputs['Metallic'].default_value = 0.8 if o.name == 'balcony_rail' else 0.0; b.inputs['Roughness'].default_value = 0.45
        elif o.name == 'boulders':
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.abspath('tex/rock_tile.png')); nt.links.new(t.outputs[0], b.inputs['Base Color'])
            b.inputs['Roughness'].default_value = 0.85; b.inputs['Specular IOR Level'].default_value = 0.15
        elif o.name == 'flag':
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.abspath('tex/flag.png')); nt.links.new(t.outputs[0], b.inputs['Base Color'])
            b.inputs['Roughness'].default_value = 0.7; m.use_backface_culling = False
        elif o.name == 'sea':
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.abspath('tex/sea.png'))
            tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / 60, 1 / 60, 1)
            nt.links.new(tc.outputs['Object'], mp.inputs[0]); nt.links.new(mp.outputs[0], t.inputs[0]); nt.links.new(t.outputs[0], b.inputs['Base Color'])
            b.inputs['Roughness'].default_value = 0.12; b.inputs['Specular IOR Level'].default_value = 0.12
            nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.9; nz.inputs['Detail'].default_value = 6
            bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; nt.links.new(tc.outputs['Object'], nz.inputs[0]); nt.links.new(nz.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal'])
        elif os.path.exists(p):
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(p); nt.links.new(t.outputs[0], b.inputs['Base Color'])
            b.inputs['Roughness'].default_value = ROUGH.get(o.name, 0.6); b.inputs['Specular IOR Level'].default_value = X.get('spec', {}).get(o.name, 0.12)
            if o.name == 'dome': b.inputs['Roughness'].default_value = 0.45
        o.data.materials.clear(); o.data.materials.append(m)
if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    build_materials(); rig.gpu(); rig.light(HERE)
    for o in [o for o in bpy.data.objects if o.type == 'CAMERA']: bpy.data.objects.remove(o)
    sc.cycles.samples = 48; sc.cycles.use_denoising = True; sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
    os.makedirs('out', exist_ok=True)
    for n in [a for a in args if a.startswith('r')] or ['r%d' % i for i in range(1, 7)]:
        G = json.load(open('gain.json')); import math
        sc.view_settings.exposure = -math.log2(sum(G[n]['g']) / 3)
        geom.set_camera(n); sc.render.filepath = os.path.abspath('out/final_%s.png' % n); bpy.ops.render.render(write_still=True)
    sc.view_settings.exposure = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('out/final_work.blend'))
