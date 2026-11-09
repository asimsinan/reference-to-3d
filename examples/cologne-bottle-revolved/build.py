"""Blender: the cologne spray bottle from one photo. usage: Blender -b -P build.py -- OUTDIR [--final]
Body (lathe), ribbed collar and cap (lathes, tilted by PHI as the sprayer sits), UVs through the photo's camera with
the angle folded (|phi|<=A the photo, beyond it the print-free back plate mirrored and stretched to the seam)."""
import bpy, bmesh, json, math, sys, os
import numpy as np
from mathutils import Vector, Matrix, Euler
WD=os.getcwd(); sys.path.insert(0,WD)
import cam as C
P=C.P; INFO=json.load(open(f'{WD}/tex_info.json'))
argv=sys.argv[sys.argv.index('--')+1:]; OUT=os.path.abspath(argv[0]); os.makedirs(OUT,exist_ok=True); FINAL='--final' in argv
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
R,rb,rf,h=P['R'],P['rb'],P['rf'],P['h']; rs=0.0015; rn=0.0105
rc0,rc1,zc0,zc1=P['rc0'],P['rc1'],P['zc0'],P['zc1']; rk0,rk1,zk1,KF=P['rk0'],P['rk1'],P['zk1'],P['KF']
RM=Matrix(C.head_rot(0.0 if os.environ.get('STRAIGHT') else P['PHI']).tolist()); NECK=Vector((0,0,h))
def body_profile():
    rg=rb-rf; pts=[(0.0025,0.0,'under'),(0.0025,rg-0.003,'under'),(0.0,rg,'under')]
    for t in np.linspace(0,math.pi/2,9)[1:]: pts.append((rf-rf*math.cos(t), rg+rf*math.sin(t),'out'))
    for z in np.linspace(rf,h-rs,40)[1:]: pts.append((z, rb+(R-rb)*z/h,'out'))
    for t in np.linspace(0,math.pi/2,7)[1:]: pts.append((h-rs+rs*math.sin(t), R-rs+rs*math.cos(t),'out'))
    pts+=[(h,rn,'top'),(zc0+0.003,rn,'neck'),(zc0+0.003,0.0,'neck')]
    return pts
def collar_profile():
    pts=[(zc0,0.0,'cunder'),(zc0,rc0*0.8,'cunder'),(zc0,rc0,'col')]
    for z in np.linspace(zc0,zc1,12)[1:]: pts.append((z,rc0+(rc1-rc0)*(z-zc0)/(zc1-zc0),'col'))
    pts+=[(zc1,rk0+0.0004,'coltop'),(zc1,0.0,'coltop')]
    return pts
def cap_profile():
    z0=zc1-0.0008; pts=[(z0,0.0,'kunder'),(z0,rk0,'cap')]
    for z in np.linspace(z0,zk1-KF,16)[1:]: pts.append((z,rk0+(rk1-rk0)*(z-zc1)/(zk1-zc1),'cap'))
    for t in np.linspace(0,math.pi/2,7)[1:]: pts.append((zk1-KF+KF*math.sin(t), rk1-KF+KF*math.cos(t),'cap'))
    pts.append((zk1,0.0,'captop')); return pts
def lathe(name,prof,SEG,ribs=None,xform=None):
    me=bpy.data.meshes.new(name); bm=bmesh.new(); rings=[]
    for z,r,tg in prof:
        if r==0: rings.append([bm.verts.new((0,0,z))]); continue
        ring=[]
        for i in range(SEG):
            ph=2*math.pi*i/SEG; rr=r
            if ribs and tg==ribs[0]: rr=r+ribs[2]*math.cos(ribs[1]*ph)
            ring.append(bm.verts.new((rr*math.cos(ph),rr*math.sin(ph),z)))
        rings.append(ring)
    tags=[]
    for k,(a,b) in enumerate(zip(rings[:-1],rings[1:])):
        tg=prof[k+1][2] if prof[k][2]!=prof[k+1][2] and len(b)==1 else prof[k][2]
        if prof[k][2]!=prof[k+1][2] and len(a)>1 and len(b)>1 and prof[k][0]==prof[k+1][0]: tg=prof[k+1][2] if prof[k+1][2] in ('top','coltop') else prof[k][2]
        for i in range(SEG):
            j=(i+1)%SEG
            if len(a)==1: f=bm.faces.new((a[0],b[i],b[j]))
            elif len(b)==1: f=bm.faces.new((a[i],a[j],b[0]))
            else: f=bm.faces.new((a[i],a[j],b[j],b[i]))
            tags.append(tg)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    if xform:
        for v in bm.verts: v.co=xform(v.co)
    bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); sc.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth=True
    return ob,tags
