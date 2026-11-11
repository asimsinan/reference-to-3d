#!/bin/zsh
# render both photo cameras with their own sun, measure, update albedo levels; N rounds
for i in $(seq 1 ${1:-3}); do
  LEV=$( [ -f lev34.json ] && python3 -c "import json;print(','.join('%s=%.4f'%(k,v) for k,v in json.load(open('lev34.json')).items()))" )
  env LEV=$LEV SUNDIR=-0.81,0.0,0.57 KS=9 SAMPLES=16 /Applications/Blender.app/Contents/MacOS/Blender -b bake34/baked.blend -P final34.py -- real cams > /dev/null 2>&1
  env LEV=$LEV SUNDIR=0.47,0.17,0.87 KS=13 SAMPLES=16 /Applications/Blender.app/Contents/MacOS/Blender -b bake34/baked.blend -P final34.py -- real cams > /dev/null 2>&1
  echo "== round $i  $(uv run -q --no-project --with numpy --with opencv-python-headless python cal34.py real 2>/dev/null | grep -E '^photo|^ALL' | tr '\n' ' ')"
  uv run -q --no-project --with numpy --with opencv-python-headless python albcal34.py | grep -E "level|ratio"
done
