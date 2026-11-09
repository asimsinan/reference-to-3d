# full chain: bake -> photo textures -> match compare -> albedo (+gain cal x2) -> final compare
set -e
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b -P bake.py >/dev/null 2>&1
bash run_match.sh | head -1
uv run -q --with numpy,opencv-python-headless python albedo.py > /dev/null
bash final_cmp.sh | head -1
for i in 1 2; do uv run -q --with numpy,opencv-python-headless python albedo_cal.py >/dev/null; uv run -q --with numpy,opencv-python-headless python albedo.py > /dev/null; done
bash final_cmp.sh
