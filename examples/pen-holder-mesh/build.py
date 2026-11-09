"""Blender: the mesh pen holder and its contents from one photo.
usage: Blender -b -P scripts/build.py -- OUTDIR [--final]
Frame: +X front (towards the camera), +Y image-right, +Z up, metres, base centre at origin."""
import bpy, bmesh, json, math, sys, os
import numpy as np
from mathutils import Vector, Matrix, Euler
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import cam as C
P=C.P; WD=os.getcwd()
argv=sys.argv[sys.argv.index('--')+1:]; OUT=os.path.abspath(argv[0]); os.makedirs(OUT,exist_ok=True); FINAL='--final' in argv
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
info=json.load(open(f'{WD}/tex_info.json'))
RW=P['rw']; HT=P['h']; RB=P['rb']; RR=P['R']; Z0=0.004          # wall radius, height, base ring radius, rim radius, base plate top
Cc=np.array([P['D'],P['YC'],P['HC']])
# ---------------- helpers ----------------
def new_obj(name,verts,faces,smooth=True):
    me=bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts],[],[tuple(f) for f in faces]); me.update()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth=smooth
    ob=bpy.data.objects.new(name,me); sc.collection.objects.link(ob); return ob
def lathe(name,prof,seg=160,axis_from=None,axis_to=None):
    """prof: list of (r,z); revolved about Z. r=0 rows become poles."""
    V=[];F=[];rings=[]
    for r,z in prof:
        if r<1e-7: rings.append([len(V)]); V.append((0,0,z)); continue
        rings.append(list(range(len(V),len(V)+seg)))
        V+=[(r*math.cos(2*math.pi*i/seg),r*math.sin(2*math.pi*i/seg),z) for i in range(seg)]
    for a,b in zip(rings[:-1],rings[1:]):
        for i in range(seg):
            j=(i+1)%seg
            if len(a)==1: F.append((a[0],b[j],b[i]))
            elif len(b)==1: F.append((a[i],a[j],b[0]))
            else: F.append((a[i],a[j],b[j],b[i]))
    ob=new_obj(name,V,F)
    if axis_from is not None: place_axis(ob,axis_from,axis_to)
    return ob
def place_axis(ob,B,T):
    B=Vector(B); T=Vector(T); d=(T-B).normalized()
    q=Vector((0,0,1)).rotation_difference(d); ob.matrix_world=Matrix.Translation(B)@q.to_matrix().to_4x4()
def torus(name,R0,r0,z0,seg=160,tseg=24,ell=None,mat=None):
    V=[];F=[]
    for i in range(seg):
        a=2*math.pi*i/seg; ca,sa=math.cos(a),math.sin(a)
        for j in range(tseg):
            b=2*math.pi*j/tseg; rr=R0+r0*math.cos(b)
            V.append((rr*ca,rr*sa,z0+r0*math.sin(b)))
    for i in range(seg):
        for j in range(tseg):
            F.append((i*tseg+j,((i+1)%seg)*tseg+j,((i+1)%seg)*tseg+(j+1)%tseg,i*tseg+(j+1)%tseg))
    return new_obj(name,V,F)
def ell_ring(name,ay,az,r0,seg=96,tseg=20):
    """elliptical ring in the local YZ plane (semi-axes ay, az), tube radius r0, centred at origin"""
    V=[];F=[]
    for i in range(seg):
        a=2*math.pi*i/seg; c=Vector((0,ay*math.cos(a),az*math.sin(a)))
        t=Vector((0,-ay*math.sin(a),az*math.cos(a))).normalized(); n=Vector((0,0,0)); nx=Vector((1,0,0)); ny=nx.cross(t)
        for j in range(tseg):
            b=2*math.pi*j/tseg; V.append(tuple(c+r0*(math.cos(b)*nx+math.sin(b)*ny)))
    for i in range(seg):
        for j in range(tseg):
            F.append((i*tseg+j,((i+1)%seg)*tseg+j,((i+1)%seg)*tseg+(j+1)%tseg,i*tseg+(j+1)%tseg))
    return new_obj(name,V,F)
