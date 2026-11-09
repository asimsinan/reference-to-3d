"""Blender: table, bench, two stools and the tabletop objects from scene.json.
Run: Blender -b -P build.py -- --mode match|final --out DIR [--shots photo,...] [--res N] [--blend f.blend] [--glb f.glb]
match: every surface is the photo projected from the solved camera (emission) -> compare with the photo.
final: real materials (oak, linen, glazed porcelain, wax, ...)."""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector, Matrix, noise
A=sys.argv[sys.argv.index("--")+1:]
arg=lambda k,d=None: A[A.index(k)+1] if k in A else d
MODE=arg("--mode","final"); OUT=arg("--out","r"); RES=int(arg("--res","1000")); SHOTS=arg("--shots","photo").split(",")
HERE=os.path.dirname(os.path.abspath(__file__)); TEX=os.path.join(HERE,"tex")
S=json.load(open(os.path.join(HERE,"scene.json"))); TB=S['table']; OB=S['objects']; CAMP=S['cam']
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
COLL={}
def coll(name):
    if name not in COLL:
        c=bpy.data.collections.new(name); sc.collection.children.link(c); COLL[name]=c
    return COLL[name]
# ------------------------------------------------------------------ mesh helpers
def mesh_obj(name, verts, faces, col, uvs=None, smooth=True, mat=None):
    me=bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts],[],faces); me.validate()
    if uvs is not None:
        uvl=me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                uvl.data[li].uv=uvs(me.vertices[me.loops[li].vertex_index].co, poly)
    for p in me.polygons: p.use_smooth=smooth
    o=bpy.data.objects.new(name,me); coll(col).objects.link(o)
    if mat: me.materials.append(mat)
    return o
def rr_ring(a,b,r,ins,z,nc=8,ns=(10,6)):
    """rounded rectangle (half sizes a,b; corner radius r, or 4 radii for corners (+,+),(-,+),(-,-),(+,-)) inset by
    ins at height z; CCW from the +X side. Same vertex count for any a,b,r,ins."""
    rs=tuple(r) if isinstance(r,(tuple,list)) else (r,)*4
    a_,b_=a-ins,b-ins; pts=[]
    cs=[(1,1,0,ns[1]),(-1,1,90,ns[0]),(-1,-1,180,ns[1]),(1,-1,270,ns[0])]
    cen=[]; rr=[]
    for k,(sx,sy,a0,_) in enumerate(cs):
        r_=max(rs[k]-ins,0.0006); rr.append(r_); cen.append((sx*(a_-r_),sy*(b_-r_)))
    for k,(sx,sy,a0,nstr) in enumerate(cs):
        (cx_,cy_),r_=cen[k],rr[k]
        for j in range(nc+1):
            t=math.radians(a0+90*j/nc); pts.append((cx_+r_*math.cos(t),cy_+r_*math.sin(t),z))
        k2=(k+1)%4; a1=math.radians(cs[k2][2]); e=pts[-1]
        nx,ny=cen[k2][0]+rr[k2]*math.cos(a1), cen[k2][1]+rr[k2]*math.sin(a1)
        for j in range(1,nstr+1):
            t=j/(nstr+1); pts.append((e[0]+(nx-e[0])*t, e[1]+(ny-e[1])*t, z))
    return pts
def loft(rings, cap_top=True, cap_bot=True, top_dome=0.0, top_steps=6):
    """rings: list of point lists (same count), bottom to top. Caps: inward rings then an n-gon."""
    V=[]; F=[]; n=len(rings[0])
    for rg in rings: V+=rg
    for i in range(len(rings)-1):
        for j in range(n):
            a=i*n+j; b=i*n+(j+1)%n; F.append((a,b,b+n,a+n))
    def cap(ring_pts, up, dome):
        base=len(V); cx=sum(p[0] for p in ring_pts)/n; cy=sum(p[1] for p in ring_pts)/n; z0=ring_pts[0][2]
        prev=list(range(base-n, base)) if up else None
        rings_idx=[]
        for s in range(1,top_steps+1):
            f=1-s/(top_steps+0.6)
            rr=[(cx+(p[0]-cx)*f, cy+(p[1]-cy)*f, z0+(dome*(1-f*f) if up else -dome*(1-f*f))) for p in ring_pts]
            rings_idx.append(len(V)); V.extend(rr)
        return rings_idx
    if cap_top:
        top=rings[-1]; idx=cap(top,True,top_dome); prev=(len(rings)-1)*n
        for st in idx:
            for j in range(n): F.append((prev+j,prev+(j+1)%n,st+(j+1)%n,st+j))
            prev=st
        F.append(tuple(prev+j for j in range(n)))
    if cap_bot:
        bot=rings[0]; idx=cap(bot,False,0.0); prev=0
        for st in idx:
            for j in range(n): F.append((prev+(j+1)%n,prev+j,st+j,st+(j+1)%n))
            prev=st
        F.append(tuple(prev+j for j in range(n))[::-1])
    return V,F
def lathe(profile, nseg=48, close_bottom=True, close_top=False):
    """profile: [(r,z)] bottom to top; r=0 at an end closes it"""
    V=[]; F=[]
    for (r,z) in profile:
        for k in range(nseg):
            t=2*math.pi*k/nseg; V.append((r*math.cos(t),r*math.sin(t),z))
    for i in range(len(profile)-1):
        for k in range(nseg):
            a=i*nseg+k; b=i*nseg+(k+1)%nseg; F.append((a,b,b+nseg,a+nseg))
    return V,F
def place(o, x,y,z, rotz=0.0):
    o.location=(x,y,z); o.rotation_euler=(0,0,rotz)
# ---- UV functions (metres -> texture), grain along u
def uv_box(scale_u, scale_v, off=(0,0), grain='x'):
    def f(co, poly):
        n=poly.normal; ax=max(range(3),key=lambda i: abs(n[i]))
        if grain=='z':          # vertical parts: grain up the part
            if ax==2: u,v=co.x,co.y
            else: u,v=co.z,(co.x if ax==1 else co.y)
        else:
            if ax==2: u,v=co.x,co.y
            elif ax==1: u,v=co.x,co.z
            else: u,v=co.y,co.z
        return (u/scale_u+off[0], v/scale_v+off[1])
    return f
def uv_cyl(scale_u, scale_v, off=(0,0)):
    def f(co,poly):
        a=math.atan2(co.y,co.x); r=math.hypot(co.x,co.y)
        return (co.z/scale_u+off[0], (a*0.03)/scale_v+off[1])
    return f
