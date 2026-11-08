import sys
from PIL import Image, ImageDraw
x0,y0,x1,y1,s,out=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),float(sys.argv[5]),sys.argv[6]
im=Image.open('ref.png')
c=im.crop((x0,y0,x1,y1)); c=c.resize((int((x1-x0)*s),int((y1-y0)*s)))
d=ImageDraw.Draw(c)
st=int(sys.argv[7]) if len(sys.argv)>7 else 25
for x in range((x0//st+1)*st,x1,st):
  X=(x-x0)*s; d.line([(X,0),(X,c.size[1])],fill=(255,0,0) if x%100==0 else (255,255,0))
  if x%(2*st)==0: d.text((X+2,2),str(x),fill=(255,80,80))
for y in range((y0//st+1)*st,y1,st):
  Y=(y-y0)*s; d.line([(0,Y),(c.size[0],Y)],fill=(255,0,0) if y%100==0 else (255,255,0))
  if y%(2*st)==0: d.text((2,Y+2),str(y),fill=(255,80,80))
c.save(out)
