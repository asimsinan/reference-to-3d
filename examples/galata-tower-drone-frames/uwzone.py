import json,numpy as np,cv2,sys
from unwrap import unwrap
import unwrap as U
S=json.load(open('solve.json')); az=S['g']['az']
zone=sys.argv[1]; r=float(sys.argv[2]); z0=float(sys.argv[3]); z1=float(sys.argv[4])
rows=[]
for k in ['r2','r3','r4']:
    o,w=unwrap(k,z0=z0,z1=z1,dz=0.03,dth=0.25,rfun=lambda Z: np.full_like(Z,r),az=az[k])
    o[w<=0.1]=(255,0,255); o=np.roll(o,720,1)[:,360:1080]
    o=cv2.resize(o,None,fx=1.5,fy=1.5)
    for d in range(-90,91,10):
        x=int((d+90)*4*1.5); cv2.line(o,(x,0),(x,10),(0,255,255),2); cv2.putText(o,str(d),(x+2,22),0,0.45,(0,255,255),1)
    cv2.putText(o,k,(5,o.shape[0]-6),0,0.7,(255,0,255),2); rows.append(o)
cv2.imwrite('out/uwz_%s.jpg'%zone,np.vstack(rows))
