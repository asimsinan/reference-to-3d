"""Showcase: the reference photo | the real-material model from the photo's camera | three views the photo does not show."""
from PIL import Image, ImageDraw, ImageFont
H=600; Wp=450; GAP=6; BG=(226,226,228)
ph=Image.open('photo.jpg').convert('RGB').crop((300,560,1360,1973))
def rg(n,crop=None):
    im=Image.open(f'showcase/sc_{n}.png').convert('RGBA'); b=Image.new('RGBA',im.size,BG+(255,)); b.alpha_composite(im); b=b.convert('RGB')
    return b.crop(crop) if crop else b
panels=[(ph,'Reference photo'),(rg('photo_cam',(300,560,1360,1973)),'Model · same camera'),(rg('q_right'),'Model · right (not in the photo)'),
        (rg('q_rear'),'Model · from behind'),(rg('top'),'Model · from above')]
out=Image.new('RGB',(len(panels)*Wp+(len(panels)-1)*GAP,H),'white')
font=ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc',18)
for i,(im,lab) in enumerate(panels):
    im=im.resize((Wp,H),Image.LANCZOS); x=i*(Wp+GAP); out.paste(im,(x,0))
    d=ImageDraw.Draw(out,'RGBA'); tw=d.textlength(lab,font=font)
    d.rounded_rectangle((x+12,H-42,x+12+tw+20,H-12),radius=8,fill=(0,0,0,150))
    d.text((x+22,H-38),lab,font=font,fill=(255,255,255,255))
out.save('pen_holder_showcase.jpg',quality=88); print(out.size)
