# blender -b -P render.py -- MODE [frames]  MODE=photo: emission of tex/<part>_photo.png (exposure per frame from gain.json) -> out/photo_rN.png
import bpy, sys, os, json
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); os.chdir(HERE)
import geom
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['photo']
MODE=argv[0]; FR=argv[1:] or ['r2','r3','r4']
GAIN=json.load(open('gain.json'))
geom.clear(); obs=geom.build_all()
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=16; sc.cycles.filter_width=1.0; sc.cycles.use_denoising=False
sc.render.film_transparent=False; sc.view_settings.view_transform='Standard'
w=bpy.data.worlds.new('W'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0,0,0,1)
names=open('bake/names.txt').read().split()
mats={}
for o in obs:
    m=bpy.data.materials.new('m_'+o.name); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
    em=nt.nodes.new('ShaderNodeEmission'); out=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0],out.inputs[0])
    if o.name in names:
        t=nt.nodes.new('ShaderNodeTexImage'); t.image=bpy.data.images.load(os.path.abspath('tex/%s_photo.png'%o.name)); t.interpolation='Cubic'
        g=nt.nodes.new('ShaderNodeMixRGB'); g.blend_type='MULTIPLY'; g.inputs[0].default_value=1.0
        nt.links.new(t.outputs[0],g.inputs[1]); nt.links.new(g.outputs[0],em.inputs[0]); mats[o.name]=g
    else:
        em.inputs[0].default_value=(0.003,0.003,0.0035,1)
    o.data.materials.clear(); o.data.materials.append(m)
os.makedirs('out',exist_ok=True)
for k in FR:
    gk=GAIN.get(k,[1,1,1])
    for g in mats.values(): g.inputs[2].default_value=((1/gk[2])**2.2,(1/gk[1])**2.2,(1/gk[0])**2.2,1)   # gain.json is BGR
    geom.set_camera(k); sc.render.filepath=os.path.abspath('out/%s_%s.png'%(MODE,k)); bpy.ops.render.render(write_still=True)
