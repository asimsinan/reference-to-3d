set -e
cd ~/Desktop/masa3d/work
L=$(cat light_args.txt)
B=/Applications/Blender.app/Contents/MacOS/Blender
rm -f ../renders/*.png
$B -b -P build.py -- --mode final --out ../renders --shots photo --res 1000 --samples 256 --vt Standard ${=L} 2>&1 | grep -E "Error|Traceback" || true
$B -b -P build.py -- --mode final --out ../renders --shots front34,left34,back34,right34,top_close,stool_close,bench_close,cups,plate,candle --res 1200 --samples 160 --vt Standard ${=L} --blend "$HOME/Desktop/masa3d/masa_takimi.blend" 2>&1 | grep -E "Error|Traceback|DONE" || true
$B -b -P build.py -- --mode final --out /tmp/x_unused --shots "" --vt Standard ${=L} --glb "$HOME/Desktop/masa3d/masa_takimi.glb" 2>&1 | grep -E "Error|Traceback|DONE" || true
$B -b -P build.py -- --mode match --out ../renders_foto --shots photo --blend "$HOME/Desktop/masa3d/masa_takimi_foto_projeksiyon.blend" 2>&1 | grep -E "Error|Traceback|DONE" || true
$B -b "$HOME/Desktop/masa3d/masa_takimi.blend" -P fix_blend.py >/dev/null 2>&1 || true
$B -b "$HOME/Desktop/masa3d/masa_takimi_foto_projeksiyon.blend" -P fix_blend.py >/dev/null 2>&1 || true
rm -f ~/Desktop/masa3d/*.blend1
uv run --with numpy --with opencv-python-headless python calib.py ../renders/photo.png | tail -1
uv run --with numpy --with opencv-python-headless python cmp.py ../renders_foto/photo.png /tmp/_c.jpg 2>/dev/null | head -1
echo FINISHED
