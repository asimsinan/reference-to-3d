"""mont.py PHOTO OUT HALF SCALE name:x,y name:x,y ...  -- tiles of zoomed crops with full-res grid labels (step 5, labels every 10)."""
import sys
from PIL import Image, ImageDraw, ImageFont
img=Image.open(sys.argv[1]).convert('RGB'); out=sys.argv[2]; h=int(sys.argv[3]); s=float(sys.argv[4])
items=[a.split(':') for a in sys.argv[5:]]
tiles=[]
for name,xy in items:
    cx,cy=map(int,xy.split(','))
    x0,y0=cx-h,cy-h; c=img.crop((x0,y0,cx+h,cy+h)).resize((int(2*h*s),int(2*h*s)),Image.NEAREST)
    d=ImageDraw.Draw(c)
    for x in range((x0//5+1)*5,cx+h,5):
        X=(x-x0)*s; col=(255,0,0) if x%10==0 else (255,255,0)
        d.line([(X,0),(X,c.size[1])],fill=col,width=1)
        if x%20==0: d.text((X+2,12),str(x),fill=(0,255,255))
    for y in range((y0//5+1)*5,cy+h,5):
        Y=(y-y0)*s; col=(255,0,0) if y%10==0 else (255,255,0)
        d.line([(0,Y),(c.size[0],Y)],fill=col,width=1)
        if y%20==0: d.text((2,Y+2),str(y),fill=(0,255,255))
    d.rectangle([0,0,c.size[0]-1,c.size[1]-1],outline=(255,255,255))
    d.rectangle([0,0,90,11],fill=(0,0,0)); d.text((2,0),name,fill=(255,255,255))
    tiles.append(c)
n=len(tiles); cols=min(4,n); rows=(n+cols-1)//cols; T=tiles[0].size[0]
M=Image.new('RGB',(cols*T,rows*T),(40,40,40))
for i,t in enumerate(tiles): M.paste(t,((i%cols)*T,(i//cols)*T))
M.save(out)
