"""grid.py photo.jpg x0 y0 x1 y1 step scale out.jpg : crop with a labelled grid"""
import sys,cv2
im=cv2.imread(sys.argv[1]); x0,y0,x1,y1,st=map(int,sys.argv[2:7]); sc=float(sys.argv[7]); out=sys.argv[8]
c=im[y0:y1,x0:x1].copy(); c=cv2.resize(c,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
for x in range((x0//st+1)*st,x1,st):
    X=int((x-x0)*sc); cv2.line(c,(X,0),(X,c.shape[0]),(0,0,255) if x%(st*5)==0 else (0,180,255),1)
    cv2.putText(c,str(x),(X+2,12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
for y in range((y0//st+1)*st,y1,st):
    Y=int((y-y0)*sc); cv2.line(c,(0,Y),(c.shape[1],Y),(0,0,255) if y%(st*5)==0 else (0,180,255),1)
    cv2.putText(c,str(y),(2,Y-2),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
cv2.imwrite(out,c)
