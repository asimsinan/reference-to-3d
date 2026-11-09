"""Draw the solved model's silhouette over the photo (union of projected discs of body + tilted head)."""
import json,numpy as np,cv2
import cam as C
P=C.P; im=cv2.imread('photo.jpg'); Rm=C.head_rot(P['PHI']); h=P['h']
def parts(P):
    body=[]; rb,rf,rs,R=P['rb'],P['rf'],P['rs'],P['R']
    for t in np.linspace(0,np.pi/2,8): body.append((rf-rf*np.cos(t), rb-rf+rf*np.sin(t)))
    for z in np.linspace(rf,h-rs,20): body.append((z, rb+(R-rb)*z/h))
    for t in np.linspace(0,np.pi/2,8): body.append((h-rs+rs*np.sin(t), R-rs+rs*np.cos(t)))
    body.append((h,0.6*P['rc0'])); body.append((P['zc0']+0.001,0.6*P['rc0']))
    head=[]
    for z in np.linspace(P['zc0'],P['zc1'],6): head.append((z,P['rc0']+(P['rc1']-P['rc0'])*(z-P['zc0'])/(P['zc1']-P['zc0'])))
    for z in np.linspace(P['zc1'],P['zk1']-P['KF'],10): head.append((z,P['rk0']+(P['rk1']-P['rk0'])*(z-P['zc1'])/(P['zk1']-P['zc1'])))
    for t in np.linspace(0,np.pi/2,6): head.append((P['zk1']-P['KF']+P['KF']*np.sin(t), P['rk1']-P['KF']+P['KF']*np.cos(t)))
    head.append((P['zk1'],1e-4))
    return body,head
ang=np.linspace(0,2*np.pi,360,endpoint=False)
def disc(z,r,Rm=None):
    X=np.stack([r*np.cos(ang),r*np.sin(ang),np.full_like(ang,z)],1)
    if Rm is not None: X=(X-[0,0,h])@Rm.T+[0,0,h]
    return C.proj(X)
m=np.zeros(im.shape[:2],np.uint8)
body,head=parts(P)
for pr,Rm_ in ((body,None),(head,Rm)):
    for (z0,r0),(z1,r1) in zip(pr[:-1],pr[1:]):
        a=disc(z0,max(r0,1e-5),Rm_); b=disc(z1,max(r1,1e-5),Rm_)
        cv2.fillConvexPoly(m,cv2.convexHull(np.round(np.vstack([a,b])).astype(np.int32)),255)
cv2.imwrite('model_mask.png',m)
cnt=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0]
vis=im.copy(); cv2.drawContours(vis,cnt,-1,(0,0,255),2)
cv2.imwrite('overlay.jpg',vis[430:1700,560:1020])
sil=cv2.imread('mask_photo.png',0)>0
print('IoU vs grabcut (rows<1545): %.3f'%(((m>0)&sil)[:1545].sum()/((m>0)|sil)[:1545].sum()))
