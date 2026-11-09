# Blender: build the 737 and render from the photo camera.
# blender -b -P build.py -- MODE OUT   (MODE: id | match | final)
import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import importlib, geom, params, mats
importlib.reload(geom); importlib.reload(params); importlib.reload(mats)
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['id', 'out_id.png']
MODE, OUT = argv[0], argv[1]

def clear():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)

def set_camera(cam_json='cam.json'):
    c = json.load(open(cam_json))
    R = Matrix(c['R']); C = Vector(c['C'])
    cd = bpy.data.cameras.new('photo_cam'); ob = bpy.data.objects.new('photo_cam', cd)
    bpy.context.scene.collection.objects.link(ob)
    Rw = R.transposed() @ Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1)))
    ob.matrix_world = Matrix.Translation(C) @ Rw.to_4x4()
    cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36; cd.lens = c['f'] * 36 / c['W']
    cd.clip_start = 1; cd.clip_end = 2000
    sc = bpy.context.scene; sc.camera = ob
    sc.render.resolution_x = c['W']; sc.render.resolution_y = c['H']; sc.render.resolution_percentage = 100
    return ob

def emit_mat(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*col, 1)
    o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0], o.inputs[0])
    return m

PALETTE = {'fuselage': (1, 0, 0), 'belly': (1, 0.5, 0), 'fin': (0, 1, 0), 'wing': (0, 0, 1), 'htail': (0, 1, 1),
           'nacelle': (1, 0, 1), 'duct': (0.3, 0, 0.3), 'core': (0.5, 0.5, 0), 'plug': (0.5, 0.5, 0),
           'spinner': (1, 1, 1), 'pylon': (1, 1, 0), 'ftf': (0.5, 0, 1), 'nosewheel': (0.2, 0.6, 0.2),
           'mainwheel': (0.2, 0.6, 0.2), 'nose': (0.6, 0.6, 0.6), 'main': (0.6, 0.6, 0.6)}

def render_settings(engine='BLENDER_EEVEE_NEXT'):
    sc = bpy.context.scene
    try: sc.render.engine = engine
    except TypeError: sc.render.engine = 'BLENDER_EEVEE'
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'

if __name__ == '__main__':
    clear()
    P = params.params()
    obs = geom.build_all(P)
    set_camera()
    render_settings()
    if MODE == 'id':
        mats = {}
        for o in obs:
            key = o.name.split('_')[0]
            col = PALETTE.get(key, (0.5, 0.5, 0.5))
            if key not in mats: mats[key] = emit_mat('id_' + key, col)
            o.data.materials.clear(); o.data.materials.append(mats[key])
        bpy.context.scene.eevee.taa_render_samples = 1 if hasattr(bpy.context.scene, 'eevee') else 1
        bpy.context.scene.render.filepath = os.path.abspath(OUT)
        bpy.ops.render.render(write_still=True)
    elif MODE == 'match':
        cam = json.load(open('cam.json'))
        for o in obs: mats.match_material(o, cam)
        bpy.context.scene.render.filepath = os.path.abspath(OUT)
        if not os.environ.get('NORENDER'): bpy.ops.render.render(write_still=True)
    elif MODE in ('final', 'views', 'sunpass', 'skypass', 'skylow', 'skyhigh', 'fillpass'):
        cal = json.load(open('calib.json')) if os.path.exists('calib.json') else {}
        if MODE not in ('final', 'views'):
            cal = dict(cal); cal.update(sun=1.0, sun_color=[1, 1, 1], sky_low=[1 if MODE == 'skylow' else 0] * 3,
                                        sky_high=[1 if MODE == 'skyhigh' else 0] * 3)
        for o in obs: mats.final_material(o, cal)
        mats.ground(cal, size=float(os.environ.get('GROUND', 220)))
        mats.world_and_sun(cal, sun_on=MODE in ('final', 'views', 'sunpass'), sky_on=MODE not in ('sunpass', 'fillpass'))
        if MODE == 'fillpass':
            mats.fill_light([1, 1, 1], float(os.environ['FILL_EL']), float(os.environ['FILL_AZ']))
        elif MODE in ('final', 'views') and 'fill' in cal:
            mats.fill_light(cal['fill'], cal['fill_el'], cal['fill_az'])
        sc = bpy.context.scene; sc.render.engine = 'CYCLES'
        try:
            sc.cycles.device = 'GPU'
            bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'METAL'
            bpy.context.preferences.addons['cycles'].preferences.get_devices()
            for dv in bpy.context.preferences.addons['cycles'].preferences.devices: dv.use = True
        except Exception as e: print('gpu', e)
        sc.cycles.samples = int(os.environ.get('SAMPLES', 128)); sc.cycles.use_denoising = True
        sc.render.resolution_percentage = int(os.environ.get('PCT', 100))
        sc.render.film_transparent = MODE not in ('final', 'views')
        sc.view_settings.view_transform = 'Standard'
        if MODE not in ('final', 'views'):
            sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
        if os.environ.get('NORENDER'):
            pass
        elif MODE == 'views':
            sc.render.film_transparent = False
            VIEWS = {'v_right34': ((55, -60, 14), (0, 0, 3), 35), 'v_rear34': ((-75, 45, 12), (-2, 0, 4), 35),
                     'v_top': ((10, 0, 120), (0, 0, 0), 30), 'v_side': ((0, 95, 4), (0, 0, 4), 40),
                     'v_engine': ((24, 14, 2.5), (8.5, 5.0, 1.8), 50), 'v_nose': ((28, 9, 2.5), (17, 0, 2.2), 45),
                     'v_front': ((70, 0, 4), (0, 0, 4), 50), 'v_under': ((10, 30, 0.6), (2, 0, 2.5), 28)}
            sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
            from mathutils import Vector
            for nm, (loc, tgt, lens) in VIEWS.items():
                cd = bpy.data.cameras.new(nm); co = bpy.data.objects.new(nm, cd); sc.collection.objects.link(co)
                co.location = loc; cd.lens = lens; cd.clip_end = 5000
                co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
                sc.camera = co; sc.render.filepath = os.path.abspath('views/%s.png' % nm)
                bpy.ops.render.render(write_still=True)
        else:
            sc.render.filepath = os.path.abspath(OUT)
            bpy.ops.render.render(write_still=True)
    if os.environ.get('DELIVER'):
        import deliver; deliver.tidy_and_save(os.environ['DELIVER'], os.environ.get('GLB'))
    else:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('dbg_%s.blend' % MODE))