def box(name,sx,sy,sz,taper=None):
    """box centred in x,y, z from 0..sz; taper: (sx_top,sy_top)"""
    tx,ty=(taper or (sx,sy))
    V=[(-sx/2,-sy/2,0),(sx/2,-sy/2,0),(sx/2,sy/2,0),(-sx/2,sy/2,0),(-tx/2,-ty/2,sz),(tx/2,-ty/2,sz),(tx/2,ty/2,sz),(-tx/2,ty/2,sz)]
    F=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return new_obj(name,V,F,smooth=False)
def on_base(uv,z=Z0):
    """pixel -> point on the plane z (where an item stands)"""
    Cm,d=C.ray(np.array([uv[0]],float),np.array([uv[1]],float)); t=(z-Cm[2])/d[0,2]; return Cm+t*d[0]
def along_ray(uv,B,L,prefer_front=True):
    """point on the pixel's ray at distance L from B (the nearer-to-vertical root)"""
    Cm,d=C.ray(np.array([uv[0]],float),np.array([uv[1]],float)); d=d[0]; q=Cm-B
    b=2*q@d; c=q@q-L*L; disc=b*b-4*c
    if disc<0: t=-b/2; print('  ! top ray never reaches length %.3f, nearest used'%L)
    else:
        ts=[(-b-math.sqrt(disc))/2,(-b+math.sqrt(disc))/2]
        t=min(ts,key=lambda tt: np.hypot(*(Cm+tt*d-B)[:2]))
    return Cm+t*d
def at_depth(uv,x):
    Cm,d=C.ray(np.array([uv[0]],float),np.array([uv[1]],float)); t=(x-Cm[0])/d[0,0]; return Cm+t*d[0]
# ---------------- materials ----------------
def img(n): return bpy.data.images.load(f'{WD}/{n}')
IMG_PHOTO=img('rim_tex.png'); IMG_CONT=img('contents_tex.png'); IMG_LAT=img('lattice_tile.png'); IMG_WALL=img('wall_tex.png')
def srgb2lin(c): c=np.asarray(c)/255.0; return tuple(np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4))
def mat(name,image=None,color=None,rough=0.35,metal=0.0,emit=0.6,alpha_img=None):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; n=nt.nodes; L=nt.links
    for x in list(n): n.remove(x)
    out=n.new('ShaderNodeOutputMaterial'); out.location=(600,0)
    b=n.new('ShaderNodeBsdfPrincipled'); b.location=(200,0)
    b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal; b.inputs['Specular IOR Level'].default_value=0.4
    if image:
        t=n.new('ShaderNodeTexImage'); t.image=image; t.location=(-300,0); t.extension='EXTEND'; t.name='Image Texture'
        L.new(t.outputs[0],b.inputs['Base Color']); L.new(t.outputs[0],b.inputs['Emission Color'])
    elif color:
        b.inputs['Base Color'].default_value=(*color,1); b.inputs['Emission Color'].default_value=(*color,1)
    b.inputs['Emission Strength'].default_value=emit
    if alpha_img:   # the image's own alpha, clipped (glTF: alphaMode MASK)
        t=n['Image Texture']; g=n.new('ShaderNodeMath'); g.operation='GREATER_THAN'; g.inputs[1].default_value=0.5; g.location=(-50,-300)
        L.new(t.outputs[1],g.inputs[0]); L.new(g.outputs[0],b.inputs['Alpha'])
        m.surface_render_method='DITHERED'; m.use_backface_culling=False
    L.new(b.outputs[0],out.inputs[0]); return m