OAK_U,OAK_V=1.40,0.60
LEG_U,LEG_V=1.22,0.16
# ------------------------------------------------------------------ materials
GAINS=json.load(open(os.path.join(HERE,"gains.json"))) if os.path.exists(os.path.join(HERE,"gains.json")) and "--nogain" not in A else {}
def img(name, colorspace='sRGB'):
    if colorspace=='sRGB' and GAINS and os.path.exists(os.path.join(TEX,name+"_cal.png")): name=name+"_cal"
    i=bpy.data.images.load(os.path.join(TEX,name+".png"),check_existing=True); i.colorspace_settings.name=colorspace; return i
def proj_mat():
    """photo projected from the solved camera, as emission (exact per pixel: computed in the shader)"""
    m=bpy.data.materials.new("photo_projection"); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear(); N=nt.nodes; Lk=nt.links
    out=N.new("ShaderNodeOutputMaterial"); geo=N.new("ShaderNodeNewGeometry")
    sub=N.new("ShaderNodeVectorMath"); sub.operation='SUBTRACT'; sub.inputs[1].default_value=CAMP['C']; Lk.new(geo.outputs['Position'],sub.inputs[0])
    comps=[]
    for i in range(3):
        d=N.new("ShaderNodeVectorMath"); d.operation='DOT_PRODUCT'; d.inputs[1].default_value=CAMP['R'][i]; Lk.new(sub.outputs[0],d.inputs[0]); comps.append(d.outputs['Value'])
    def m_(op,a,b):
        n_=N.new("ShaderNodeMath"); n_.operation=op
        for k,x in enumerate((a,b)):
            if isinstance(x,(int,float)): n_.inputs[k].default_value=x
            else: Lk.new(x,n_.inputs[k])
        return n_.outputs[0]
    u=m_('DIVIDE', m_('ADD', m_('MULTIPLY', m_('DIVIDE',comps[0],comps[2]), CAMP['f']), CAMP['cx']), CAMP['w'])
    v=m_('SUBTRACT',1.0, m_('DIVIDE', m_('ADD', m_('MULTIPLY', m_('DIVIDE',comps[1],comps[2]), CAMP['f']), CAMP['cy']), CAMP['h']))
    cmb=N.new("ShaderNodeCombineXYZ"); Lk.new(u,cmb.inputs[0]); Lk.new(v,cmb.inputs[1])
    t=N.new("ShaderNodeTexImage"); t.image=bpy.data.images.load(os.path.join(HERE,"ref.jpg")); t.extension='EXTEND'; t.interpolation='Cubic'
    Lk.new(cmb.outputs[0],t.inputs[0]); e=N.new("ShaderNodeEmission"); Lk.new(t.outputs[0],e.inputs[0]); Lk.new(e.outputs[0],out.inputs[0])
    return m
PROJ=proj_mat() if MODE in ("match","id") else None
def pbr(name, color=None, tex=None, rough=0.5, spec=0.5, normal=None, nstr=1.0, sss=0.0, sss_r=(1,0.5,0.3), coat=0.0, metallic=0.0, alpha_tex=False, rough_tex=None):
    if MODE in ("match","id"): return PROJ
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; N=nt.nodes; Lk=nt.links
    b=N["Principled BSDF"]
    if tex:
        t=N.new("ShaderNodeTexImage"); t.image=img(tex); t.interpolation='Cubic'; Lk.new(t.outputs[0],b.inputs["Base Color"])
        if alpha_tex: Lk.new(t.outputs[1],b.inputs["Alpha"])
    elif color:
        g=GAINS.get(name,[1,1,1]); color=tuple(min(1.0,c*k) for c,k in zip(color,g)); b.inputs["Base Color"].default_value=(*color,1)
    b.inputs["Roughness"].default_value=rough; b.inputs["Specular IOR Level"].default_value=spec; b.inputs["Metallic"].default_value=metallic
    if sss>0:
        b.inputs["Subsurface Weight"].default_value=sss; b.inputs["Subsurface Radius"].default_value=sss_r; b.inputs["Subsurface Scale"].default_value=0.01
    if coat>0: b.inputs["Coat Weight"].default_value=coat; b.inputs["Coat Roughness"].default_value=0.08
    if normal:
        tn=N.new("ShaderNodeTexImage"); tn.image=img(normal,'Non-Color'); nm=N.new("ShaderNodeNormalMap"); nm.inputs[0].default_value=nstr
        Lk.new(tn.outputs[0],nm.inputs[1]); Lk.new(nm.outputs[0],b.inputs["Normal"])
    return m
def srgb(r,g,b):
    f=lambda c: (c/255)/12.92 if c/255<=0.04045 else ((c/255+0.055)/1.055)**2.4
    return (f(r),f(g),f(b))
M_OAK=pbr("oak",tex="oak_photo",rough=0.32,spec=0.5,normal="oak_photo_n",nstr=0.35)
M_LEG=pbr("oak_leg",tex="leg_photo",rough=0.40,spec=0.5,normal="leg_photo_n",nstr=0.3)
M_LINEN=pbr("linen",tex="linen_photo",rough=0.95,spec=0.25,normal="linen_photo_n",nstr=0.6)
M_SLOT=pbr("slot_dark",color=srgb(40,28,20),rough=0.8)
M_PORC=pbr("porcelain",color=srgb(240,239,235),rough=0.12,spec=0.5,coat=0.3)
M_LABEL=pbr("porcelain_print",tex="cup_label",rough=0.12,spec=0.5,coat=0.3)
M_COAST=pbr("coaster",tex="oak_coaster",rough=0.55,spec=0.4,normal="oak_n",nstr=0.3)
M_PLATE=pbr("plate_wood",tex="oak_plate",rough=0.3,spec=0.5,normal="oak_photo_n",nstr=0.3,coat=0.3)
M_MUF=pbr("muffin",color=srgb(64,40,30),rough=0.75,spec=0.35)
M_MUFP=pbr("muffin_paper",color=srgb(70,44,32),rough=0.6,spec=0.4)
M_PINK=pbr("pink_wax",tex="pink_wax",coat=0.6,rough=0.22,spec=0.6,sss=0.15,sss_r=(1.0,0.45,0.35))
M_WAX=pbr("white_wax",color=srgb(238,233,222),rough=0.45,spec=0.4,sss=0.4,sss_r=(1.0,0.75,0.5))
M_WICK=pbr("wick",color=srgb(30,26,24),rough=0.9)
M_POT=pbr("pot_ceramic",color=srgb(236,234,228),rough=0.45,spec=0.4)
M_SOIL=pbr("soil",color=srgb(60,45,35),rough=0.95)
M_LEAF=pbr("leaf",tex="leaf",rough=0.5,spec=0.4)
M_LEAF_IN=pbr("leaf_inner",color=srgb(18,40,16),rough=0.7)
M_STEM=pbr("stem",color=srgb(196,190,170),rough=0.6)
M_PAPER=pbr("napkin",color=srgb(240,238,234),rough=0.85,spec=0.3)
# ------------------------------------------------------------------ table
L,W,T,H=TB['L'],TB['W'],TB['T'],TB['H']; rc=TB['rc']
def board_top(name, a, b, r, z0, t, er_top=0.004, er_bot=0.0015, x=0, y=0, rot=0, mat=None, uvf=None, col="Masa", steps=4):
    rings=[rr_ring(a,b,r,er_bot,z0)]
    for k in range(1,steps+1):
        th=math.pi/2*k/steps; rings.append(rr_ring(a,b,r,er_bot*(1-math.sin(th)),z0+er_bot*(1-math.cos(th))))
    for k in range(steps+1):
        th=math.pi/2*k/steps; rings.append(rr_ring(a,b,r,er_top*(1-math.cos(th)),z0+t-er_top+er_top*math.sin(th)))
    V,F=loft(rings); o=mesh_obj(name,V,F,col,uvs=uvf,mat=mat); place(o,x,y,0,rot); return o
