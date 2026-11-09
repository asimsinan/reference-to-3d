import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--')+1])
for o in bpy.data.objects:
    if o.type!='MESH': continue
    m=o.data.materials[0] if o.data.materials else None
    print('%-18s verts %6d uv %s mat %s blend %s'%(o.name,len(o.data.vertices),[u.name for u in o.data.uv_layers],m.name if m else None,getattr(m,'blend_method','-') if m else None))
print('images:',[(i.name,i.size[:]) for i in bpy.data.images])