M_RING=mat('rim_photo',IMG_PHOTO,rough=0.3)
M_DARK=mat('metal_black',color=srgb2lin(info['wire_rgb']),rough=0.45,metal=0.4,emit=0.4)
M_LAT=mat('wire_lattice',IMG_WALL,rough=0.45,metal=0.4,emit=0.6,alpha_img='same')
M_CONT=mat('contents_photo',IMG_CONT,rough=0.3)
M_SILVER=M_CONT
# ---------------- UV projection through the photo camera ----------------
_CT=np.array(IMG_CONT.pixels[:],np.float32).reshape(IMG_CONT.size[1],IMG_CONT.size[0],4)[::-1,:,:3]*255   # rows top-down, sRGB
def plain_top_material(ob,top_uv):
    u,v=int(top_uv[0]),int(top_uv[1]); px=_CT[max(v-4,0):v+40,max(u-6,0):u+6].reshape(-1,3)
    col=np.median(px,0); m=mat(ob.name+'_cap',color=srgb2lin(col),rough=0.35)
    ob.data.materials.append(m); k=len(ob.data.materials)-1; M=ob.matrix_world.to_3x3()
    for p in ob.data.polygons:
        n=M@p.normal
        if abs(n.z)>0.55: p.material_index=k
def uv_project(ob,mirror_x=None,fold=None):
    """each loop's UV = photo pixel of the vertex; faces turned from the camera take the mirror about the plane
    x=mirror_x (an item's own axis plane); fold: body of revolution about Z, angle folded (as the mug's body)"""
    me=ob.data; uvl=me.uv_layers.new(name='photo'); M=ob.matrix_world
    for p in me.polygons:
        c=np.array(M@p.center); n=np.array(M.to_3x3()@p.normal); toc=Cc-c; toc/=np.linalg.norm(toc)
        mir=(mirror_x is not None) and (np.array([-n[0],n[1],n[2]])@toc > n@toc)
        for li in p.loop_indices:
            co=np.array(M@me.vertices[me.loops[li].vertex_index].co)
            if fold is not None:
                rho=math.hypot(co[0],co[1]); ph=math.atan2(co[1],co[0]); A=fold
                if abs(ph)>A: ph=math.copysign(A*(math.pi-abs(ph))/(math.pi-A),ph)
                co=np.array([rho*math.cos(ph),rho*math.sin(ph),co[2]])
            elif mir: co=np.array([2*mirror_x-co[0],co[1],co[2]])
            u,v=C.proj(co); uvl.data[li].uv=(u/C.W,1-v/C.H)
# ---------------- the holder ----------------
HOLDER=[]
rt=0.0026                                   # rim tube radius (the ring is ~5 mm thick)
top_ring=torus('rim_ring',RR-rt,rt,HT-rt); top_ring.data.materials.append(M_RING); uv_project(top_ring,fold=math.radians(72)); HOLDER.append(top_ring)
rbt=0.0024
# the solved base circle is the ring's lowest contour seen from elevation e: z = zc - rbt cos e, r = Rc + rbt sin e
e_b=math.atan2(P['HC'],P['D']); base_ring=torus('base_ring',RB-rbt*math.sin(e_b),rbt,P['zb']+rbt*math.cos(e_b)); base_ring.data.materials.append(M_RING); uv_project(base_ring,fold=math.radians(72)); HOLDER.append(base_ring)
# wall: one surface, lattice alpha; UV u = cells around, v = cells up
NA=int(round(2*math.pi*RW/info['cell_a'])); zw0,zw1=P['zb']+rbt*math.cos(e_b),HT-rt
wall=lathe('mesh_wall',[(RW,zw0),(RW,zw1)],seg=240); wall.data.materials.append(M_LAT)
uvl=wall.data.uv_layers.new(name='wall'); me=wall.data
for p in me.polygons:
    base_u=None
    for li in p.loop_indices:
        co=me.vertices[me.loops[li].vertex_index].co; ph=(math.atan2(co.y,co.x)+math.pi)/(2*math.pi)   # seam at the back
        if base_u is None: base_u=ph
        if ph<base_u-0.5: ph+=1
        if ph>base_u+0.5: ph-=1
        uvl.data[li].uv=(ph,(co.z-zw0)/(zw1-zw0))
