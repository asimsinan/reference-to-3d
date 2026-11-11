# blender -b -P irr.py -- PASS : irradiance per texel under light.json (pass 1: grey albedo, pass 2: tex/<part>_alb.png)
import bpy, sys, os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); os.chdir(HERE)
import geom, rig
PASS=int(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else 1
geom.clear(); obs=geom.build_all(); rig.gpu(); rig.light(HERE)
sc=bpy.context.scene; sc.cycles.samples=96; sc.cycles.use_denoising=False
names=open('bake/names.txt').read().split(); imgs={}
SIZE={'shaft':1024,'roof':1024,'arcade':1024,'upper':1024}
for o in obs:
    m=bpy.data.materials.new('irr'); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
    d=nt.nodes.new('ShaderNodeBsdfDiffuse'); out=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(d.outputs[0],out.inputs[0])
    d.inputs[0].default_value=(0.5,0.5,0.5,1) if o.name!='railing' else (0.02,0.02,0.02,1)
    p=os.path.abspath('tex/%s_alb.png'%o.name)
    if PASS>1 and os.path.exists(p):
        t=nt.nodes.new('ShaderNodeTexImage'); t.image=bpy.data.images.load(p); nt.links.new(t.outputs[0],d.inputs[0])
    if o.name in names:
        sz=SIZE.get(o.name,512)
        img=bpy.data.images.new(o.name+'_irr',sz,sz,float_buffer=True,alpha=True); img.colorspace_settings.name='Non-Color'
        tn=nt.nodes.new('ShaderNodeTexImage'); tn.image=img; nt.nodes.active=tn; imgs[o.name]=img
    o.data.materials.clear(); o.data.materials.append(m)
bk=sc.render.bake; bk.use_pass_direct=True; bk.use_pass_indirect=True; bk.use_pass_color=False; bk.margin=4
for n in names:
    o=bpy.data.objects[n]
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active=o
    bpy.ops.object.bake(type='DIFFUSE',pass_filter={'DIRECT','INDIRECT'},use_clear=True)
    imgs[n].filepath_raw=os.path.abspath('tex/%s_irr.exr'%n); imgs[n].file_format='OPEN_EXR'; imgs[n].save(); print('irr',n)
