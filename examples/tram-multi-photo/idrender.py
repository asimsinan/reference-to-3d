# blender -b -P idrender.py -- [cams]   -> out/id{k}.png + out/idmap.json
import bpy, sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import geom, rig
if os.environ.get('V34'):
    import geom34; obs = geom34.build_all(interior=bool(os.environ.get('INT')))
else:
    obs = geom.build_all()
for o in obs:
    bpy.context.view_layer.objects.active = o
for o in obs:
    for md in list(o.modifiers):
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
cols = rig.id_colors(obs)
for o in obs:
    m = rig.emission_mat('id_' + o.name, cols[o.name]); o.data.materials.clear(); o.data.materials.append(m)
json.dump({k: [round(c * 255) for c in v] for k, v in cols.items()}, open(os.path.join(HERE, 'out', 'idmap.json'), 'w'))
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 1; sc.cycles.use_denoising = False
sc.cycles.pixel_filter_type = 'BOX'; sc.cycles.filter_width = 0.01; sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'; sc.render.dither_intensity = 0; sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
ks = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 1 else list(rig.J['cams'])
for k in ks:
    rig.photo_camera(k); sc.render.filepath = os.path.join(HERE, 'out', 'id%s.png' % k)
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'out', 'geom.blend'))
