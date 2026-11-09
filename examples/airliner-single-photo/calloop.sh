cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
pass() { for P in sunpass skylow skyhigh; do PCT=50 SAMPLES=64 $B -b -P build.py -- $P pass_$P.exr > /dev/null 2>&1; done; FILL_EL=25 FILL_AZ=240 PCT=50 SAMPLES=64 $B -b -P build.py -- fillpass fills/fill_25_240_.exr >/dev/null 2>&1; }
WHITEGROUND=1 pass; uv run -q --with numpy,opencv-python-headless python groundcal.py
pass; uv run -q --with numpy,scipy,opencv-python-headless python calfit.py ${WG:-1.0} fills/fill_25_240_.exr
