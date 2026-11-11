import cv2,numpy as np
P=cv2.imread('ref2/p8.png'); r=cv2.imread('out/real34_8.png',cv2.IMREAD_UNCHANGED)
out=[]
for n,(x0,y0,x1,y1) in {'backL1':(265,560,385,700),'backR1':(940,590,1060,740),'cushL1':(230,760,370,830),'floor':(560,650,760,840),'wains':(1150,620,1270,700),'ceil':(820,40,940,90)}.items():
    p=np.median(P[y0:y1,x0:x1].reshape(-1,3).mean(1)); q=np.median(r[y0:y1,x0:x1,:3].reshape(-1,3).mean(1)); out.append('%s %d/%d'%(n,p,q))
print('  '.join(out))
