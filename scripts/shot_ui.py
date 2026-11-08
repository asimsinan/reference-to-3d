"""Open a .blend with the interface, screenshot the window after ~6 s, quit: what the user will see on opening it.
Run: Blender file.blend --factory-startup -P shot_ui.py -- out.png"""
import bpy
import sys
OUT=sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else "ui.png"
n=[0]
def tick():
    n[0]+=1
    if n[0]<12: return 0.5
    win=bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=win, screen=win.screen):
        bpy.ops.screen.screenshot(filepath=OUT)
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick, first_interval=1.0)
