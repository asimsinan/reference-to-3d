import bpy,sys,os; os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,'.')
import geom; geom.clear(); geom.build_all(); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('bake/shape.blend'))
