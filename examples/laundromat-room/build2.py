# Blender: the detailed laundromat (scene2.json), the photo projected from its solved camera.
import bpy, bmesh, json, sys, os, math
from mathutils import Matrix, Vector
import numpy as np
D=os.path.dirname(os.path.abspath(__file__))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
MODE=args[0] if args else 'final'
LAYER={'Bench':'A','Book':'A','Card':'A','Bucket':'A','Cart':'A','Washers':'B','Table':'B'}  # rest: C          # 'final' or 'mask' (props white, room black: what the props cover)
S=json.load(open(os.path.join(D,'scene2.json'))); R=S['room']
f=1253.978; W,H=1920,1080
d=np.array([-0.12228594,-0.07097164,0.98995413]); u=np.array([-0.00743268,-0.99734655,-0.07241975])
X=np.cross(d,u); X/=np.linalg.norm(X); Y=d; Z=np.cross(X,Y); M=np.c_[X,Y,Z]
bx=M.T@np.array([1,0,0.]); by=M.T@np.array([0,-1,0.]); bz=M.T@np.array([0,0,-1.])
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
def coll(n): c=bpy.data.collections.new(n); sc.collection.children.link(c); return c
C_room=coll('Laundromat'); C_cam=coll('Camera')
root=bpy.data.objects.new('Laundromat',None); C_room.objects.link(root)
props_root=bpy.data.objects.new('Props',None); C_room.objects.link(props_root); props_root.parent=root
shell_root=bpy.data.objects.new('Room_shell',None); C_room.objects.link(shell_root); shell_root.parent=root
cd=bpy.data.cameras.new('ViewCam'); cam=bpy.data.objects.new('ViewCam',cd); C_cam.objects.link(cam)
cam.matrix_world=Matrix(((bx[0],by[0],bz[0],0),(bx[1],by[1],bz[1],0),(bx[2],by[2],bz[2],R['h']),(0,0,0,1)))
cd.sensor_fit='HORIZONTAL'; cd.sensor_width=36; cd.lens=f*36/W; cd.clip_start=0.05; cd.clip_end=50; sc.camera=cam
proj=bpy.data.objects.new('Projector',None); C_cam.objects.link(proj); proj.matrix_world=cam.matrix_world.copy(); proj.empty_display_size=0.2
proj.hide_viewport=False
def load(n,cs='sRGB'): im=bpy.data.images.load(os.path.join(D,n)); im.colorspace_settings.name=cs; return im
def proj_mat(name,img,alpha_img=None,flat=None,tile=None):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; N=nt.nodes; L=nt.links
    for n in list(N): N.remove(n)
    out=N.new('ShaderNodeOutputMaterial')
    if flat is not None:
        em=N.new('ShaderNodeEmission'); em.inputs[0].default_value=(*flat,1); L.new(em.outputs[0],out.inputs['Surface']); return m
    tc=N.new('ShaderNodeTexCoord'); tc.object=proj
    sep=N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'],sep.inputs[0])
    def m1(op,a,b=None,v=None):
        n=N.new('ShaderNodeMath'); n.operation=op; L.new(a,n.inputs[0])
        if b is not None: L.new(b,n.inputs[1])
        if v is not None: n.inputs[1].default_value=v
        return n.outputs[0]
    nz=m1('MULTIPLY',sep.outputs['Z'],v=-1); nzc=m1('MAXIMUM',nz,v=1e-4)
    def axis(o,k):
        n=N.new('ShaderNodeMath'); n.operation='MULTIPLY_ADD'; n.inputs[1].default_value=k; n.inputs[2].default_value=0.5
        L.new(m1('DIVIDE',o,nzc),n.inputs[0]); return n.outputs[0]
    U=axis(sep.outputs['X'],f/W); V=axis(sep.outputs['Y'],f/H)
    comb=N.new('ShaderNodeCombineXYZ'); L.new(U,comb.inputs[0]); L.new(V,comb.inputs[1])
    tex=N.new('ShaderNodeTexImage'); tex.image=img; tex.extension='EXTEND'; tex.interpolation='Linear'; L.new(comb.outputs[0],tex.inputs[0])
    dd=m1('SUBTRACT',m1('MAXIMUM',m1('ABSOLUTE',m1('SUBTRACT',U,v=0.5)),m1('ABSOLUTE',m1('SUBTRACT',V,v=0.5))),v=0.5)
    mr=N.new('ShaderNodeMapRange'); mr.interpolation_type='SMOOTHSTEP'; L.new(dd,mr.inputs['Value']); mr.inputs['From Max'].default_value=0.06
    fac=m1('MAXIMUM',mr.outputs['Result'],m1('LESS_THAN',nz,v=0.05))
    oi=N.new('ShaderNodeObjectInfo'); fb=oi.outputs['Color']
    if tile is not None:
        geo=N.new('ShaderNodeNewGeometry')
        sub=N.new('ShaderNodeVectorMath'); sub.operation='SUBTRACT'; L.new(geo.outputs['Position'],sub.inputs[0]); sub.inputs[1].default_value=tile['o']
        cmb=N.new('ShaderNodeCombineXYZ')
        for i_,(ax,sz) in enumerate(((tile['u'],tile['su']),(tile['v'],tile['sv']))):
            dt=N.new('ShaderNodeVectorMath'); dt.operation='DOT_PRODUCT'; L.new(sub.outputs[0],dt.inputs[0]); dt.inputs[1].default_value=ax
            L.new(m1('DIVIDE',dt.outputs['Value'],v=sz),cmb.inputs[i_])
        tt=N.new('ShaderNodeTexImage'); tt.image=load(os.path.join('tiles',tile['img']+'.png')); tt.extension='REPEAT'; tt.interpolation='Linear'
        L.new(cmb.outputs[0],tt.inputs[0]); fb=tt.outputs['Color']
    mix=N.new('ShaderNodeMix'); mix.data_type='RGBA'; L.new(fac,mix.inputs['Factor']); L.new(tex.outputs['Color'],mix.inputs['A']); L.new(fb,mix.inputs['B'])
    em=N.new('ShaderNodeEmission'); L.new(mix.outputs['Result'],em.inputs['Color'])
    if MODE.startswith('mask'): em.inputs['Color'].default_value=(1,1,1,1); L.remove(em.inputs['Color'].links[0])
    if alpha_img is not None:
        at=N.new('ShaderNodeTexImage'); at.image=alpha_img; at.extension='CLIP'; L.new(comb.outputs[0],at.inputs[0])
        tr=N.new('ShaderNodeBsdfTransparent'); mx=N.new('ShaderNodeMixShader')
        L.new(at.outputs['Color'],mx.inputs[0]); L.new(tr.outputs[0],mx.inputs[1]); L.new(em.outputs[0],mx.inputs[2]); L.new(mx.outputs[0],out.inputs['Surface'])
        try: m.surface_render_method='DITHERED'
        except: pass
    else: L.new(em.outputs[0],out.inputs['Surface'])
    for i,n in enumerate(N): n.location=((i%8)*200-1600,-(i//8)*250)
    return m
img_ref=load('ref.png'); img_plate=load('plate.png'); a_plant=load('alpha_plant.png','Non-Color')
if MODE.startswith('mask'):
    MA=MB=MC=proj_mat('Photo_Props',img_ref); M_plant=proj_mat('Photo_Plant',img_ref,a_plant); M_room=proj_mat('Photo_Room',None,flat=(0,0,0))
else:
    MA=proj_mat('Photo_Props_front',img_ref); MB=proj_mat('Photo_Props_mid',load('plate_B.png')); MC=proj_mat('Photo_Props_back',load('plate_C.png'))
    M_plant=proj_mat('Photo_Plant',load('plate_C.png'),a_plant); M_room=proj_mat('Photo_Room',img_plate)
MAT={'A':MA,'B':MB,'C':MC}
TJ=json.load(open(os.path.join(D,'tiles.json')))
def T(name,**over): t=dict(TJ[name]); t.update(over); t['img']=name; return t
Xl=R['Xl']; Lb=TJ['light']['o']
TILE={'Floor':T('floor'),'Ceiling':T('ceiling'),'Wall_left_windows':T('window'),'Wall_front':T('window',u=[1,0,0],o=[Xl,0,0]),
      'Wall_right':T('wall'),'Wall_back':T('wall',u=[1,0,0]),'Washers':T('washer'),'Bench':T('bench_seat'),'Bench_back':T('bench_back'),
      'Light_mid':T('light',o=[Lb[0],Lb[1]-1.946,0]),'Light_front':T('light',o=[Lb[0],Lb[1]-3.891,0])}
LAYER.update({'Bench_back':'A'})
SRC={'A':img_ref,'B':None,'C':None}
def mat_for(name,layer,room=False):
    if MODE.startswith('mask') or name not in TILE: return M_room if room else MAT[layer]
    img=img_plate if room else {'A':img_ref,'B':bpy.data.images.get('plate_B.png'),'C':bpy.data.images.get('plate_C.png')}[layer]
    return proj_mat('Photo_'+name,img,tile=TILE[name])
TONES=json.load(open(os.path.join(D,'tones.json')))
TONE_ALIAS={'Bench_back':'Bench_back','Light_mid':'Light_near','Light_front':'Light_near','Washers':'Washers','Dryers':'Dryers','Table':'Table_top','Cart':'Cart','Bench':'Bench_seat','Stool_L':'Stool_L_seat','Stool_R':'Stool_R_seat','Book':'Bench_seat','Card':'Bench_back','Plant':'Cabinet'}
def obj(name,bm,mat,parent):
    me=bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(name,me); C_room.objects.link(o); o.parent=parent; me.materials.append(mat)
    o.color=(*TONES.get(TONE_ALIAS.get(name,name),[0.05,0.05,0.05]),1); return o
def add_box(bm,x0,x1,y0,y1,z0,z1):
    bmesh.ops.create_cube(bm,size=1,matrix=Matrix.Translation(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))@Matrix.Diagonal((x1-x0,y1-y0,z1-z0,1)))
def add_tube(bm,a,b,r,seg):
    a=Vector(a); b=Vector(b); dv=b-a; L_=dv.length
    rot=dv.to_track_quat('Z','Y').to_matrix().to_4x4()
    bmesh.ops.create_cone(bm,cap_ends=True,segments=seg,radius1=r,radius2=r,depth=L_,matrix=Matrix.Translation((a+b)/2)@rot)
def add_cylx(bm,x0,x1,y,z,r,seg):
    rot=Matrix.Rotation(math.pi/2,4,'Y')
    bmesh.ops.create_cone(bm,cap_ends=True,segments=seg,radius1=r,radius2=r,depth=abs(x1-x0),matrix=Matrix.Translation(((x0+x1)/2,y,z))@rot)
def add_cone(bm,p):
    x,y=p['c']; z0,z1=p['z']; r0,r1=p['r']; seg=p['seg']
    def ring(z,r): return [bm.verts.new((x+r*math.cos(t),y+r*math.sin(t),z)) for t in np.linspace(0,2*math.pi,seg,endpoint=False)]
    lo,hi=ring(z0,r0),ring(z1,r1)
    for i in range(seg): bm.faces.new((lo[i],lo[(i+1)%seg],hi[(i+1)%seg],hi[i]))
    if p['bottom']: bm.faces.new(lo[::-1])
    if p['top']: bm.faces.new(hi)
    if p['inner']:
        t=p['inner']; li,hi2=ring(z0+t,r0-t),ring(z1,r1-t)
        for i in range(seg): bm.faces.new((li[(i+1)%seg],li[i],hi2[i],hi2[(i+1)%seg])); bm.faces.new((hi[i],hi[(i+1)%seg],hi2[(i+1)%seg],hi2[i]))
        bm.faces.new(li)
def add_quad(bm,v):
    V=[bm.verts.new(p) for p in v]
    for f_ in [(0,1,5,4),(2,6,7,3),(4,5,7,6),(0,2,3,1),(0,4,6,2),(1,3,7,5)]: bm.faces.new([V[i] for i in f_])
for g in S['groups']:
    bm=bmesh.new()
    for p in g['parts']:
        k=p['k']
        if k=='box': add_box(bm,*p['b'])
        elif k=='tube': add_tube(bm,p['a'],p['b'],p['r'],p['seg'])
        elif k=='cylx': add_cylx(bm,p['x0'],p['x1'],p['y'],p['z'],p['r'],p['seg'])
        elif k=='cone': add_cone(bm,p)
        elif k=='quad': add_quad(bm,p['v'])
        elif k=='poly': bm.faces.new([bm.verts.new(v) for v in p['v']])
    bmesh.ops.recalc_face_normals(bm,faces=[f_ for f_ in bm.faces if len(bm.faces)>1]) if g['mat']!='plant' else None
    o=obj(g['name'],bm,M_plant if g['mat']=='plant' else mat_for(g['name'],LAYER.get(g['name'],'C')),props_root)
    if MODE.startswith('mask:') and LAYER.get(g['name'],'C') not in MODE[5:]: o.hide_render=True
xl,xr,yf,yb,hc=R['Xl'],R['Xr'],R['Yf'],R['Yb'],R['Hc']
shell=dict(Floor=[(xl,yf,0),(xr,yf,0),(xr,yb,0),(xl,yb,0)],Ceiling=[(xl,yf,hc),(xl,yb,hc),(xr,yb,hc),(xr,yf,hc)],
           Wall_back=[(xl,yb,0),(xr,yb,0),(xr,yb,hc),(xl,yb,hc)],Wall_left_windows=[(xl,yf,0),(xl,yb,0),(xl,yb,hc),(xl,yf,hc)],
           Wall_right=[(xr,yb,0),(xr,yf,0),(xr,yf,hc),(xr,yb,hc)],Wall_front=[(xr,yf,0),(xl,yf,0),(xl,yf,hc),(xr,yf,hc)])
for k,v in shell.items():
    bm=bmesh.new(); bm.faces.new([bm.verts.new(p) for p in v]); obj(k,bm,mat_for(k,None,room=True),shell_root)
sc.render.engine='BLENDER_EEVEE'; sc.render.resolution_x=W; sc.render.resolution_y=H
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'; sc.render.filter_size=0.5
w=bpy.data.worlds.new('World'); w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0,0,0,1); sc.world=w
sc.eevee.taa_render_samples=16
if MODE.startswith('mask'):
    sc.render.filepath=os.path.join(D,'cover_'+MODE[5:]+'.png'); bpy.ops.render.render(write_still=True); print('MASK DONE')
else:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(D,'laundromat_build.blend')); print('BUILT')
