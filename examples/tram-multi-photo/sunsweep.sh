#!/bin/zsh
# sunsweep.sh K "az1 az2 .." "el1 el2 .."  (azimuth deg from +X towards +Y, elevation deg)
k=$1
for az in ${=2}; do for el in ${=3}; do
  d=$(python3 -c "import math;a=math.radians($az);e=math.radians($el);print('%.4f,%.4f,%.4f'%(math.cos(e)*math.cos(a),math.cos(e)*math.sin(a),math.sin(e)))")
  env SUNDIR=$d KS=$k SAMPLES=12 /Applications/Blender.app/Contents/MacOS/Blender -b bake34/baked.blend -P final34.py -- real cams > /dev/null 2>&1
  echo "az $az el $el  $(env KS=$k uv run -q --no-project --with numpy --with opencv-python-headless python cal34.py real 2>/dev/null | grep -E '^photo' )"
done; done
