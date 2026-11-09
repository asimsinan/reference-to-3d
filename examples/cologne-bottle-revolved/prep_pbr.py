"""Cylindrical label texture for the real-material version: the photo rectified round the axis (fold at +-A, the
print-free back plate beyond), the cylinder's shading divided out per column (a cream band of the label), plus the
label's z-range, the yellow band's z and the liquid level read through the camera.
writes label_albedo.png (2048x1024, u=0.5 front, v=z/h), label_mask.png, pbr_info.json, pbr_vis.jpg"""
import cv2,numpy as np,json,math
import cam as C
P=C.P; INFO=json.load(open('tex_info.json')); X0,Y0,X1,Y1=INFO['crop']; UP=INFO['up']
front=cv2.imread('tex_front.png'); back=cv2.imread('tex_back.png')
R,h=P['R'],P['h']; A=math.radians(72)
NU,NV=2048,1024
phi=(np.arange(NU)+0.5)/NU*2*np.pi-np.pi            # -pi..pi, front (0) at the centre
z=(np.arange(NV)+0.5)/NV*h                           # bottom row = z 0 -> flip later so v=0 is the bottom
def fold(ph):
    f=ph.copy(); m=np.abs(ph)>A; f[m]=np.sign(ph[m])*A*(np.pi-np.abs(ph[m]))/(np.pi-A); return f
PH,Z=np.meshgrid(phi,z); F=fold(PH)
rr=P['rb']+(R-P['rb'])*Z/h
X=np.stack([rr*np.cos(F),rr*np.sin(F),Z],-1).reshape(-1,3)
uv=C.proj(X).reshape(NV,NU,2)
mx=((uv[...,0]-X0)*UP).astype(np.float32); my=((uv[...,1]-Y0)*UP).astype(np.float32)
rf=cv2.remap(front,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
rb=cv2.remap(back,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
isback=np.abs(PH)>A
rect=np.where(isback[...,None],rb,rf)
# heights through the camera: the front point (phi=0) of the cylinder at a photo row
def z_at_row(v,u=780.0):
    Cc,d=C.ray(np.array([u]),np.array([v])); Cc=Cc; d=d[0]
    # intersect with the cylinder r=R
    a=d[0]**2+d[1]**2; b=2*(Cc[0]*d[0]+Cc[1]*d[1]); c=Cc[0]**2+Cc[1]**2-R*R
    t=(-b-math.sqrt(b*b-4*a*c))/(2*a); return float(Cc[2]+t*d[2])
z_top=z_at_row(996); z_bot=z_at_row(1578); z_band=z_at_row(1424); z_liq=z_at_row(925); z_cream0=z_at_row(1065); z_cream1=z_at_row(1025)
print('label z %.4f..%.4f  yellow band top %.4f  liquid %.4f  cream band %.4f..%.4f'%(z_bot,z_top,z_band,z_liq,z_cream0,z_cream1))
# shading per column from the plain cream band
rows=(z>=z_cream0)&(z<=z_cream1)
lum=cv2.cvtColor(rect,cv2.COLOR_BGR2GRAY).astype(np.float32)
s=np.median(lum[rows],0); s=cv2.GaussianBlur(s[None],(0,0),12)[0]
s=s/np.percentile(s,97); s=np.clip(s,0.35,1.0)
alb=np.clip(rect.astype(np.float32)/s[None,:,None],0,255).astype(np.uint8)
# the label band: slightly inside the measured edges; soft 2-px edge
mask=((z>=z_bot)&(z<=z_top)).astype(np.float32)[:,None]*np.ones((1,NU),np.float32)
mask=cv2.GaussianBlur(mask,(0,0),1.0)
alb=alb[::-1]; mask=mask[::-1]      # v=0 at the bottom (image row 0 = top = z h)
cv2.imwrite('label_albedo.png',alb); cv2.imwrite('label_mask.png',(mask*255).astype(np.uint8))
json.dump(dict(z_top=z_top,z_bot=z_bot,z_band=z_band,z_liq=z_liq,A_deg=72),open('pbr_info.json','w'),indent=1)
vis=np.vstack([cv2.resize(rect[::-1],(1024,512)),cv2.resize(alb,(1024,512))]); cv2.imwrite('pbr_vis.jpg',vis)
print('shading min %.2f'%s.min())
# the maps the real-material shader reads on the same cylindrical UVs (image maps, not Mix nodes: glTF keeps them)
m=mask
cv2.imwrite('label_trans.png',((1-m)*255).astype(np.uint8))              # transmission: clear PET outside the label
cv2.imwrite('label_rough.png',(8+m*(140-8)).astype(np.uint8))              # roughness 0.03 clear, 0.55 paper
alb_m=alb.copy(); alb_m[m<0.5]=(255,255,255)                               # white base colour where the PET is clear
cv2.imwrite('label_albedo_m.png',alb_m)
