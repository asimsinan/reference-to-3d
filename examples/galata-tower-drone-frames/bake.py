# blender -b -P bake.py : world position + normal per texel (EXR) for textured parts, depth from every photo camera
import bpy, sys, os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); os.chdir(HERE)
import geom
SIZE={'shaft':2048,'roof':2048,'cornice':1024,'arcade':2048,'balcony':1024,'upper':2048,'dormers':512,'finial':512,'posts':512}
SKIP=('railing',)
def bake_attr(o,attr,size,path):
    m=bpy.data.materials.new('bk'); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
    geo=nt.nodes.new('ShaderNodeNewGeometry'); em=nt.nodes.new('ShaderNodeEmission'); out=nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(geo.outputs['Position' if attr=='P' else 'True Normal'],em.inputs[0]); nt.links.new(em.outputs[0],out.inputs[0])
    img=bpy.data.images.new(o.name+attr,size,size,float_buffer=True,alpha=True)
    tn=nt.nodes.new('ShaderNodeTexImage'); tn.image=img; nt.nodes.active=tn
    o.data.materials.clear(); o.data.materials.append(m)
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active=o
    img.generated_color=(0,0,0,0); img.colorspace_settings.name='Non-Color'
    bpy.ops.object.bake(type='EMIT',margin=3,use_clear=True)
    img.filepath_raw=path; img.file_format='OPEN_EXR'; img.save()
geom.clear(); obs=geom.build_all()
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=1; sc.cycles.device='CPU'; sc.cycles.use_denoising=False
os.makedirs('bake',exist_ok=True); names=[]
for o in obs:
    if o.name in SKIP: continue
    sz=SIZE.get(o.name,512)
    bake_attr(o,'P',sz,os.path.abspath('bake/%s_P.exr'%o.name)); bake_attr(o,'N',sz,os.path.abspath('bake/%s_N.exr'%o.name)); names.append(o.name)
open('bake/names.txt','w').write('\n'.join(names))
m=bpy.data.materials.new('depth'); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
geo=nt.nodes.new('ShaderNodeNewGeometry'); vt=nt.nodes.new('ShaderNodeVectorTransform'); vt.vector_type='POINT'; vt.convert_from='WORLD'; vt.convert_to='CAMERA'
sep=nt.nodes.new('ShaderNodeSeparateXYZ'); ab=nt.nodes.new('ShaderNodeMath'); ab.operation='ABSOLUTE'
em=nt.nodes.new('ShaderNodeEmission'); out=nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(geo.outputs['Position'],vt.inputs[0]); nt.links.new(vt.outputs[0],sep.inputs[0]); nt.links.new(sep.outputs['Z'],ab.inputs[0]); nt.links.new(ab.outputs[0],em.inputs[0]); nt.links.new(em.outputs[0],out.inputs[0])
for o in obs: o.data.materials.clear(); o.data.materials.append(m)
sc.cycles.pixel_filter_type='BOX'; sc.cycles.filter_width=0.01; sc.render.film_transparent=True; sc.view_settings.view_transform='Raw'
sc.render.image_settings.file_format='OPEN_EXR'; sc.render.image_settings.color_depth='32'
for k in ['r1','r2','r3','r4']:
    geom.set_camera(k); sc.render.filepath=os.path.abspath('bake/depth_%s.exr'%k); bpy.ops.render.render(write_still=True)
