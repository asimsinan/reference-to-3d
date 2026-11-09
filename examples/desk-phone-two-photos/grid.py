import sys
from PIL import Image, ImageDraw
import os; im=Image.open(os.environ.get('IMG','ref.jpg')).convert('RGB')
x0,y0,x1,y1=map(int,sys.argv[1:5]); step=int(sys.argv[5]); out=sys.argv[6]
c=im.crop((x0,y0,x1,y1)); s=float(sys.argv[7]) if len(sys.argv)>7 else 1
c=c.resize((int(c.width*s),int(c.height*s)))
d=ImageDraw.Draw(c)
for x in range((x0//step+1)*step,x1,step):
    X=(x-x0)*s; d.line([(X,0),(X,c.height)],fill=(0,255,0)); d.text((X+2,2),str(x),fill=(255,255,0))
for y in range((y0//step+1)*step,y1,step):
    Y=(y-y0)*s; d.line([(0,Y),(c.width,Y)],fill=(0,255,0)); d.text((2,Y+2),str(y),fill=(255,255,0))
c.save(out)
