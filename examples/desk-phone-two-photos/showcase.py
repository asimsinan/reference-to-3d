"""Showcase: the two reference photos | the model (real materials, Cycles) from the front photo's camera | sides.
Reads ref.jpg, side.jpg, r_show/{photo,show_q,show_rear,show_top}.png; writes phone_showcase.jpg"""
from PIL import Image, ImageDraw, ImageFont
H=520; GAP=6
def crop_to(im, box, w):
    im=im.convert('RGB').crop(box); return im.resize((w, H), Image.LANCZOS)
ref=Image.open('ref.jpg'); side=Image.open('side.jpg'); pv=Image.open('r_show/photo.png')
sx=pv.width/ref.width
panels=[(crop_to(ref,(180,740,1250,1650),610),'Reference · front'),
        (crop_to(side,(100,520,1200,1150),610),'Reference · side'),
        (crop_to(pv,tuple(int(v*sx) for v in (180,740,1250,1650)),610),'Model · front photo\'s camera'),
        (crop_to(Image.open('r_show/show_q.png'),(150,190,850,690),610),'Model · three-quarter'),
        (crop_to(Image.open('r_show/show_rear.png'),(150,190,850,690),610),'Model · back (not in the photos)'),
        (crop_to(Image.open('r_show/show_top.png'),(190,95,810,623),610),'Model · from above')]
cols=3; Wp=610
out=Image.new('RGB',(cols*Wp+(cols-1)*GAP, 2*H+GAP),'white')
font=ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc',20)
for i,(im,lab) in enumerate(panels):
    x=(i%cols)*(Wp+GAP); y=(i//cols)*(H+GAP); out.paste(im,(x,y))
    d=ImageDraw.Draw(out,'RGBA'); tw=d.textlength(lab,font=font)
    d.rounded_rectangle((x+12,y+H-44,x+12+tw+22,y+H-12),radius=8,fill=(0,0,0,150))
    d.text((x+23,y+H-40),lab,font=font,fill=(255,255,255,255))
out.save('phone_showcase.jpg',quality=88); print(out.size)