HOLDER.append(wall)
plate=lathe('base_plate',[(0,Z0-0.0012),(RW,Z0-0.0012),(RW,Z0),(0,Z0)]); plate.data.materials.append(M_DARK); HOLDER.append(plate)
print('holder: rim R %.4f h %.4f wall r %.4f base r %.4f, %d cells around'%(RR,HT,RW,RB,NA))
# ---------------- the contents ----------------
ITEMS=[]
def pen(name,top,bottom,r,rcap=None,cap=0.0,dx=0.0):
    B=on_base(bottom); T=at_depth(top,B[0]+dx); L=float(np.linalg.norm(T-B)); d=(T-B)/L
    prof=[(0,0),(r*0.6,0),(r,r*0.4)]
    if cap>0:
        prof+=[(r,L-cap),(rcap,L-cap),(rcap,L-rcap)]
        for k in range(1,7): a=math.pi/2*k/6; prof.append((rcap*math.cos(a),L-rcap+rcap*math.sin(a)))
    else:
        prof+=[(r,L-r)]
        for k in range(1,7): a=math.pi/2*k/6; prof.append((r*math.cos(a),L-r+r*math.sin(a)))
    ob=lathe(name,prof,seg=48,axis_from=B,axis_to=T); ob.data.materials.append(M_CONT); uv_project(ob,mirror_x=float((B[0]+T[0])/2)); ITEMS.append(ob)
    plain_top_material(ob,top)
    lean=math.degrees(math.acos(d[2])); print('%-14s bottom (%.3f,%.3f) top z %.3f length %.3f lean %.1f deg  rho_b %.3f rho_t %.3f'%(name,B[0],B[1],T[2],L,lean,np.hypot(*B[:2]),np.hypot(*T[:2])))
    return ob
pen('pen_uniball_L',(738,648),(689,1525),0.0050,0.0056,0.019,dx=0.004)
pen('pen_red',(768,757),(775,1520),0.0038,0.0041,0.012)
pen('marker_black',(817,727),(817,1525),0.0047,0.0049,0.030)
pen('pen_uniball_R',(928,742),(1020,1510),0.0050,0.0056,0.019,dx=-0.004)
# glue stick: vertical cylinder, top just under the scissors ring
B=on_base((900,1530)); g=lathe('glue_stick',[(0,0),(0.0062,0),(0.0062,0.094),(0.0055,0.097),(0,0.097)],seg=48,axis_from=B,axis_to=B+np.array([0,0,1]))
g.data.materials.append(M_CONT); uv_project(g,mirror_x=float(B[0])); ITEMS.append(g); print('glue_stick at (%.3f,%.3f)'%(B[0],B[1]))
plain_top_material(g,C.proj(B+np.array([0,0,0.09])))
# nail file: a flat pointed blade, nearly vertical, face turned ~25 deg to the camera
B=on_base((662,1487)); T=at_depth((690,1000),B[0]); T[2]=B[2]+0.086
nf=box('nail_file',0.0012,0.011,0.086); nf.data.materials.append(M_SILVER)
tip=box('nail_file_tip',0.0012,0.011,0.016,taper=(0.0012,0.002)); tip.data.materials.append(M_SILVER)
place_axis(nf,B+np.array([0,0,0.016]),T); place_axis(tip,B+np.array([0,0,0.016]),B)
for o in (nf,tip): o.matrix_world=o.matrix_world@Matrix.Rotation(math.radians(25),4,'Z'); ITEMS.append(o)
# teaspoon: bowl down (a flattened ellipsoid), flat handle up, bowl plane turned 60 deg from the camera
B=on_base((905,1493),z=Z0+0.004)
bowl=lathe('spoon_bowl',[(0,-0.0045)]+[(0.0135*math.sin(a),-0.0045*math.cos(a)) for a in np.linspace(0.15,math.pi-0.15,14)]+[(0,0.0045)],seg=48)
bowl.scale=(1,1.7,1); bowl.rotation_euler=(0,math.radians(90),math.radians(60)); bowl.location=B+np.array([0,0,0.0])
bpy.context.view_layer.update(); bowl.matrix_world=bowl.matrix_world.copy()
bowl.data.materials.append(M_SILVER); ITEMS.append(bowl)
hd=box('spoon_handle',0.0015,0.006,0.080,taper=(0.0015,0.0085)); hd.data.materials.append(M_SILVER)
place_axis(hd,B+np.array([0,0,0.034]),B+np.array([0,0,0.12])); hd.matrix_world=hd.matrix_world@Matrix.Rotation(math.radians(60),4,'Z'); ITEMS.append(hd)
# scissors: one finger ring up (the other behind it), two closed blades down to the tip on the base
RC=at_depth((905,905),-0.012); TIP=on_base((880,1500))
ring=ell_ring('scissors_ring',0.012,0.0088,0.0026); ring.data.materials.append(M_SILVER)
ring2=ell_ring('scissors_ring2',0.012,0.0088,0.0026); ring2.data.materials.append(M_SILVER)
Rm=Matrix.Translation(Vector(RC))@Matrix.Rotation(math.radians(-35),4,'Z')@Matrix.Rotation(math.radians(20),4,'Y')
ring.matrix_world=Rm; ring2.matrix_world=Matrix.Translation(Vector((-0.006,0,-0.001)))@Rm
ITEMS+=[ring,ring2]
bl=box('scissors_blades',0.0035,0.012,float(np.linalg.norm(RC-TIP))-0.007,taper=(0.002,0.003)); bl.data.materials.append(M_SILVER)
place_axis(bl,TIP,RC); bl.matrix_world=bl.matrix_world@Matrix.Rotation(math.radians(-35),4,'Z'); ITEMS.append(bl)
print('scissors ring at (%.3f,%.3f,%.3f) tip at (%.3f,%.3f)'%(RC[0],RC[1],RC[2],TIP[0],TIP[1]))
for o in ITEMS:
    if o.data.uv_layers: continue
    uv_project(o,mirror_x=float(o.matrix_world.translation.x))
