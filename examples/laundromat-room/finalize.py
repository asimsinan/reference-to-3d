import bpy, sys
out=sys.argv[sys.argv.index('--')+1]
print('screens',[s.name for s in bpy.data.screens])
for scr in bpy.data.screens:
    for a in scr.areas:
        if a.type=='VIEW_3D':
            sp=a.spaces[0]; sp.shading.type='MATERIAL'; sp.region_3d.view_perspective='CAMERA'
            sp.overlay.show_floor=False; sp.overlay.show_axis_x=False; sp.overlay.show_axis_y=False
            sp.lens=24; sp.clip_start=0.05
bpy.ops.file.pack_all()
for o in bpy.context.view_layer.objects: o.select_set(False)
r=bpy.data.objects['Laundromat']; r.select_set(True); bpy.context.view_layer.objects.active=r
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('SAVED',out)
