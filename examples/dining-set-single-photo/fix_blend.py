import bpy
for scr in bpy.data.screens:
    for a in scr.areas:
        if a.type=='VIEW_3D': a.spaces[0].overlay.show_relationship_lines=False
r=bpy.data.objects.get("Masa_Takimi"); r.empty_display_size=0.05
bpy.ops.wm.save_mainfile()