# two leaves of the top, split along the seam (a flip top): rounded at the table's corners, square at the seam
sy=TB['seam_y']; g=TB['seam_gap']/2; rs_=0.0015
for nm,(y0,y1),rads,off in [('top_leaf_back',(sy+g,W/2),(rc,rc,rs_,rs_),(0.1,0.3)),('top_leaf_front',(-W/2,sy-g),(rs_,rs_,rc,rc),(0.1,0.05))]:
    board_top(nm, L/2, (y1-y0)/2, rads, H-T, T, x=0, y=(y0+y1)/2, mat=M_OAK, uvf=uv_box(OAK_U,OAK_V,off), er_top=0.004)
# legs: round, slightly tapered, rounded foot
for i,(lx,ly) in enumerate(TB['legs']):
    rt,rb=TB['leg_r_top'],TB['leg_r_bot']; fr=0.006
    prof=[(0,0.0)]+[(rb-fr+fr*math.sin(math.pi/2*k/5), fr-fr*math.cos(math.pi/2*k/5)) for k in range(6)]+[(rb+(rt-rb)*f,(H-T)*f) for f in (0.3,0.6,1.0)]
    prof=[(r,z) for (r,z) in prof]; V,F=lathe(prof,40)
    F.append(tuple(len(V)-40+k for k in range(40)))
    o=mesh_obj(f"leg_{i+1}",V,F,"Masa",uvs=uv_box(LEG_U,LEG_V,(0.3*i,0.2*i),'z'),mat=M_LEG); place(o,lx,ly,0)
# aprons
ab=TB['apron_zb']; at=TB['apron_t']; zt_=H-T
def plank(name,a,b,z0,z1,x,y,rot,uvoff):
    V,F=loft([rr_ring(a,b,0.002,0,z0,nc=2,ns=(6,2)),rr_ring(a,b,0.002,0,z1,nc=2,ns=(6,2))],top_steps=1)
    o=mesh_obj(name,V,F,"Masa",uvs=uv_box(OAK_U,OAK_V,uvoff),mat=M_OAK,smooth=False); place(o,x,y,0,rot); return o
sx_=TB['short_apron_x']; plank("apron_end_1",at/2,TB['short_apron_half'],ab,zt_,-(sx_-at/2),0,0,(0.2,0.1)); plank("apron_end_2",at/2,TB['short_apron_half'],ab,zt_,(sx_-at/2),0,0,(0.6,0.4))
ly_=TB['long_apron_y']; plank("apron_side_front",TB['long_apron_half'],at/2,ab,zt_,0,-(ly_-at/2),0,(0.0,0.6)); plank("apron_side_back",TB['long_apron_half'],at/2,ab,zt_,0,(ly_-at/2),0,(0.5,0.8))
for i,(x,s) in enumerate(TB['slots']):
    plank(f"slot_{i+1}",0.004,0.0012,H-T-0.034,H-T-0.004,x,s*(ly_+0.0004),0,(0,0)).data.materials[0]=M_SLOT if MODE!="match" else PROJ
# ------------------------------------------------------------------ seats (bench, two stools)
FAB=0.43
def tube_between(name, p0, p1, r0, r1, col, mat, zcut0=None, zcut1=None, n=28, nrings=8, foot_fillet=0.0025, uvoff=(0,0)):
    """tapered round leg from p0 (top) to p1 (foot); end rings slid along the axis onto the planes z=zcut0 / z=zcut1"""
    p0=Vector(p0); p1=Vector(p1); d=(p1-p0); Lg=d.length; d.normalize()
    e1=d.cross(Vector((0,0,1))); e1=e1.normalized() if e1.length>1e-6 else Vector((1,0,0)); e2=d.cross(e1).normalized()
    rings=[]
    ss=[k/nrings for k in range(nrings+1)]
    for s in ss:
        rings.append((s, r0+(r1-r0)*s))
    V=[];F=[];UV=[]
    for i,(s,r) in enumerate(rings):
        c=p0+d*(Lg*s)
        for k in range(n):
            t=2*math.pi*k/n; q=c+r*(math.cos(t)*e1+math.sin(t)*e2)
            if i==0 and zcut0 is not None: q=q+d*((zcut0-q.z)/d.z)
            if i==len(rings)-1 and zcut1 is not None: q=q+d*((zcut1-q.z)/d.z)
            V.append(q)
    # foot: a small rounded edge, then the flat sole
    last=len(rings)-1; base=len(V)
    for k in range(n):
        q=V[last*n+k]; c=p1; v=(q-Vector((c.x,c.y,q.z))); V.append(Vector((c.x,c.y,q.z))+v*((v.length-foot_fillet)/max(v.length,1e-6))-Vector((0,0,0)))
    for k in range(n): V[base+k].z=max(V[base+k].z-0.0,0.0)
    for k in range(n): V[last*n+k].z+=foot_fillet
    for i in range(len(rings)):
        for k in range(n):
            a=i*n+k; b=i*n+(k+1)%n; F.append((a,b,b+n,a+n))
    F.append(tuple(range(n))[::-1]); F.append(tuple(base+k for k in range(n)))
    def uvf(co,poly):
        w=Vector(co)-p0; s=w.dot(d); a=math.atan2(w.dot(e2),w.dot(e1))
        rr=(Vector(co)-(p0+d*s)).length
        return (s/LEG_U+uvoff[0], a*rr/LEG_V+uvoff[1])
    return mesh_obj(name,V,F,col,uvs=uvf,mat=mat)
