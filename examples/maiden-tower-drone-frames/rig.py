import bpy, json, os
from math import radians, cos, sin
from mathutils import Vector
def light(here):
    L = json.load(open(os.path.join(here, 'light.json')))
    for o in [o for o in bpy.data.objects if o.type == 'LIGHT']: bpy.data.objects.remove(o)
    sd = bpy.data.lights.new('Sun', 'SUN'); so = bpy.data.objects.new('Sun', sd); bpy.context.scene.collection.objects.link(so)
    az, el = radians(L['sun_az']), radians(L['sun_el']); d = Vector((cos(az) * cos(el), sin(az) * cos(el), sin(el)))
    so.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); so.location = d * 80
    m = max(L['sun']); sd.energy = m; sd.color = [c / m for c in L['sun']]; sd.angle = radians(0.6)
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); bg2 = nt.nodes.new('ShaderNodeBackground')
    mix = nt.nodes.new('ShaderNodeMixShader'); lp = nt.nodes.new('ShaderNodeLightPath')
    bg.inputs[0].default_value = (*L['sky'], 1); bg2.inputs[0].default_value = (0.45, 0.62, 0.85, 1)
    # lighting sky: zenith -> horizon gradient (clear sky is darker and bluer overhead, hazy and brighter at the horizon)
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], ramp.inputs[0])
    zen = L.get('zenith', [0.10, 0.20, 0.42]); hor = L.get('horizon', [0.75, 0.82, 0.92])
    ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (*hor, 1)
    ramp.color_ramp.elements[1].position = 1.0; ramp.color_ramp.elements[1].color = (*zen, 1)
    e = ramp.color_ramp.elements.new(0.18); e.color = (*[0.55 * a + 0.45 * b for a, b in zip(hor, zen)], 1)
    nt.links.new(ramp.outputs[0], bg2.inputs[0])
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0]); nt.links.new(bg.outputs[0], mix.inputs[1]); nt.links.new(bg2.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])
    return so
def gpu():
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'
    try:
        pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'METAL'; pr.get_devices()
        for d in pr.devices: d.use = True
        sc.cycles.device = 'GPU'
    except Exception as e: print('gpu', e)
