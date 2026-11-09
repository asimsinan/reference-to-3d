import bpy,sys
out=sys.argv[sys.argv.index('--')+1]
for o in bpy.data.objects:
    if o.type=='LIGHT': o.data.energy={'key':40,'fill':15,'rim':25}.get(o.name,10)
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type=='VIEW_3D':
                sp.shading.type='MATERIAL'; sp.overlay.show_extras=False
                r3=sp.region_3d; r3.view_location=(0,0,0.15); r3.view_distance=0.8
bpy.ops.object.select_all(action='DESELECT'); bpy.data.objects['vazo'].select_set(True)
bpy.ops.file.pack_all(); bpy.ops.wm.save_as_mainfile(filepath=out+'/vazo_foto.blend')
bpy.ops.export_scene.gltf(filepath=out+'/vazo_foto.glb',use_selection=True,export_format='GLB')