for nm,sp in S['seats'].items():
    col={"bench":"Bank","S1":"Tabure_1","S2":"Tabure_2"}[nm]
    a,b,r_,zr,zt,zb,ztr,TW=sp['a'],sp['b'],sp['rc'],sp['zr'],sp['zt'],sp['tray_zb'],sp['tray_zt'],sp['TW']
    fl=zb+0.012; er=0.004
    # tray: outer bottom edge rounded, outer wall, rounded rim, inner wall, floor
    rings=[]
    for k in range(4):
        th=math.pi/2*k/3; rings.append(rr_ring(a+TW,b+TW,r_+TW,er*(1-math.sin(th)),zb+er*(1-math.cos(th))))
    rings.append(rr_ring(a+TW,b+TW,r_+TW,0,ztr-TW/2))
    for k in range(1,6):
        th=math.pi*k/6; rings.append(rr_ring(a+TW,b+TW,r_+TW,TW/2*(1-math.cos(th)),ztr-TW/2+TW/2*math.sin(th)))
    rings.append(rr_ring(a+TW,b+TW,r_+TW,TW,ztr-TW/2)); rings.append(rr_ring(a+TW,b+TW,r_+TW,TW,fl))
    V,F=loft(rings,top_steps=3)
    tray=mesh_obj(f"{col}_kasa",V,F,col,uvs=uv_box(OAK_U,OAK_V,(0.37*len(nm),0.21*len(nm))),mat=M_OAK); place(tray,sp['cx'],sp['cy'],0,sp['th'])
    # cushion: from the tray floor, sides bulging a little above the rim, rounded top edge, slightly domed top
    RE=0.03; rings=[rr_ring(a,b,r_,0.002,fl+0.002), rr_ring(a,b,r_,0.0,zr), rr_ring(a,b,r_,-0.002,(zr+zt-RE)/2+0.004)]
    for k in range(7):
        th=math.pi/2*k/6; rings.append(rr_ring(a,b,r_,RE*(1-math.cos(th)),zt-RE+RE*math.sin(th)))
    V,F=loft(rings,top_dome=0.006,top_steps=8)
    cu=mesh_obj(f"{col}_minder",V,F,col,uvs=uv_box(FAB,FAB),mat=M_LINEN); place(cu,sp['cx'],sp['cy'],0,sp['th'])
    for i,lg in enumerate(sp['legs']):
        tube_between(f"{col}_ayak_{i+1}",lg['top'],lg['foot'],sp['leg_r_top'],sp['leg_r_bot'],col,M_LEG,zcut0=zb+0.001,zcut1=0.0,uvoff=(0.13*i,0.31*i))
# ------------------------------------------------------------------ tabletop objects
def merge(o):
    bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(o.data); bm.free(); return o
def lathe_obj(name,prof,col,mat,nseg=48,uvf=None):
    V,F=lathe(prof,nseg); o=mesh_obj(name,V,F,col,uvs=uvf,mat=mat); return merge(o)
