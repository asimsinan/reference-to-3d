from geom import *
from PIL import Image, ImageDraw
im=Image.open('ref.jpg').convert('RGB'); dr=ImageDraw.Draw(im)
def poly(P,c):
    q=[tuple(x) for x in proj(np.array(P))]; dr.line(q+[q[0]],fill=c,width=3)
poly(quad_deck(),(255,0,0))
poly([(D/2,-W/2,0),(D/2,W/2,0),(D/2,W/2,HB),(D/2,-W/2,HB)],(255,128,0))
poly([lid(0,-W/2),lid(LL,-W/2),lid(LL,W/2),lid(0,W/2)],(0,255,255))
poly([lid(0,-W/2,HL),lid(LL,-W/2,HL),lid(LL,W/2,HL),lid(0,W/2,HL)],(255,0,255))
im.resize((1000,750)).save('overlay.jpg')
