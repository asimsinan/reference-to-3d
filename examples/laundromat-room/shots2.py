import bpy, os, sys
from mathutils import Vector
D=os.path.dirname(bpy.data.filepath); out=os.path.join(D,'renders2'); os.makedirs(out,exist_ok=True)
sc=bpy.context.scene; base=sc.camera
V={'cam':None,
 'walk':((0.3,2.2,1.55),(0.9,7.0,1.1),20,()),
 'cart':((-0.2,2.6,1.2),(0.75,3.95,0.5),28,()),
 'bench':((0.6,1.0,1.1),(-0.6,2.6,0.5),24,()),
 'washers':((0.2,1.2,1.0),(1.6,3.0,0.7),22,()),
 'stools':((0.9,4.3,1.3),(-0.1,6.3,0.5),26,()),
 'eye_left':((0,0,1.375),(-3,0.6,1.1),18,()),
 'eye_right':((0,0,1.375),(3,0.6,1.0),18,()),
 'eye_back':((0,0,1.375),(0.3,-3,1.0),18,()),
 'eye_down':((0,0,1.375),(0.2,1.2,0),18,()),
 'entrance':((0.4,-0.9,1.6),(0.5,6.0,0.9),18,()),
 'from_back':((0.3,6.2,1.6),(0.2,-1.2,1.0),18,()),
 'over':((-1.0,-1.3,3.9),(0.7,4.2,0.4),16,('Ceiling','Wall_front','Light_near','Light_far'))}
which=sys.argv[sys.argv.index('--')+1].split(',')
for k in which:
    v=V[k]; hide=()
    if v is None: c=base
    else:
        pos,tgt,lens,hide=v; cd=bpy.data.cameras.new(k); c=bpy.data.objects.new(k,cd); sc.collection.objects.link(c)
        c.location=pos; c.rotation_euler=(Vector(tgt)-Vector(pos)).to_track_quat('-Z','Y').to_euler(); cd.lens=lens; cd.clip_start=0.03
    for n in hide: bpy.data.objects[n].hide_render=True
    sc.camera=c; sc.render.filepath=os.path.join(out,k+'.png'); bpy.ops.render.render(write_still=True)
    for n in hide: bpy.data.objects[n].hide_render=False