ang=lambda v: math.atan2(v[1],v[0])
LEFT=OB['img_left']; AWAY=OB['img_away']; TOCAM=(-AWAY[0],-AWAY[1]); RIGHT=(-LEFT[0],-LEFT[1])
def cup(name, c, handle_dir, label=False, hz=(0.80,0.24), reach=0.019):
    rb,rt,h=c['rb'],c['rt'],c['h']; rad=lambda z: rb+(rt-rb)*(z/h)**0.85
    outer=[(0,0.0),(rb-0.004,0.0),(rb-0.001,0.0008),(rb,0.003)]+[(rad(h*f),h*f) for f in (0.12,0.3,0.5,0.7,0.85,0.95)]+[(rt,h-0.0012)]
    rim=[(rt-0.0006,h-0.0002),(rt-0.0016,h),(rt-0.0026,h-0.0002),(rt-0.0032,h-0.0012)]
    inner=[(rad(h*f)-0.0032,h*f) for f in (0.92,0.75,0.5,0.3,0.18)]+[(rb-0.007,0.0075),(rb-0.012,0.0062),(0,0.006)]
    prof=outer+rim+inner
    o=lathe_obj(name,prof,"Masa_ustu",M_PORC,64); place(o,c['X'],c['Y'],c['z'])
    if label and MODE not in ("match","id"):
        # the printed word: the body's outer faces take the label material, u = angle round the cup
        o.data.materials.append(M_LABEL); me=o.data
        tx=label; uvl=me.uv_layers.new(name="UVMap")
        for p in me.polygons:
            cz=sum((me.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
            rr=math.hypot(cz.x,cz.y)
            if 0.004<cz.z<h-0.0015 and rr>rad(cz.z)-0.0012: p.material_index=1
            for li in p.loop_indices:
                co=me.vertices[me.loops[li].vertex_index].co; a=math.atan2(co.y,co.x)-tx
                a=(a+math.pi)%(2*math.pi)-math.pi
                if p.material_index==1 and abs(a)>math.pi*0.9:   # far side: keep the seam in the plain area
                    a=math.copysign(math.pi*0.9,a)
                uvl.data[li].uv=(0.5+a/(2*math.pi), co.z/h)
    # handle: an oval tube on a C curve in the plane at handle_dir
    phi=handle_dir; za,zb_=hz[0]*h,hz[1]*h
    P=[(rad(za)-0.003,za),(rad(za)+reach,za+0.003),(rad(zb_)+reach+0.002,zb_+0.004),(rad(zb_)-0.003,zb_)]
    pts=[]
    for k in range(25):
        t=k/24; bx=(1-t)**3*P[0][0]+3*(1-t)**2*t*P[1][0]+3*(1-t)*t*t*P[2][0]+t**3*P[3][0]
        bz=(1-t)**3*P[0][1]+3*(1-t)**2*t*P[1][1]+3*(1-t)*t*t*P[2][1]+t**3*P[3][1]; pts.append(Vector((bx,0,bz)))
    V=[];F=[];n=16
    for i,p in enumerate(pts):
        tg=(pts[min(i+1,24)]-pts[max(i-1,0)]).normalized(); side=Vector((0,1,0)); nrm=tg.cross(side).normalized()
        for k in range(n):
            t=2*math.pi*k/n; V.append(p+0.0042*math.cos(t)*nrm+0.0026*math.sin(t)*side)
    for i in range(24):
        for k in range(n): a=i*n+k; b=i*n+(k+1)%n; F.append((a,b,b+n,a+n))
    hd=mesh_obj(name+"_kulp",V,F,"Masa_ustu",mat=M_PORC); hd.location=(c['X'],c['Y'],c['z']); hd.rotation_euler=(0,0,phi)
    return o
_a=math.radians(60); _hd=(math.cos(_a)*LEFT[0]+math.sin(_a)*TOCAM[0], math.cos(_a)*LEFT[1]+math.sin(_a)*TOCAM[1])
cup("fincan_1",OB['cup1'],ang(_hd),hz=(0.66,0.13),reach=0.017)
phi_txt=ang((math.cos(math.radians(53))*TOCAM[0]+math.sin(math.radians(53))*RIGHT[0], math.cos(math.radians(53))*TOCAM[1]+math.sin(math.radians(53))*RIGHT[1]))
cup("fincan_2",OB['cup2'],ang(AWAY),label=phi_txt)
def coaster(name,c,cupc):
    R0,RL,OFF,TH=c.get('R0',0.040),0.017,c.get('R0',0.040)+0.001,0.007
    def rfun(t):
        # radius of the union (main disc + lobe toward the image's right) along direction t from the main centre
        lx,ly=OFF*RIGHT[0],OFF*RIGHT[1]; dx,dy=math.cos(t),math.sin(t)
        bproj=lx*dx+ly*dy; disc=bproj**2-(lx*lx+ly*ly-RL*RL); r=R0
        if disc>0: r=max(r,bproj+math.sqrt(disc))
        return r
    N=96; base=[rfun(2*math.pi*k/N) for k in range(N)]
    sm=[sum(base[(k+j)%N]*math.exp(-(j/2.2)**2) for j in range(-6,7))/sum(math.exp(-(j/2.2)**2) for j in range(-6,7)) for k in range(N)]
    sm=[max(a,b) if b-a<0.004 else a*0.4+b*0.6 for a,b in zip(sm,base)]
    def ring(ins,z): return [((sm[k]-ins)*math.cos(2*math.pi*k/N),(sm[k]-ins)*math.sin(2*math.pi*k/N),z) for k in range(N)]
    rings=[ring(0.0012,0),ring(0,0.0012)]+[ring(0.002*(1-math.cos(math.pi/2*k/3)),TH-0.002+0.002*math.sin(math.pi/2*k/3)) for k in range(4)]
    V,F=loft(rings,top_steps=4); o=mesh_obj(name,V,F,"Masa_ustu",uvs=uv_box(0.3,0.08,(0.2,0.1)),mat=M_COAST); place(o,c['X'],c['Y'],H)
coaster("bardak_alti_1",OB['coaster1'],OB['cup1']); coaster("bardak_alti_2",OB['coaster2'],OB['cup2'])
p=OB['plate']; rt=p['rt']; h=0.030; rb=rt-0.022
prof=[(0,0),(rb-0.012,0),(rb-0.006,0.0006),(rb,0.003)]
for k in range(1,9):
    f=k/8; prof.append((rb+(rt-0.004-rb)*math.sin(f*math.pi/2), 0.003+(h-0.007)*(1-math.cos(f*math.pi/2))**0.8))
for k in range(0,7):   # rounded rim, 7 mm thick
    t=math.pi*k/6; prof.append((rt-0.0035-0.0035*math.cos(t)+0.0035, h-0.0035+0.0035*math.sin(t)))
prof+=[(rt-0.008,h-0.004),(rt-0.012,h-0.011),(rb-0.006,0.0095),(rb-0.03,0.0085),(0,0.0085)]
lathe_obj("tabak",prof,"Masa_ustu",M_PLATE,96,uvf=uv_box(0.3,0.08,(0.4,0.2))).location=(p['X'],p['Y'],H)
M_MUFT=pbr("muffin_top",tex="muffin",rough=0.8,spec=0.3)
def muffin(name,m,seed):
    """a chocolate muffin as in the photo: fluted paper cup widening upward (~45 % of the height), a lumpy cracked
    crown that barely overhangs it, flattish on top"""
    r=m['r']; Ht=0.050; hb=0.016; n=72
    prof=[(r*0.76,0.0),(r*0.78,0.002),(r*0.86,hb*0.5),(r*0.93,hb),(r*1.0,hb+0.003),(r*1.04,hb+0.008)]
    for k in range(1,11):
        f=k/10; rr=r*1.04*math.cos(f*math.pi/2); z=hb+0.008+(Ht-hb-0.008)*math.sin(f*math.pi/2)
        prof.append((max(rr,0.0005),z))
    V=[];F=[];UV=[]
    for i,(rr,z) in enumerate(prof):
        for k in range(n):
            t=2*math.pi*k/n; q=Vector((rr*math.cos(t),rr*math.sin(t),z))
            if i<=3:
                q.xy*=1+0.03*math.cos(t*24)*min(1,z/0.003)
            else:
                pp=Vector((q.x*45+seed,q.y*45,q.z*45))
                lump=noise.noise(pp)*0.0055                         # big lobes
                crack=-0.0028*max(0.0,0.35-abs(noise.noise(pp*1.6+Vector((3.1,0,0)))))/0.35   # crevices between lobes
                crumb=noise.noise(Vector((q.x*170,q.y*170+seed,q.z*170)))*0.0011
                dirv=Vector((q.x,q.y,(q.z-hb)*1.6)).normalized(); q+=dirv*(lump+crack+crumb)
            V.append(q); UV.append((k/n,z/Ht))
    for i in range(len(prof)-1):
        for k in range(n): a_=i*n+k; b_=i*n+(k+1)%n; F.append((a_,b_,b_+n,a_+n))
    F.append(tuple(range(n))[::-1])
    o=mesh_obj(name,V,F,"Masa_ustu",mat=M_MUFP); o.data.materials.append(M_MUFT)
    uvl=o.data.uv_layers.new(name="UVMap")
    for poly in o.data.polygons:
        if 4*n<=poly.index<len(F)-1: poly.material_index=1
        for li in poly.loop_indices: uvl.data[li].uv=UV[o.data.loops[li].vertex_index]
    o.location=(m['X'],m['Y'],m['z']+0.0015); return o
muffin("kek_1",OB['muffin1'],3.1); muffin("kek_2",OB['muffin2'],7.7)
s=OB['sphere']; bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=s['R'],location=(s['X'],s['Y'],H+s['R']))
o=bpy.context.object; o.name="pembe_kure_mum"; [c_.objects.unlink(o) for c_ in o.users_collection]; coll("Masa_ustu").objects.link(o); o.data.materials.append(M_PINK)
for p_ in o.data.polygons: p_.use_smooth=True
def wick(name,x,y,z,hh=0.007):
    V,F=lathe([(0,0),(0.0011,0),(0.0011,hh),(0.0006,hh+0.0008),(0,hh+0.001)],10); w=merge(mesh_obj(name,V,F,"Masa_ustu",mat=M_WICK))
    w.location=(x,y,z); w.rotation_euler=(0.15,0.1,0); return w
wick("kure_fitili",s['X'],s['Y'],H+2*s['R']-0.002,0.006)
c=OB['candle']; r,h=c['rb'],c['h']
prof=[(0,0),(r-0.002,0),(r,0.002),(r,h-0.004),(r-0.0012,h-0.0008),(r-0.0035,h),(r-0.008,h-0.0018),(r*0.5,h-0.0035),(0,h-0.004)]
lathe_obj("mum",prof,"Masa_ustu",M_WAX,64).location=(c['X'],c['Y'],H)
wick("mum_fitili",c['X'],c['Y'],H+h-0.0045,0.009)
pt=OB['pot']; r,h=pt['r'],pt['h']
prof=[(0,0),(r*0.82-0.003,0),(r*0.82,0.002),(r*0.95,h*0.6),(r,h-0.004),(r+0.0015,h-0.003),(r+0.0015,h),(r-0.003,h),(r-0.0045,h-0.006),(0,h-0.006)]
lathe_obj("saksi",prof,"Masa_ustu",M_POT,48).location=(pt['X'],pt['Y'],H)
V,F=lathe([(0,0),(r-0.0045,0)],32); F.append(tuple(range(32,64))); so=merge(mesh_obj("toprak",V,F,"Masa_ustu",mat=M_SOIL)); so.location=(pt['X'],pt['Y'],H+h-0.0062)
# plant: a rosette of narrow pointed leaves
import random; rnd=random.Random(4)
V=[];F=[];UV=[]
base=Vector((pt['X'],pt['Y'],H+h-0.006)); top_z=OB['plant_top']
top_z=OB['plant_top']; core=Vector((base.x,base.y,top_z-0.052))
for i in range(800):
    # needles from a core above a short stem: mostly up and outward, the lowest ones level; tips curl up
    el=math.asin(rnd.uniform(-0.88,1.0)); az=rnd.uniform(0,2*math.pi)
    d=Vector((math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el)))
    Ll=rnd.uniform(0.042,0.052)*(1.0 if el>0.0 else 0.95)
    side=d.cross(Vector((0,0,1))); side=side.normalized() if side.length>1e-4 else Vector((1,0,0)); nrm=d.cross(side).normalized()
    w0=rnd.uniform(0.0022,0.0032); seg=6; start=core+d*0.004; row=rnd.random()
    for k in range(seg+1):
        t=k/seg; p_=start+d*(Ll*t)+Vector((0,0,0.007*t*t*(1-max(0,math.sin(el)))))
        w=w0*(1-t)**0.75
        V+= [p_-side*w, p_+nrm*w*0.5, p_+side*w]; UV+=[(t,row)]*3
        if k:
            j=len(V)-6; F+=[(j,j+1,j+4,j+3),(j+1,j+2,j+5,j+4)]
