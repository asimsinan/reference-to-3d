import sys
from PIL import Image
ims=[Image.open(p) for p in sys.argv[2:]]
h=max(i.size[1] for i in ims); W=sum(i.size[0] for i in ims)+8*(len(ims)-1)
o=Image.new('RGB',(W,h),(0,0,0)); x=0
for i in ims: o.paste(i,(x,0)); x+=i.size[0]+8
o.save(sys.argv[1])
