#!/bin/zsh
B=/Applications/Blender.app/Contents/MacOS/Blender
for i in $(seq 1 ${1:-3}); do
  LEV=$(python3 -c "import json;print(','.join('%s=%.4f'%(k,v) for k,v in json.load(open('lev34.json')).items()))")
  env LEV=$LEV KS=8 SAMPLES=24 $B -b bake34/baked.blend -P final34.py -- real cams > /dev/null 2>&1
  echo "== round $i $(uv run -q --no-project --with numpy --with opencv-python-headless python int8.py 2>/dev/null | tail -1) $(uv run -q --no-project --with numpy --with opencv-python-headless python seatstat.py)"
  uv run -q --no-project --with numpy --with opencv-python-headless python intcal.py
done