tilt=lambda co: RM@(co-NECK)+NECK
BODY,TB=lathe('sise_govde',body_profile(),180)
COL,TC=lathe('sise_bilezik',collar_profile(),192,ribs=('col',48,0.00035),xform=tilt)
CAP,TK=lathe('sise_kapak',cap_profile(),128,xform=tilt)
# ---------- camera ----------
camd=bpy.data.cameras.new('photo_cam'); cam=bpy.data.objects.new('photo_cam',camd); sc.collection.objects.link(cam)
f,r,up=C.axes(P['TH'],P['PSI']); Cc=Vector((P['D'],P['YC'],P['HC']))
cam.matrix_world=Matrix(((r[0],up[0],-f[0],Cc.x),(r[1],up[1],-f[1],Cc.y),(r[2],up[2],-f[2],Cc.z),(0,0,0,1)))
camd.sensor_fit='HORIZONTAL'; camd.sensor_width=36; camd.lens=P['F']/C.W*36
camd.shift_x=-(P['CX']-C.W/2)/C.W; camd.shift_y=(P['CY']-C.H/2)/C.W; camd.clip_start=0.02; camd.clip_end=20
sc.camera=cam; sc.render.resolution_x=C.W; sc.render.resolution_y=C.H
eng=bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys()
sc.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in eng else 'BLENDER_EEVEE'
sc.view_settings.view_transform='Standard'
world=bpy.data.worlds.new('world'); sc.world=world; world.use_nodes=True; BG=world.node_tree.nodes['Background']
def render(path,transparent=True):
    sc.render.film_transparent=transparent; sc.render.image_settings.color_mode='RGBA' if transparent else 'RGB'
    sc.render.filepath=path; bpy.ops.render.render(write_still=True)
# ---------- materials ----------
def img(n): return bpy.data.images.load(f'{WD}/{n}')
def mat(name,image=None,color=None,rough=0.25,emit=0.6,spec=0.4):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; n=nt.nodes; L=nt.links
    for x in list(n): n.remove(x)
    out=n.new('ShaderNodeOutputMaterial'); out.location=(600,0)
    b=n.new('ShaderNodeBsdfPrincipled'); b.location=(200,0)
    b.inputs['Roughness'].default_value=rough; b.inputs['Specular IOR Level'].default_value=spec
    if image:
        t=n.new('ShaderNodeTexImage'); t.image=image; t.location=(-300,0); t.extension='EXTEND'
        L.new(t.outputs[0],b.inputs['Base Color']); L.new(t.outputs[0],b.inputs['Emission Color'])
    else:
        b.inputs['Base Color'].default_value=(*color,1); b.inputs['Emission Color'].default_value=(*color,1)
    b.inputs['Emission Strength'].default_value=emit
    L.new(b.outputs[0],out.inputs[0]); return m
def srgb2lin(c): c=np.asarray(c)/255.0; return tuple(np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4))
IMF=img('tex_front.png'); IMB=img('tex_back.png')
M=dict(body_f=mat('pet_photo',IMF,rough=0.12),body_b=mat('pet_photo_back',IMB,rough=0.12),
       under=mat('pet_bottom',color=srgb2lin(INFO['under_rgb']),rough=0.3,emit=0.5),
       col_f=mat('collar_photo',IMF,rough=0.45,spec=0.3),col_b=mat('collar_photo_back',IMB,rough=0.45,spec=0.3),
       cap_f=mat('cap_photo',IMF,rough=0.2),cap_b=mat('cap_photo_back',IMB,rough=0.2),
       dark=mat('black_plastic',color=(0.02,0.02,0.02),rough=0.5,emit=0.0))
# ---------- UVs: fold the angle ----------
A=math.radians(float(os.environ.get('FOLD','72')))
def fold(phi):
    if abs(phi)<=A: return phi
    return math.copysign(A*(math.pi-abs(phi))/(math.pi-A),phi)
X0,Y0,X1,Y1=INFO['crop']
def uv_of(Xw):
    u,v=C.proj(np.array(Xw,float)[None])[0]; return ((u-X0)/(X1-X0), 1-(v-Y0)/(Y1-Y0))
def assign(ob,tags,mf,mb,munder,tilted):
    me=ob.data
    for m_ in (mf,mb,munder,M['dark']): me.materials.append(m_)
    uvl=me.uv_layers.new(name='photo')
    for p,tg in zip(me.polygons,tags):
        if tg in ('under','cunder','kunder','neck'):
            p.material_index=2 if tg=='under' else 3
            for li in p.loop_indices: uvl.data[li].uv=(0.5,0.5)
            continue
        c=Vector(p.center)
        cl=(RM.inverted()@(c-NECK)+NECK) if tilted else c
        phc=math.atan2(cl.y,cl.x); p.material_index=1 if abs(phc)>A+1e-4 else 0
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            lc=(RM.inverted()@(co-NECK)+NECK) if tilted else Vector(co)
            rho=math.hypot(lc.x,lc.y); fphi=fold(math.atan2(lc.y,lc.x))
            q=Vector((rho*math.cos(fphi),rho*math.sin(fphi),lc.z))
            if tilted: q=RM@(q-NECK)+NECK
            uvl.data[li].uv=uv_of(q)
