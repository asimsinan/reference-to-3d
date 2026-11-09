from cushfit import *
S1=json.load(open('cush.json'))['S1']; cx,cy,th,a,b,rc,zr,zt=S1
out={'S1':S1}
# S2: same stool; free centre and yaw. Only its outline away from S1 (S1 covers its front-left)
m1=cv2.dilate(cv2.imread('mask_S1.png',0),np.ones((9,9),np.uint8))>0
out['S2']=fit('S2',[0.25,-0.46,0.0,a,b,rc,zr,zt],keep=lambda x,y: ~m1[np.clip(y.astype(int),0,999),np.clip(x.astype(int),0,999)] & ~((x<760)&(y>560)),
              fixed=dict(a=a,b=b,rc=rc,zr=zr,zt=zt)).tolist()
# bench: same section (b, rc, heights), free length and centre; its far edge against the curtain is unreliable: keep
# the near (lower) outline and the left end only
out['bench']=fit('bench',[0.016,0.572,0.0,0.46,b,rc,zr,zt],keep=lambda x,y: (y> 530+0.15*(x-80)) | (x<100),
              fixed=dict(b=b,rc=rc,zr=zr,zt=zt)).tolist()
json.dump(out,open('cush.json','w'),indent=1)
