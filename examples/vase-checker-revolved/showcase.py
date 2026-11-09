"""vase_showcase.jpg: the reference photo | the model from the photo's camera | three views the photo does not show"""
from PIL import Image, ImageDraw, ImageFont
H=600; Wp=450; GAP=6
ph=Image.open('../photo.jpg').convert('RGB').crop((0,50,600,850))
pc=Image.open('showcase/s_photo_cam.png').convert('RGB').crop((0,100,1200,1700))
rg=lambda n: Image.open(f'showcase/s_{n}.png').convert('RGB')
panels=[(ph,'Reference photo'),(pc,'Model · same camera'),(rg('three_quarter'),'Model · three-quarter'),
        (rg('back'),'Model · back (not in the photo)'),(rg('top'),'Model · from above')]
out=Image.new('RGB',(len(panels)*Wp+(len(panels)-1)*GAP,H),'white')
font=ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc',18)
for i,(im,lab) in enumerate(panels):
    im=im.resize((Wp,H),Image.LANCZOS); x=i*(Wp+GAP); out.paste(im,(x,0))
    d=ImageDraw.Draw(out,'RGBA'); tw=d.textlength(lab,font=font)
    d.rounded_rectangle((x+12,H-42,x+12+tw+20,H-12),radius=8,fill=(0,0,0,150))
    d.text((x+22,H-38),lab,font=font,fill=(255,255,255,255))
out.save('vase_showcase.jpg',quality=88); print(out.size)
