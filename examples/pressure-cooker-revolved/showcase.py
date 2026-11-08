"""Showcase renders of the steel version: the three views in docs/showcase/pressure-cooker.jpg.
usage: Blender -b steel/pressure_cooker_steel.blend -P showcase.py -- show      (then tile show_a/b/c.png)

steel.py's cards sit in front, for the photo's low camera. Seen from 20-25 deg above, polished steel mirrors the
floor, not the cards: a white floor made the body flat white, a floor dark in reflections made it black. What reads
as steel from any side: the floor white to the camera but, in glossy rays, light with dark sectors round the pot
(sin of 5x the angle), which a cylinder shows as vertical dark bands; plus a ring of tall black cards for the upper
part. Both are invisible to the camera."""
import bpy, bmesh, math, sys, os
from mathutils import Vector
OUT=sys.argv[sys.argv.index('--')+1]; sc=bpy.context.scene
for o in list(sc.objects):
    if o.name.startswith('card_'): bpy.data.objects.remove(o)
blk=bpy.data.materials['card_black']; studio=bpy.data.collections['studio']
for i in range(7):
    a=math.radians(i*360/7+20); nm=f'card_ring{i}'
    me=bpy.data.meshes.new(nm); bm=bmesh.new(); bmesh.ops.create_grid(bm,x_segments=1,y_segments=1,size=0.5); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(nm,me); studio.objects.link(o); me.materials.append(blk)
    o.scale=(0.28,1.8,1); o.location=(math.cos(a)*0.9,math.sin(a)*0.9,0.45)
    o.rotation_euler=(Vector((0,0,0.45))-o.location).to_track_quat('Z','Y').to_euler()
    o.visible_camera=False; o.visible_shadow=False; o.visible_diffuse=False
# the floor: white to the camera, dark in reflections (steel seen from above mirrors the floor)
fm=bpy.data.materials['floor']; nt=fm.node_tree; outn=nt.nodes['Material Output']; wb=nt.nodes['Principled BSDF']
db=nt.nodes.new('ShaderNodeEmission')   # what reflections see: light floor with dark sectors round the pot
tc=nt.nodes.new('ShaderNodeTexCoord'); sp=nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'],sp.inputs[0])
at=nt.nodes.new('ShaderNodeMath'); at.operation='ARCTAN2'; nt.links.new(sp.outputs['Y'],at.inputs[0]); nt.links.new(sp.outputs['X'],at.inputs[1])
mu=nt.nodes.new('ShaderNodeMath'); mu.operation='MULTIPLY_ADD'; mu.inputs[1].default_value=5; mu.inputs[2].default_value=0.7; nt.links.new(at.outputs[0],mu.inputs[0])
si=nt.nodes.new('ShaderNodeMath'); si.operation='SINE'; nt.links.new(mu.outputs[0],si.inputs[0])
mr=nt.nodes.new('ShaderNodeMapRange'); mr.interpolation_type='SMOOTHSTEP'; mr.inputs['From Min'].default_value=0.35; mr.inputs['From Max'].default_value=0.7
nt.links.new(si.outputs[0],mr.inputs['Value'])
cr=nt.nodes.new('ShaderNodeMix'); cr.data_type='RGBA'; cr.inputs['A'].default_value=(0.75,0.75,0.77,1); cr.inputs['B'].default_value=(0.02,0.02,0.025,1)
nt.links.new(mr.outputs[0],cr.inputs['Factor']); nt.links.new(cr.outputs['Result'],db.inputs['Color'])
lp=nt.nodes.new('ShaderNodeLightPath'); mx=nt.nodes.new('ShaderNodeMixShader')
nt.links.new(lp.outputs['Is Glossy Ray'],mx.inputs[0]); nt.links.new(wb.outputs[0],mx.inputs[1]); nt.links.new(db.outputs[0],mx.inputs[2])
nt.links.new(mx.outputs[0],outn.inputs[0])
sc.world.node_tree.nodes['Background'].inputs[1].default_value=0.85
sc.cycles.samples=160
def shot(name,az,el,dist=1.15,lens=50,t=(0,0.04,0.12)):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector(t)
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=sc.render.resolution_y=900; sc.render.filepath=f'{OUT}/show_{name}.png'
    bpy.ops.render.render(write_still=True)
shot('a',35,20,dist=0.95); shot('b',-140,24,dist=0.95); shot('c',70,22,dist=0.55,t=(0,0.08,0.15))
