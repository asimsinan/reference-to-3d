"""marks.py PHOTO PTS.json KEY OUT X0 Y0 X1 Y1 SCALE -- draw labelled crosshairs of pts[KEY] (name -> [x,y]) on a zoomed crop."""
import sys, json
from PIL import Image, ImageDraw
img=Image.open(sys.argv[1]).convert('RGB'); P=json.load(open(sys.argv[2]))[sys.argv[3]]
out=sys.argv[4]; x0,y0,x1,y1=map(int,sys.argv[5:9]); s=float(sys.argv[9])
c=img.crop((x0,y0,x1,y1)).resize((int((x1-x0)*s),int((y1-y0)*s)),Image.LANCZOS); d=ImageDraw.Draw(c)
for x in range((x0//50+1)*50,x1,50):
    X=(x-x0)*s; d.line([(X,0),(X,8)],fill=(255,255,0)); d.text((X+1,8),str(x),fill=(255,255,0))
for y in range((y0//50+1)*50,y1,50):
    Y=(y-y0)*s; d.line([(0,Y),(8,Y)],fill=(255,255,0)); d.text((9,Y-5),str(y),fill=(255,255,0))
for k,v in P.items():
    if v is None or isinstance(v[0],list): continue
    X=(v[0]-x0)*s; Y=(v[1]-y0)*s
    if not(0<=X<c.size[0] and 0<=Y<c.size[1]): continue
    r=10
    d.line([(X-r,Y),(X-3,Y)],fill=(0,255,0)); d.line([(X+3,Y),(X+r,Y)],fill=(0,255,0))
    d.line([(X,Y-r),(X,Y-3)],fill=(0,255,0)); d.line([(X,Y+3),(X,Y+r)],fill=(0,255,0))
    d.text((X+5,Y+4),k,fill=(0,255,255))
c.save(out)
