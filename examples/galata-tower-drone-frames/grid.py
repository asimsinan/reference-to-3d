"""grid.py IMG X0 Y0 X1 Y1 SCALE OUT [STEP]  -- crop of the full-res image with a pixel grid (full-res coordinates)."""
import sys
from PIL import Image, ImageDraw
img,x0,y0,x1,y1,s,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),float(sys.argv[6]),sys.argv[7]
st=int(sys.argv[8]) if len(sys.argv)>8 else 50
im=Image.open(img); c=im.crop((x0,y0,x1,y1)); c=c.resize((int((x1-x0)*s),int((y1-y0)*s)))
d=ImageDraw.Draw(c)
for x in range((x0//st+1)*st,x1,st):
  X=(x-x0)*s; d.line([(X,0),(X,c.size[1])],fill=(255,0,0) if x%(st*4)==0 else (255,255,0),width=1)
  if x%(st*2)==0: d.text((X+2,2),str(x),fill=(255,0,0))
for y in range((y0//st+1)*st,y1,st):
  Y=(y-y0)*s; d.line([(0,Y),(c.size[0],Y)],fill=(255,0,0) if y%(st*4)==0 else (255,255,0),width=1)
  if y%(st*2)==0: d.text((2,Y+2),str(y),fill=(255,0,0))
c.save(out)
