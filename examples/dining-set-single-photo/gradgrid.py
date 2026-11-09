import cv2, numpy as np, sys
from PIL import Image, ImageDraw
x0,y0,x1,y1=map(int,sys.argv[1:5]); step=int(sys.argv[5]); out=sys.argv[6]; s=float(sys.argv[7])
im=cv2.imread('ref.jpg'); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(np.float32)
gm=sum(np.hypot(cv2.Sobel(lab[...,i],cv2.CV_32F,1,0),cv2.Sobel(lab[...,i],cv2.CV_32F,0,1)) for i in range(3))
gm=np.clip(gm/np.percentile(gm,99)*255,0,255).astype(np.uint8)
c=Image.fromarray(gm[y0:y1,x0:x1]).convert('RGB').resize((int((x1-x0)*s),int((y1-y0)*s)),Image.NEAREST)
d=ImageDraw.Draw(c)
for x in range((x0//step+1)*step,x1,step):
    X=(x-x0)*s; d.line([(X,0),(X,c.height)],fill=(0,120,0)); d.text((X+2,2),str(x),fill=(255,255,0))
for y in range((y0//step+1)*step,y1,step):
    Y=(y-y0)*s; d.line([(0,Y),(c.width,Y)],fill=(0,120,0)); d.text((2,Y+2),str(y),fill=(255,255,0))
c.save(out)
