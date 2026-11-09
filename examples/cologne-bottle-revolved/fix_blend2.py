import bpy
for m in bpy.data.materials:
    b=m.node_tree.nodes.get('Principled BSDF') if m.node_tree else None
    if b and (b.inputs['Transmission Weight'].default_value>0 or b.inputs['Transmission Weight'].links):
        m.surface_render_method='BLENDED'; m.use_transparency_overlap=True
        try: m.use_raytrace_refraction=False
        except Exception: pass
bpy.ops.wm.save_mainfile(); print('blended')