OBJS=HOLDER+ITEMS
# ---------------- camera ----------------
camd=bpy.data.cameras.new('photo_cam'); cam=bpy.data.objects.new('photo_cam',camd); sc.collection.objects.link(cam)
cam.location=(P['D'],P['YC'],P['HC'])
cam.matrix_world=Matrix.Translation(Vector(cam.location))@Euler((math.pi/2-P['TH'],0,math.pi/2)).to_matrix().to_4x4()@Matrix.Rotation(P.get('RO',0.0),4,'Z')
camd.sensor_fit='HORIZONTAL'; camd.sensor_width=36; camd.lens=P['F']/C.W*36
camd.shift_x=-(C.CX-C.W/2)/C.W; camd.shift_y=(C.CY-C.H/2)/C.W; camd.clip_start=0.02; camd.clip_end=20
sc.camera=cam; sc.render.resolution_x=C.W; sc.render.resolution_y=C.H
from bpy_extras.object_utils import world_to_camera_view as w2c
bpy.context.view_layer.update()
for X in [(RR,0,HT),(0,RR,HT),(0,-RR,HT),(0,0,0),(-RR,0,HT)]:
    q=w2c(sc,cam,Vector(X)); print('  proj check',X,'cam.py',np.round(C.proj(X),1),'blender',round(q.x*C.W,1),round((1-q.y)*C.H,1))
eng=bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys()
sc.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in eng else 'BLENDER_EEVEE'
sc.view_settings.view_transform='Standard'
world=bpy.data.worlds.new('world'); sc.world=world; world.use_nodes=True; BG=world.node_tree.nodes['Background']
def render(path,transparent=True):
    sc.render.film_transparent=transparent; sc.render.filepath=path; bpy.ops.render.render(write_still=True)
def emission_only(on):
    for m in bpy.data.materials:
        if not m.use_nodes or 'Principled BSDF' not in m.node_tree.nodes: continue
        b=m.node_tree.nodes['Principled BSDF']; t=m.node_tree.nodes.get('Image Texture')
        if on:
            m['bc']=list(b.inputs['Base Color'].default_value); m['es']=b.inputs['Emission Strength'].default_value
            if t and b.inputs['Base Color'].links: m.node_tree.links.remove(b.inputs['Base Color'].links[0])
            b.inputs['Base Color'].default_value=(0,0,0,1); b.inputs['Emission Strength'].default_value=1.0
            b.inputs['Specular IOR Level'].default_value=0.0; b.inputs['Metallic'].default_value=0.0
        else:
            if t: m.node_tree.links.new(t.outputs[0],b.inputs['Base Color'])
            else: b.inputs['Base Color'].default_value=m['bc']
            b.inputs['Emission Strength'].default_value=m['es']; b.inputs['Specular IOR Level'].default_value=0.4
            b.inputs['Metallic'].default_value=0.4 if m.name in ('metal_black','wire_lattice') else 0.0
