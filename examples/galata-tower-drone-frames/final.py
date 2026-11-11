# blender -b -P final.py -- PREFIX [frames] : real materials (albedo textures) under light.json, rendered from the photo cameras
import bpy, sys, os, json
from math import log2
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); os.chdir(HERE)
import geom, rig
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['final']
PRE=argv[0]; FR=argv[1:] or ['r2','r3','r4']
GAIN=json.load(open('gain.json'))
def materials(obs):
    for o in obs:
        m=bpy.data.materials.new('mat_'+o.name); m.use_nodes=True; nt=m.node_tree; b=nt.nodes['Principled BSDF']
        p=os.path.abspath('tex/%s_alb.png'%o.name)
        if os.path.exists(p):
            t=nt.nodes.new('ShaderNodeTexImage'); t.image=bpy.data.images.load(p); t.interpolation='Cubic'; nt.links.new(t.outputs[0],b.inputs['Base Color'])
        if o.name in ('roof','dormers'):
            b.inputs['Roughness'].default_value=0.6; b.inputs['Specular IOR Level'].default_value=0.06
        elif o.name=='finial':
            b.inputs['Metallic'].default_value=0.85; b.inputs['Roughness'].default_value=0.32
        elif o.name=='railing':
            b.inputs['Base Color'].default_value=(0.015,0.015,0.016,1); b.inputs['Roughness'].default_value=0.7; b.inputs['Specular IOR Level'].default_value=0.1
        else:
            b.inputs['Roughness'].default_value=0.9; b.inputs['Specular IOR Level'].default_value=0.08
        o.data.materials.clear(); o.data.materials.append(m)
if __name__=='__main__':
    geom.clear(); obs=geom.build_all(); materials(obs); rig.gpu(); rig.light(HERE)
    sc=bpy.context.scene; sc.cycles.samples=256; sc.cycles.use_denoising=False; sc.cycles.filter_width=1.0; sc.view_settings.view_transform='Standard'
    for k in FR:
        g=GAIN.get(k,[1,1,1]); sc.view_settings.exposure=-2.2*log2(sum(g)/3)
        geom.set_camera(k); sc.render.filepath=os.path.abspath('out/%s_%s.png'%(PRE,k)); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('out/%s_work.blend'%PRE))
