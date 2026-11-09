"""Real materials on the fitted model: black painted wire and rings, steel for the scissors/spoon/file, the pens keep
the photo's printing as base colour (no emission). Cycles renders, kalemlik_pbr.blend, kalemlik_pbr.glb.
usage: Blender -b final/kalemlik.blend -P scripts/pbr.py -- OUTDIR"""
import bpy, math, sys, os
from mathutils import Vector
argv=sys.argv[sys.argv.index('--')+1:]; OUT=os.path.abspath(argv[0]); os.makedirs(OUT,exist_ok=True)
sc=bpy.context.scene
def principled(m): return m.node_tree.nodes['Principled BSDF']
def set_flat(m,col,rough,metal=0.0):
    b=principled(m); nt=m.node_tree
    for inp in ('Base Color','Emission Color'):
        if b.inputs[inp].links: nt.links.remove(b.inputs[inp].links[0])
    b.inputs['Base Color'].default_value=(*col,1); b.inputs['Roughness'].default_value=rough
    b.inputs['Metallic'].default_value=metal; b.inputs['Emission Strength'].default_value=0.0
    b.inputs['Specular IOR Level'].default_value=0.5
STEEL_NAMES={'scissors_ring','scissors_ring2','scissors_blades','spoon_bowl','spoon_handle','nail_file','nail_file_tip'}
steel=bpy.data.materials.new('steel'); steel.use_nodes=True; set_flat(steel,(0.75,0.75,0.77),0.18,1.0)
for m in bpy.data.materials:
    if not m.use_nodes or 'Principled BSDF' not in m.node_tree.nodes: continue
    b=principled(m); b.inputs['Emission Strength'].default_value=0.0
    if m.name=='wire_lattice': set_flat(m,(0.012,0.012,0.012),0.45,0.5)          # black painted steel, alpha stays
    elif m.name=='rim_photo': set_flat(m,(0.01,0.01,0.01),0.28,0.3)             # the black rings (coated wire)
    elif m.name=='metal_black': set_flat(m,(0.012,0.012,0.012),0.6,0.4)
    elif m.name=='contents_photo': b.inputs['Roughness'].default_value=0.32; b.inputs['Specular IOR Level'].default_value=0.5
    elif m.name.endswith('_cap'): b.inputs['Roughness'].default_value=0.35
    elif m.name=='table': b.inputs['Roughness'].default_value=0.75
for o in bpy.data.objects:
    if o.name in STEEL_NAMES:
        o.data.materials.clear(); o.data.materials.append(steel)
# world: an interior HDRI + the area lights
hdr=None
for root in (os.path.dirname(bpy.app.binary_path)+'/../Resources',):
    for dp,dn,fn in os.walk(root):
        if 'interior.exr' in fn: hdr=os.path.join(dp,'interior.exr'); break
w=sc.world; nt=w.node_tree; bg=nt.nodes['Background']
if hdr:
    env=nt.nodes.new('ShaderNodeTexEnvironment'); env.image=bpy.data.images.load(hdr); nt.links.new(env.outputs[0],bg.inputs[0])
    mp=nt.nodes.new('ShaderNodeMapping'); tc=nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Generated'],mp.inputs[0]); nt.links.new(mp.outputs[0],env.inputs[0])
    mp.inputs['Rotation'].default_value=(0,0,math.radians(140))
bg.inputs[1].default_value=0.7
for o in bpy.data.objects:
    if o.type=='LIGHT': o.data.energy*=0.6
sc.render.engine='CYCLES'; sc.cycles.samples=96; sc.cycles.use_denoising=True; sc.view_settings.view_transform='AgX'; sc.view_settings.exposure=0.0
try: sc.cycles.device='GPU'
except Exception: pass
def shot(name,az,el,dist=0.36,lens=50,res=900):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector((0,0,0.07))
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=sc.render.resolution_y=res; sc.render.film_transparent=False
    sc.render.filepath=f'{OUT}/pbr_{name}.png'; bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(c); bpy.data.cameras.remove(cd)
shot('front',0,12); shot('q_right',50,22); shot('q_rear',-135,28); shot('top',30,70); shot('close',20,15,dist=0.22); shot('right',90,12)
sc.camera=bpy.data.objects['photo_cam']
model=[o for o in bpy.data.objects if o.type=='MESH' and o.name!='table']
bpy.ops.object.select_all(action='DESELECT')
for o in model: o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['mesh_wall']
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/kalemlik_pbr.blend')
bpy.ops.export_scene.gltf(filepath=f'{OUT}/kalemlik_pbr.glb',use_selection=True,export_format='GLB')
print('done', hdr)
