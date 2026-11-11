#!/bin/bash
B=/Applications/Blender.app/Contents/MacOS/Blender
python3 texbuild.py 2>/dev/null
$B -b -P render.py -- photo >/dev/null 2>&1
$B -b -P irr.py -- 2 2>&1 | grep -iE "error|Trace"
python3 albedo.py >/dev/null
$B -b -P final.py -- final 2>&1 | grep -iE "error|Trace"
$B -b -P lightpass.py -- r2 r3 r4 2>&1 | grep -iE "error|Trace"
python3 lightfit.py
python3 stats.py photo; python3 stats.py final; python3 stats.py fit
