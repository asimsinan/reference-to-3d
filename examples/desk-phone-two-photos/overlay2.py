from geom import *
from PIL import Image, ImageDraw
for name,cam,img,crop,outn in [('front',cam1,'ref.jpg',(200,700,1300,1600),'overlay.jpg'),('side',cam2,'side.jpg',(100,540,1200,1120),'overlay_side.jpg')]:
    im=Image.open(img).convert('RGB'); dr=ImageDraw.Draw(im)
    def poly(P,c,w=3,close=True):
        q=[tuple(x) for x in cam.proj(np.array(P,float))]; dr.line(q+([q[0]] if close else []),fill=c,width=w)
    pl=plan()
    poly([(x,y,ztop(x)) for x,y in pl],(255,0,0)); poly([(x,y,0) for x,y in pl],(255,128,0))
    poly([(x,y,zband(x)) for x,y in pl],(0,200,255),w=2); poly([(x,y,zband(x)-T) for x,y in pl],(0,200,255),w=2)
    for i in range(4):
        for j in range(3):
            x=X0+i*PX; y=Y0+j*PY; kw=0.75*PY
            top=[(x-KD/2,y-kw/2),(x-KD/2,y+kw/2),(x+KD/2,y+kw/2),(x+KD/2,y-kw/2)]
            poly([(a,b,ztop(a)+KH) for a,b in top],(0,255,0),w=2)
    im.crop(crop).save(outn)
