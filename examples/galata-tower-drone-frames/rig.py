import bpy, json, os
from math import radians, cos, sin
from mathutils import Vector
def light(here, ground=True):
    L=json.load(open(os.path.join(here,'light.json')))
    for o in [o for o in bpy.data.objects if o.type=='LIGHT']: bpy.data.objects.remove(o)
    if L.get('sun',0)>0:
        sd=bpy.data.lights.new('Sun','SUN'); so=bpy.data.objects.new('Sun',sd); bpy.context.scene.collection.objects.link(so)
        az,el=radians(L['sun_az']),radians(L['sun_el']); d=Vector((cos(az)*cos(el),sin(az)*cos(el),sin(el)))
        so.rotation_euler=d.to_track_quat('Z','Y').to_euler(); sd.energy=L['sun']; sd.angle=radians(L.get('sun_angle',20))
    w=bpy.data.worlds.new('World'); bpy.context.scene.world=w; w.use_nodes=True; nt=w.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputWorld'); bg=nt.nodes.new('ShaderNodeBackground'); bg2=nt.nodes.new('ShaderNodeBackground')
    mix=nt.nodes.new('ShaderNodeMixShader'); lp=nt.nodes.new('ShaderNodeLightPath')
    bg.inputs[0].default_value=(*L['sky_cam'],1)
    tc=nt.nodes.new('ShaderNodeTexCoord'); sep=nt.nodes.new('ShaderNodeSeparateXYZ'); ramp=nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Generated'],sep.inputs[0]); nt.links.new(sep.outputs['Z'],ramp.inputs[0])
    hor=L['horizon']; zen=L['zenith']
    ramp.color_ramp.elements[0].position=0.0; ramp.color_ramp.elements[0].color=(*hor,1)
    ramp.color_ramp.elements[1].position=1.0; ramp.color_ramp.elements[1].color=(*zen,1)
    nt.links.new(ramp.outputs[0],bg2.inputs[0])
    nt.links.new(lp.outputs['Is Camera Ray'],mix.inputs[0]); nt.links.new(bg.outputs[0],mix.inputs[2]); nt.links.new(bg2.outputs[0],mix.inputs[1]); nt.links.new(mix.outputs[0],out.inputs[0])
    if ground:
        import geom
        bpy.ops.mesh.primitive_circle_add(vertices=64,radius=120,fill_type='NGON',location=(0,0,geom.P['zg']))
        g=bpy.context.active_object; g.name='ground'
        m=bpy.data.materials.new('ground'); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=(*L['ground'],1); b.inputs['Roughness'].default_value=1.0
        g.data.materials.append(m); g.visible_camera=False
        return g
def gpu():
    sc=bpy.context.scene; sc.render.engine='CYCLES'
    try:
        pr=bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type='METAL'; pr.get_devices()
        for d in pr.devices: d.use=True
        sc.cycles.device='GPU'
    except Exception as e: print('gpu',e)
