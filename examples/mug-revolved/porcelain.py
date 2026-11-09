"""Real porcelain instead of the photo's light. usage: Blender -b final/kupa.blend -P porcelain.py -- OUTDIR
Glossy glaze (roughness 0.07) with the photo's detail baked into the base colour maps (pbr_maps.py), an unglazed
matte foot, a bright interior HDRI and soft area lights, Cycles. Writes kupa_porselen.blend/.glb and renders.
Exposure was set by measuring, not by eye: with interior.exr at 1.0 and the lights the first render was all white.
--photo-only renders the photo's camera only; compare body boxes (left, middle, right) with the photo and set
EXPO (AgX, -1.6 here) and the key/fill ratio until each is within a few levels. env SPP (samples), WORLD."""
import bpy, math, os, sys
from mathutils import Vector, Euler
HERE=os.getcwd()   # alb_*.png are in the working folder
OUT=os.path.abspath(sys.argv[sys.argv.index('--')+1]); os.makedirs(OUT,exist_ok=True)
sc=bpy.context.scene
def img(n):
    im=bpy.data.images.load(f'{HERE}/{n}'); return im
def glaze(m,image,rough=0.07,coat=0.0):
    nt=m.node_tree; n=nt.nodes; L=nt.links
    for x in list(n): n.remove(x)
    o=n.new('ShaderNodeOutputMaterial'); o.location=(500,0)
    b=n.new('ShaderNodeBsdfPrincipled'); b.location=(150,0)
    b.inputs['Roughness'].default_value=rough; b.inputs['IOR'].default_value=1.52
    b.inputs['Specular IOR Level'].default_value=0.5; b.inputs['Emission Strength'].default_value=0.0
    if isinstance(image,tuple): b.inputs['Base Color'].default_value=(*image,1)
    else:
        t=n.new('ShaderNodeTexImage'); t.image=image; t.extension='EXTEND'; t.location=(-300,0)
        L.new(t.outputs[0],b.inputs['Base Color'])
    L.new(b.outputs[0],o.inputs[0])
M=bpy.data.materials
glaze(M['glaze_photo'],img('alb_body.png')); M['glaze_photo'].name='porcelain_glaze'
glaze(M['glaze_photo_back'],img('alb_back.png')); M['glaze_photo_back'].name='porcelain_glaze_back'
glaze(M['glaze_inside_photo'],img('alb_inside.png')); M['glaze_inside_photo'].name='porcelain_glaze_inside'
glaze(M['handle_photo'],img('alb_handle.png')); M['handle_photo'].name='porcelain_glaze_handle'
glaze(M['unglazed_foot'],(0.80,0.76,0.69),rough=0.65); M['unglazed_foot'].name='porcelain_unglazed_foot'
for nm in ('glaze_inside','handle_glaze'):
    if nm in M: M.remove(M[nm])
# table: light wood tone, satin
tb=M['table']; b=tb.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value=(0.52,0.34,0.18,1); b.inputs['Roughness'].default_value=0.45
b.inputs['Emission Strength'].default_value=0.0
bpy.data.objects['table'].scale=(1.6,1.6,1)
# world: Blender's interior HDRI (soft window light, something for the glaze to reflect)
w=sc.world; nt=w.node_tree; n=nt.nodes
for x in list(n): n.remove(x)
env=n.new('ShaderNodeTexEnvironment'); env.image=bpy.data.images.load(
    os.path.join(bpy.utils.system_resource('DATAFILES'),'studiolights','world','interior.exr'))
mp=n.new('ShaderNodeMapping'); tc=n.new('ShaderNodeTexCoord'); mp.inputs['Rotation'].default_value=(0,0,math.radians(200))
bg=n.new('ShaderNodeBackground'); bg.inputs[1].default_value=1.0; o=n.new('ShaderNodeOutputWorld')
nt.links.new(tc.outputs['Generated'],mp.inputs[0]); nt.links.new(mp.outputs[0],env.inputs[0])
nt.links.new(env.outputs[0],bg.inputs[0]); nt.links.new(bg.outputs[0],o.inputs[0])
# lights: the photo's key came from the left (the mug's right, -Y); a big soft key, a fill, a top rim
L={o.name:o for o in bpy.data.objects if o.type=='LIGHT'}
def setl(nm,loc,energy,size):
    o=L[nm]; o.location=loc; o.data.energy=energy; o.data.size=size
    o.rotation_euler=(Vector((0,0,0.06))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
setl('key',(0.25,-0.45,0.35),26,0.5); setl('fill',(0.45,0.35,0.2),1.5,0.6); setl('rim',(-0.35,0.15,0.45),8,0.4)
sc.render.engine='CYCLES'; sc.cycles.samples=int(os.environ.get('SPP','160')); sc.cycles.use_denoising=True
try: sc.cycles.device='GPU'
except Exception: pass
sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'
sc.render.film_transparent=False
sc.view_settings.exposure=float(os.environ.get('EXPO','-1.6')); bg.inputs[1].default_value=float(os.environ.get('WORLD','0.7'))
cam=bpy.data.objects['photo_cam']
def shot(name,az,el,dist=0.42,lens=50,res=900,t=(0,0.01,0.058)):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector(t)
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=sc.render.resolution_y=res; sc.render.filepath=f'{OUT}/p_{name}.png'
    bpy.ops.render.render(write_still=True); bpy.data.objects.remove(c); bpy.data.cameras.remove(cd)
if '--photo-only' in sys.argv:
    sc.camera=cam; sc.render.resolution_x=750; sc.render.resolution_y=1000; sc.render.filepath=f'{OUT}/p_photo_cam.png'
    bpy.ops.render.render(write_still=True); sys.exit(0)
if '--no-render' not in sys.argv:
    sc.camera=cam; sc.render.resolution_x=750; sc.render.resolution_y=1000; sc.render.filepath=f'{OUT}/p_photo_cam.png'
    bpy.ops.render.render(write_still=True)
    shot('front',0,10); shot('q_front_right',50,22); shot('q_rear_left',-130,25); shot('top',20,65)
    shot('handle_close',70,20,dist=0.2)
sc.camera=cam; sc.render.resolution_x=1500; sc.render.resolution_y=2000
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type=='VIEW_3D':
                sp.shading.type='MATERIAL'; sp.shading.studio_light='interior.exr'
                sp.shading.use_scene_world=False; sp.shading.studiolight_intensity=1.2
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/kupa_porselen.blend')
bpy.ops.object.select_all(action='DESELECT')
for nm in ('mug_body','mug_handle'): bpy.data.objects[nm].select_set(True)
bpy.ops.export_scene.gltf(filepath=f'{OUT}/kupa_porselen.glb',use_selection=True,export_format='GLB')