pl=mesh_obj("bitki",V,F,"Masa_ustu",mat=M_LEAF)
uvl=pl.data.uv_layers.new(name="UVMap")
for poly in pl.data.polygons:
    for li in poly.loop_indices: uvl.data[li].uv=UV[pl.data.loops[li].vertex_index]
# dark inner core and a short light stem
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=0.022,location=tuple(core))
co_=bpy.context.object; co_.name="bitki_ic"; [c_.objects.unlink(co_) for c_ in co_.users_collection]; coll("Masa_ustu").objects.link(co_); co_.data.materials.append(M_LEAF_IN)
V,F=lathe([(0.0035,0),(0.003,core.z-base.z-0.015)],12); st=merge(mesh_obj("bitki_govde",V,F,"Masa_ustu",mat=M_STEM)); st.location=base
# napkin on the plate: a folded paper square, its lower half on the plate's floor, the upper half leaning on the rim
pp=OB['plate']; NP=OB.get('napkin')
nx,ny=NP if NP else (pp['X']+0.03,pp['Y']-0.07)
dv=Vector((nx-pp['X'],ny-pp['Y'],0)).normalized(); sd=Vector((-dv.y,dv.x,0)); s_=0.034
P0=Vector((0,0,0)); pts=[]
V=[];F=[]
for i in range(7):
    t=i/6; w=s_*(1-t*0.35)
    lift=0.0 if t<0.45 else (t-0.45)/0.55*0.013
    c=dv*(-0.045+0.042*t)+Vector((0,0,lift+0.0004))
    V+=[tuple(c-sd*w/2),tuple(c+sd*w/2)]
    if i: j=len(V)-4; F.append((j,j+1,j+3,j+2))
nap=mesh_obj("pecete",V,F,"Masa_ustu",mat=M_PAPER); nap.location=(nx,ny,H+0.0088)
sol=nap.modifiers.new("kalinlik","SOLIDIFY"); sol.thickness=0.0006
# ------------------------------------------------------------------ camera from the photo
cd=bpy.data.cameras.new("photo_cam"); cam=bpy.data.objects.new("photo_camera",cd); coll("studio").objects.link(cam)
cd.sensor_fit='HORIZONTAL'; cd.sensor_width=36; cd.lens=CAMP['f']/CAMP['w']*36; cd.clip_start=0.05
cd.shift_x=-(CAMP['cx']-CAMP['w']/2)/CAMP['w']; cd.shift_y=(CAMP['cy']-CAMP['h']/2)/CAMP['w']
Rr=CAMP['R']; Mc=Matrix(((Rr[0][0],-Rr[1][0],-Rr[2][0]),(Rr[0][1],-Rr[1][1],-Rr[2][1]),(Rr[0][2],-Rr[1][2],-Rr[2][2])))
cam.matrix_world=Matrix.Translation(Vector(CAMP['C']))@Mc.to_4x4(); sc.camera=cam
# ------------------------------------------------------------------ render setup
sc.view_settings.view_transform="Standard"
if MODE=="id":
    import random as _r; _g=_r.Random(1)
    for o in [o for o in sc.objects if o.type=="MESH"]:
        m=bpy.data.materials.new("id_"+o.name); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
        e=nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value=(_g.random(),_g.random(),_g.random(),1); out=nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0],out.inputs[0])
        for i in range(len(o.data.materials)): o.data.materials[i]=m
