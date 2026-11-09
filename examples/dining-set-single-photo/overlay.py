from geom import *
from PIL import Image, ImageDraw
im=Image.open('ref.jpg').convert('RGB').resize((2000,2000)); dr=ImageDraw.Draw(im)
def poly(P,c,close=True,w=2):
    q=[tuple(2*x) for x in proj(np.array(P))]; dr.line(q+([q[0]] if close else []),fill=c,width=w)
def rect(z,c): poly([(-L/2,-W/2,z),(L/2,-W/2,z),(L/2,W/2,z),(-L/2,W/2,z)],c)
rect(H,(255,0,0)); rect(H-T,(255,128,0))
for sx in (-1,1):
    for sy in (-1,1):
        poly([(sx*C_['bx'],sy*C_['by'],0),(sx*C_['bx'],sy*C_['by'],H-T)],(0,255,255),False)
im.save('overlay.jpg')