assign(BODY,TB,M['body_f'],M['body_b'],M['under'],False)
assign(COL,TC,M['col_f'],M['col_b'],M['dark'],True)
assign(CAP,TK,M['cap_f'],M['cap_b'],M['dark'],True)
OBJS=[BODY,COL,CAP]
# ---------- comparison render: emission only ----------
def emission_only(on):
    for m_ in bpy.data.materials:
        b=m_.node_tree.nodes['Principled BSDF']; t=m_.node_tree.nodes.get('Image Texture')
        if on:
            m_['bc']=list(b.inputs['Base Color'].default_value); m_['em']=b.inputs['Emission Strength'].default_value; m_['sp']=b.inputs['Specular IOR Level'].default_value
            if t and b.inputs['Base Color'].links: m_.node_tree.links.remove(b.inputs['Base Color'].links[0])
            b.inputs['Base Color'].default_value=(0,0,0,1); b.inputs['Emission Strength'].default_value=1.0 if (t or m_.name!='black_plastic') else 1.0
            if m_.name=='black_plastic': b.inputs['Emission Color'].default_value=(0.02,0.02,0.02,1)
            b.inputs['Specular IOR Level'].default_value=0.0
        else:
            if t: m_.node_tree.links.new(t.outputs[0],b.inputs['Base Color'])
            else: b.inputs['Base Color'].default_value=m_['bc']
            b.inputs['Emission Strength'].default_value=m_['em']; b.inputs['Specular IOR Level'].default_value=m_['sp']
BG.inputs[1].default_value=0.0
emission_only(True); render(f'{OUT}/photo_view.png'); emission_only(False)
# ---------- lit scene, other views ----------
BG.inputs[0].default_value=(0.6,0.6,0.62,1); BG.inputs[1].default_value=0.35
def light(name,loc,energy,size):
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.size=size
    o=bpy.data.objects.new(name,ld); o.location=loc; sc.collection.objects.link(o)
    o.rotation_euler=(Vector((0,0,0.07))-o.location).to_track_quat('-Z','Y').to_euler(); return o
LIGHTS=[light('key',(0.4,-0.35,0.5),6,0.4),light('fill',(0.3,0.5,0.3),2.5,0.5),light('rim',(-0.45,0.1,0.45),3,0.4)]
fme=bpy.data.meshes.new('floor'); bm=bmesh.new(); bmesh.ops.create_grid(bm,x_segments=1,y_segments=1,size=0.25)
bm.to_mesh(fme); bm.free(); floor=bpy.data.objects.new('masa',fme); sc.collection.objects.link(floor)
floor.data.materials.append(mat('masa',color=srgb2lin((196,176,146)),rough=0.6,emit=0.0))
def shot(name,az,el,dist=0.36,lens=85,res=900,target=(0,0,0.068)):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector(target)
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=sc.render.resolution_y=res; render(f'{OUT}/view_{name}.png',transparent=False)
    bpy.data.objects.remove(c); bpy.data.cameras.remove(cd)
shot('front',0,8); shot('q_front_right',45,18); shot('side',90,10); shot('q_rear',-135,22); shot('rear',180,8); shot('top',30,65)
shot('close_label',15,5,dist=0.2,target=(0,0,0.045)); shot('close_cap',40,20,dist=0.15,target=(0,0,0.115)); shot('close_shoulder',-60,15,dist=0.15,target=(0,0,0.085)); shot('close_base',120,12,dist=0.16,target=(0,0,0.012))
sc.camera=cam; sc.render.resolution_x=C.W; sc.render.resolution_y=C.H
if FINAL:
    colM=bpy.data.collections.new('kolonya'); colS=bpy.data.collections.new('studio')
    sc.collection.children.link(colM); sc.collection.children.link(colS)
    root=bpy.data.objects.new('Kolonya',None); colM.objects.link(root)
    for o in OBJS: sc.collection.objects.unlink(o); colM.objects.link(o); o.parent=root
    for o in LIGHTS+[floor,cam]: sc.collection.objects.unlink(o); colS.objects.link(o)
    camd.display_size=0.02
    for scr in bpy.data.screens:
        for ar in scr.areas:
            for sp in ar.spaces:
                if sp.type=='VIEW_3D':
                    sp.shading.type='MATERIAL'; sp.overlay.show_extras=False; sp.clip_start=0.001
                    r3=sp.region_3d; r3.view_perspective='PERSP'; r3.view_location=(0,0,0.07); r3.view_distance=0.38
                    r3.view_rotation=Euler((math.radians(78),0,math.radians(60))).to_quaternion()
    bpy.ops.object.select_all(action='DESELECT')
    for o in OBJS: o.select_set(True)
    bpy.context.view_layer.objects.active=BODY
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/kolonya.blend')
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/kolonya.glb',use_selection=True,export_format='GLB')
print('verts:',{o.name:len(o.data.vertices) for o in OBJS})
