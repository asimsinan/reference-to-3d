"""zoom.py IMG OUT name:x:y[:half] ... -- montage of zoomed crops (scale 6, grid every 2 px, labels every 10) around approx points."""
import sys
from PIL import Image, ImageDraw
im=Image.open(sys.argv[1]).convert('RGB'); out=sys.argv[2]; S=6; tiles=[]
for spec in sys.argv[3:]:
    p=spec.split(':'); n=p[0]; x=int(float(p[1])); y=int(float(p[2])); h=int(p[3]) if len(p)>3 else 16
    x0,y0=x-h,y-h; c=im.crop((x0,y0,x+h,y+h)).resize((2*h*S,2*h*S),Image.NEAREST); d=ImageDraw.Draw(c)
    for k in range(2*h+1):
        X=k*S; v=x0+k; col=(255,0,0) if v%10==0 else (255,255,0)
        if v%2==0: d.line([(X,0),(X,4 if v%10 else 2*h*S)],fill=col,width=1)
        if v%10==0: d.text((X+2,10),str(v),fill=(255,0,0))
        v=y0+k; Y=k*S; col=(0,255,255) if v%10==0 else (255,255,0)
        if v%2==0: d.line([(0,Y),(4 if v%10 else 2*h*S,Y)],fill=col,width=1)
        if v%10==0: d.text((10,Y+2),str(v),fill=(0,255,255))
    d.text((4,2*h*S-14),n,fill=(255,0,255)); tiles.append(c)
cols=4; w=max(t.size[0] for t in tiles); hh=max(t.size[1] for t in tiles); rows=(len(tiles)+cols-1)//cols
M=Image.new('RGB',(cols*(w+4),rows*(hh+4)),(40,40,40))
for i,t in enumerate(tiles): M.paste(t,((i%cols)*(w+4),(i//cols)*(hh+4)))
M.save(out)
