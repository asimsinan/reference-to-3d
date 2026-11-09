set -e
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b -P bake.py 2>&1 | grep -iE "error|traceback" | head -3 || true
uv run -q --with numpy,opencv-python-headless python texbuild.py > /dev/null
$B -b -P build.py -- match out_match.png 2>&1 | grep -iE "error|traceback" | head -3 || true
uv run -q --with numpy,opencv-python-headless python cmp.py out_match.png cmp_match.jpg 2>&1 | grep -v WARN
