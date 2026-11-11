#!/bin/zsh
for su in ${=1}; do for sk in ${=2}; do
  env SUN=$su SKY=$sk SAMPLES=16 /Applications/Blender.app/Contents/MacOS/Blender -b bake34/baked.blend -P final34.py -- real cams > /dev/null 2>&1
  echo "SUN $su SKY $sk  $(uv run -q --no-project --with numpy --with opencv-python-headless python cal34.py real 2>/dev/null | grep -E '^photo|^ALL' | tr '\n' ' ')"
done; done
