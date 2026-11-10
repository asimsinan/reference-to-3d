#!/bin/zsh
# geoloop.sh : geometry only -> id renders -> GrabCut IoU (fast shape check)
cd "$(dirname "$0")"; B=/Applications/Blender.app/Contents/MacOS/Blender; PY=(uv run -q --with numpy --with scipy --with opencv-python-headless python); [[ -n "$PYX" ]] && PY=(${=PYX})
$B -b -P mkshape.py 2>&1 | grep -E "Traceback|rror:"
$B -b bake/shape.blend -P idr.py 2>&1 | grep -E "Traceback|rror:"
"${PY[@]}" iouf.py 2>/dev/null
