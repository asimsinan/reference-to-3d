cd "$(dirname "$0")"
SAMPLES=${SAMPLES:-128} /Applications/Blender.app/Contents/MacOS/Blender -b -P build.py -- final out_final.png >/dev/null 2>&1
python3 - <<'PY'
from PIL import Image
import os; d=os.getcwd() + '/'
im=Image.open(d+'out_final.png').convert('RGBA'); im.putalpha(Image.open(d+'out_match.png').getchannel('A')); im.save(d+'out_final_plane.png')
r=Image.open(d+'ref.jpg').resize((885,594)); b=Image.open(d+'out_final.png').convert('RGB').resize((885,594))
s=Image.new('RGB',(885,1188)); s.paste(r,(0,0)); s.paste(b,(0,594)); s.save(d+'sbs_final.jpg')
PY
uv run -q --with numpy,opencv-python-headless python cmp.py out_final_plane.png cmp_final.jpg 2>&1 | grep -v WARN
