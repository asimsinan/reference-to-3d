#!/bin/bash
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b -P idr.py >/dev/null 2>&1
$B -b -P bake.py >/dev/null 2>&1
$B -b -P irr.py -- 1 >/dev/null 2>&1
./run2.sh