BG.inputs[1].default_value=0.0
sc.render.image_settings.color_mode='RGBA'
for o in ITEMS: o.hide_render=True
wall.data.materials[0]=M_DARK; render(f'{OUT}/holder_mask.png'); wall.data.materials[0]=M_LAT
for o in ITEMS: o.hide_render=False
emission_only(True); render(f'{OUT}/photo_view.png'); emission_only(False)
# ---------------- lit views ----------------
BG.inputs[0].default_value=(0.6,0.6,0.62,1); BG.inputs[1].default_value=0.35
def light(name,loc,energy,size):
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.size=size
    o=bpy.data.objects.new(name,ld); o.location=loc; sc.collection.objects.link(o)
    o.rotation_euler=(Vector((0,0,0.06))-o.location).to_track_quat('-Z','Y').to_euler(); return o
LIGHTS=[light('key',(0.45,-0.35,0.5),5,0.6),light('fill',(0.3,0.5,0.35),2,0.7),light('rim',(-0.5,0.1,0.45),2.5,0.5)]
fme=bpy.data.meshes.new('floor'); bm=bmesh.new(); bmesh.ops.create_grid(bm,x_segments=1,y_segments=1,size=0.3)
bm.to_mesh(fme); bm.free(); floor=bpy.data.objects.new('table',fme); sc.collection.objects.link(floor)
floor.data.materials.append(mat('table',color=srgb2lin((214,196,168)),rough=0.9,emit=0.0))
def shot(name,az,el,dist=0.36,lens=50,res=900):
    cd=bpy.data.cameras.new(name); c=bpy.data.objects.new(name,cd); sc.collection.objects.link(c); cd.lens=lens
    a=math.radians(az); e=math.radians(el); t=Vector((0,0,0.07))
    c.location=t+Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))*dist
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler(); sc.camera=c
    sc.render.resolution_x=sc.render.resolution_y=res; render(f'{OUT}/view_{name}.png',transparent=False)
    bpy.data.objects.remove(c); bpy.data.cameras.remove(cd)
if FINAL:
    shot('front',0,12); shot('q_right',50,22); shot('right',90,12); shot('q_rear',-135,28); shot('top',30,70); shot('close',20,15,dist=0.22)
sc.camera=cam; sc.render.resolution_x=C.W; sc.render.resolution_y=C.H
if FINAL:
    colM=bpy.data.collections.new('kalemlik'); colS=bpy.data.collections.new('studio')
    sc.collection.children.link(colM); sc.collection.children.link(colS)
    root=bpy.data.objects.new('Kalemlik',None); colM.objects.link(root)
    for o in OBJS: sc.collection.objects.unlink(o); colM.objects.link(o); o.parent=root; o.matrix_parent_inverse=Matrix.Identity(4)
    for o in LIGHTS+[floor,cam]: sc.collection.objects.unlink(o); colS.objects.link(o)
    camd.display_size=0.02
    for scr in bpy.data.screens:
        for ar in scr.areas:
            for sp in ar.spaces:
                if sp.type=='VIEW_3D':
                    sp.shading.type='MATERIAL'; sp.overlay.show_extras=False; sp.clip_start=0.001
                    r3=sp.region_3d; r3.view_perspective='PERSP'; r3.view_location=(0,0,0.07); r3.view_distance=0.42
                    r3.view_rotation=Euler((math.radians(75),0,math.radians(110))).to_quaternion()
    bpy.ops.object.select_all(action='DESELECT')
    for o in OBJS: o.select_set(True)
    bpy.context.view_layer.objects.active=wall
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/kalemlik.blend')
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/kalemlik.glb',use_selection=True,export_format='GLB')