if MODE in ("match","id"):
    sc.render.engine="BLENDER_EEVEE"; sc.render.dither_intensity=0.0
    sc.render.film_transparent=True
    if MODE=="id": sc.render.filter_size=0.01
    world=bpy.data.worlds.new("w"); sc.world=world; world.use_nodes=True; world.node_tree.nodes["Background"].inputs[1].default_value=0
else:
    sc.render.engine="CYCLES"; sc.cycles.device='GPU'; sc.cycles.samples=int(arg("--samples","160")); sc.cycles.use_denoising=True
    try:
        pr=bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type='METAL'; pr.get_devices()
        for d_ in pr.devices: d_.use=True
    except Exception as e: print("GPU setup",e)
    sc.view_settings.view_transform=arg("--vt","AgX"); sc.view_settings.look=arg("--look","None").replace("_"," ") if sc.view_settings.view_transform=="Standard" else "AgX - Base Contrast"
    sc.view_settings.exposure=float(arg("--exposure","0"))
    world=bpy.data.worlds.new("world"); sc.world=world; world.use_nodes=True
    bg=world.node_tree.nodes["Background"]; bg.inputs[0].default_value=(*srgb(235,222,212),1); bg.inputs[1].default_value=float(arg("--world","0.35"))
    def area(nm,loc,target,size,energy,color=(1,1,1),shape='RECTANGLE',size_y=None):
        ld=bpy.data.lights.new(nm,'AREA'); ld.energy=energy; ld.shape=shape; ld.size=size; ld.size_y=size_y or size; ld.color=color
        lo=bpy.data.objects.new(nm,ld); coll("studio").objects.link(lo); lo.location=loc
        lo.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler(); return lo
    # the window: big, soft, from the image's left-back (the curtains), a little warm-white
    wl=Vector((LEFT[0],LEFT[1],0)); wa=Vector((AWAY[0],AWAY[1],0))
    area("pencere",tuple(Vector((0,0,1.4))+wl*float(arg("--wd","3.2"))+wa*float(arg("--wa","0.8"))),(0,0.1,0.5),3.0,float(arg("--win","900")),(1.0,0.97,0.94),size_y=2.4)
    _c=Vector(CAMP['C']); _f=(Vector((0,0,0.5))-_c); _f.z=0; _f.normalize()
    area("dolgu",tuple(Vector((_c.x,_c.y,float(arg("--fillz","1.67"))))+_f*float(arg("--fillfwd","0"))),(0,-0.2,0.45),float(arg("--fillsize","2.6")),float(arg("--fill","120")),(1.0,0.96,0.92))
    EN=json.load(open(os.path.join(HERE,"env.json"))); col_=lambda k: srgb(*EN['colors'][k])
    M_FLOOR=pbr("floor",tex="floor",rough=0.62,spec=0.35,normal="floor_n",nstr=0.4)
    M_WALL=pbr("wall",color=col_('wall'),rough=0.9,spec=0.2)
    M_SKIRT=pbr("supurgelik",color=col_('skirting'),rough=0.5,spec=0.4)
    M_CURT=pbr("curtain",color=col_('curtain_brown'),rough=0.9,spec=0.2,sss=0.0)
    ms=bpy.data.materials.new("tul_perde"); ms.use_nodes=True; nt=ms.node_tree; nt.nodes.clear()
    em=nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value=(*srgb(250,247,248),1)
    # folds: the sheer brighter where it faces the room, a little darker in the folds
    tc=nt.nodes.new("ShaderNodeTexCoord"); wv=nt.nodes.new("ShaderNodeTexWave"); wv.wave_type='BANDS'; wv.bands_direction='X'; wv.inputs['Scale'].default_value=1.0
    wv.inputs['Distortion'].default_value=3.0; wv.inputs['Detail'].default_value=2.0; nt.links.new(tc.outputs['UV'],wv.inputs['Vector'])
    mr=nt.nodes.new("ShaderNodeMapRange"); mr.inputs['To Min'].default_value=0.62*float(arg("--sheer","3.0")); mr.inputs['To Max'].default_value=float(arg("--sheer","3.0"))
    nt.links.new(wv.outputs['Fac'],mr.inputs['Value']); nt.links.new(mr.outputs['Result'],em.inputs[1])
    ou=nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0],ou.inputs[0])
    ang=math.radians(EN['plank_dir_deg']); TU,TV=3*EN['plank_l'],20*EN['plank_w']
    def fuv(co,poly):
        u=co.x*math.cos(ang)+co.y*math.sin(ang); v=-co.x*math.sin(ang)+co.y*math.cos(ang); return (u/TU,v/TV)
    V=[(-4,-4,0),(4,-4,0),(4,4,0),(-4,4,0)]; fo=mesh_obj("zemin",V,[(0,1,2,3)],"oda",uvs=fuv,mat=M_FLOOR,smooth=False)
    cn=Vector((*EN['corner'],0)); er=Vector((*EN['e_r'],0)); ew=Vector((*EN['e_w'],0)); HW=2.7
    def wall(name,e,length,mat,off=0.0,z0=0.0,z1=HW,inward=None):
        n=Vector((-e.y,e.x,0)); n=n if n.dot(Vector((0,0,0))-cn)>0 else -n
        p0=cn+n*off; p1=p0+e*length
        V=[tuple(p0+Vector((0,0,z0))),tuple(p1+Vector((0,0,z0))),tuple(p1+Vector((0,0,z1))),tuple(p0+Vector((0,0,z1)))]
        f=(0,1,2,3) if (p1-p0).cross(Vector((0,0,1))).dot(n)<0 else (3,2,1,0)
        return mesh_obj(name,V,[f],"oda",mat=mat,smooth=False), n
    _,n_r=wall("duvar_sag",er,4.5,M_WALL); _,n_w=wall("duvar_pencere",ew,4.5,M_WALL)
    for nm_,e in (("supurgelik_sag",er),("supurgelik_pencere",ew)):
        n=Vector((-e.y,e.x,0)); n=n if n.dot(-cn)>0 else -n
        V,F=loft([[tuple(cn+n*0.0+e*s_+Vector((0,0,z))) for s_ in (0,4.5)]+[tuple(cn+n*0.015+e*s_+Vector((0,0,z))) for s_ in (4.5,0)] for z in (0,0.075)],top_steps=1)
        mesh_obj(nm_,V,F,"oda",mat=M_SKIRT,smooth=False)
    def pleated(name,s0,s1,off,mat,amp=0.035,period=0.11):
        V=[];F=[]; n=n_w; N=max(8,int((s1-s0)/0.01))
        for i in range(N+1):
            s_=s0+(s1-s0)*i/N; p=cn+ew*s_+n*(off+amp*math.sin(2*math.pi*s_/period))
            V+=[tuple(p+Vector((0,0,0.01))),tuple(p+Vector((0,0,HW)))]
            if i: j=len(V)-4; F.append((j,j+2,j+3,j+1))
        o_=mesh_obj(name,V,F,"oda",mat=mat); uvl=o_.data.uv_layers.new(name="UVMap")
        for poly in o_.data.polygons:
            for li in poly.loop_indices:
                vi=o_.data.loops[li].vertex_index; uvl.data[li].uv=((vi//2)/N*(s1-s0)/period*0.5, (vi%2))
        return o_
    cu_=EN['curtain']; pleated("perde_kahve",cu_['brown_r'],cu_['brown_l'],0.12,M_CURT,0.05,0.10)
    pleated("tul",cu_['brown_l'],4.5,0.16,ms,0.03,0.09)
    # sunlight through the sheer: an area light at the window, behind the sheer, facing the room
    mid=cn+ew*((cu_['brown_l']+3.2)/2)+n_w*0.05+Vector((0,0,1.35))
    ld=bpy.data.lights.new("pencere_isik",'AREA'); ld.shape='RECTANGLE'; ld.size=3.0; ld.size_y=2.4; ld.energy=float(arg("--win","300")); ld.color=(1.0,0.97,0.94)
    lo=bpy.data.objects.new("pencere_isik",ld); coll("studio").objects.link(lo); lo.location=mid
    lo.rotation_euler=(mid+n_w*-1.0).to_track_quat('Z','Y').to_euler() if False else (-n_w).to_track_quat('Z','Y').to_euler()
    for o_ in [o_ for o_ in sc.objects if o_.name=="pencere"]: bpy.data.objects.remove(o_)
    # soft light from above (a ceiling softbox, as in a product shot): lights the tops, leaves the fronts in shade
    if float(arg("--top","0"))>0:
        ld2=bpy.data.lights.new("tavan_isik",'AREA'); ld2.shape='RECTANGLE'; ld2.size=2.4; ld2.size_y=2.0; ld2.energy=float(arg("--top","0")); ld2.color=(1.0,0.97,0.94)
        lo2=bpy.data.objects.new("tavan_isik",ld2); coll("studio").objects.link(lo2); lo2.location=(float(arg("--topx","-0.3")),float(arg("--topy","-0.3")),2.6); lo2.rotation_euler=(0,0,0)
sc.render.resolution_x=RES; sc.render.resolution_y=RES
VIEWS={"photo":None,
       "front34":((-2.2,-2.0,1.45),(0,-0.1,0.45),40),"left34":((-1.9,2.3,1.35),(0,0.1,0.45),40),
       "back34":((1.25,0.15,1.45),(-0.2,0,0.45),24),"right34":((0.3,-1.9,1.3),(-0.1,0.1,0.45),28),
       "top_close":((-0.75,-0.55,1.15),(0.05,-0.02,0.77),45),"stool_close":((-0.9,-1.4,0.85),(0.0,-0.45,0.35),45),
       "bench_close":((-1.1,1.6,0.8),(0.0,0.55,0.35),45),"cups":((-0.55,-0.35,0.92),(-0.28,0.0,0.78),60),
       "plate":((-0.12,-0.25,0.95),(0.15,0.0,0.78),60),"candle":((0.05,-0.3,0.92),(0.40,-0.02,0.80),60),
       "under":((-0.9,-0.9,0.25),(0,0,0.55),35)}
os.makedirs(OUT,exist_ok=True)
for shot in SHOTS:
    if not shot: continue
    if shot=="photo":
        sc.camera=cam
        if arg("--border"):
            x0,y0,x1,y1=map(float,arg("--border").split(",")); sc.render.use_border=True; sc.render.use_crop_to_border=True
            sc.render.border_min_x,sc.render.border_max_x=x0,x1; sc.render.border_min_y,sc.render.border_max_y=1-y1,1-y0
    else:
        loc,tgt,lens=VIEWS[shot]; cdd=bpy.data.cameras.new(shot); co=bpy.data.objects.new(shot,cdd); sc.collection.objects.link(co)
        cdd.lens=lens; cdd.clip_start=0.02; co.location=loc; co.rotation_euler=(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y').to_euler(); sc.camera=co
    sc.render.filepath=os.path.join(OUT,shot+".png"); bpy.ops.render.render(write_still=True)
sc.camera=cam
def tidy_scene():
    for o in [o for o in sc.objects if o.type=="CAMERA" and o!=cam]: bpy.data.objects.remove(o)
    root=bpy.data.objects.new("Masa_Takimi",None); root.empty_display_size=0.05; sc.collection.objects.link(root)
    for cname,c_ in COLL.items():
        if cname in ("studio","oda"): continue
        for o in c_.objects: o.parent=root
    cam.data.display_size=0.15
    for o in sc.objects: o.select_set(False)
    root.select_set(True); bpy.context.view_layer.objects.active=root
    for scr in bpy.data.screens:
        for area_ in scr.areas:
            if area_.type!='VIEW_3D': continue
            sp=area_.spaces[0]; sp.clip_start=0.01; sp.clip_end=100; sp.overlay.show_extras=False; sp.overlay.show_relationship_lines=False; sp.shading.type='MATERIAL'
            r3=sp.region_3d; r3.view_location=(0,0,0.45); r3.view_distance=3.4; r3.view_perspective='PERSP'
            r3.view_rotation=(Vector((-2.2,-2.0,1.45))-Vector((0,-0.1,0.45))).to_track_quat('Z','Y')
if arg("--blend"):
    tidy_scene()
    for i in bpy.data.images:
        if i.source=='FILE': i.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(arg("--blend")))
if arg("--glb"):
    for o in [o for o in sc.objects if o.type in ("LIGHT","CAMERA") or any(c.name in ("oda","studio") for c in o.users_collection)]: bpy.data.objects.remove(o)
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(arg("--glb")),export_format='GLB',export_cameras=False,export_lights=False,export_apply=True)
print("DONE")
