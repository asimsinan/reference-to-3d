import bpy,sys
out=sys.argv[sys.argv.index('--')+1]
for m in bpy.data.materials:
    if m.name.startswith(('photo','unglazed')):
        b=m.node_tree.nodes['Principled BSDF']; t=m.node_tree.nodes.get('Image Texture')
        if t and b.inputs['Base Color'].links: m.node_tree.links.remove(b.inputs['Base Color'].links[0])
        b.inputs['Base Color'].default_value=(0,0,0,1); b.inputs['Emission Strength'].default_value=1.0; b.inputs['Specular IOR Level'].default_value=0.0
bpy.ops.wm.save_as_mainfile(filepath=out+'/vazo_foto.blend')
bpy.ops.object.select_all(action='DESELECT'); bpy.data.objects['vazo'].select_set(True)
bpy.ops.export_scene.gltf(filepath=out+'/vazo_foto.glb',use_selection=True,export_format='GLB')
