"""Showcase: the reference photo | the model (real materials) from the photo's camera | sides the photo does not show.
Reads photo.jpg and real_final/{photo_view,view_q_front_right,view_rear,view_top}.png; writes cologne_showcase.jpg"""
from PIL import Image, ImageDraw, ImageFont
H=600; Wp=450; GAP=6
box=(400,300,1160,1760)                      # the bottle in the photo and in the photo-camera render (same frame)
ph=Image.open('photo.jpg').convert('RGB').crop(box)
pv=Image.open('real_final/photo_view.png').convert('RGB').crop(box)
def sq(n):                                    # 900x900 studio view -> portrait 3:4 centre crop
    im=Image.open(f'real_final/view_{n}.png').convert('RGB'); return im.crop((112,0,787,900))
panels=[(ph,'Reference photo'),(pv,'Model · same camera'),(sq('q_front_right'),'Model · three-quarter'),
        (sq('rear'),'Model · back (not in the photo)'),(sq('top'),'Model · from above')]
out=Image.new('RGB',(len(panels)*Wp+(len(panels)-1)*GAP,H),'white')
font=ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc',18)
for i,(im,lab) in enumerate(panels):
    im=im.resize((Wp,H),Image.LANCZOS); x=i*(Wp+GAP); out.paste(im,(x,0))
    d=ImageDraw.Draw(out,'RGBA'); tw=d.textlength(lab,font=font)
    d.rounded_rectangle((x+12,H-42,x+12+tw+20,H-12),radius=8,fill=(0,0,0,150))
    d.text((x+22,H-38),lab,font=font,fill=(255,255,255,255))
out.save('cologne_showcase.jpg',quality=88); print(out.size)
