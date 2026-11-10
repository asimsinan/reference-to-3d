#!/bin/zsh
# run2.sh [views] : geometry -> bake -> photo textures -> irradiance (2 passes) -> albedo -> final renders
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=(uv run -q --with numpy --with scipy --with opencv-python-headless python); [[ -n "$PYX" ]] && PY=(${=PYX})   # PYX: a ready python when uv waits on its cache lock
if [[ "$1" != "nogeo" ]]; then
$B -b -P bake.py 2>&1 | grep -E "Traceback|rror:" | head -3
$PY texbuild.py 2>/dev/null >/dev/null
$B -b bake/geom.blend -P irr.py -- 1 2>&1 | grep -E "Traceback|rror:"; $PY albedo.py 2>/dev/null >/dev/null
else shift; fi
$B -b bake/geom.blend -P irr.py -- 2 2>&1 | grep -E "Traceback|rror:"; $PY albedo.py 2>/dev/null >/dev/null
$PY mkextra.py 2>/dev/null >/dev/null
$B -b bake/geom.blend -P final.py -- "$@" 2>&1 | grep -E "Traceback|rror:"
