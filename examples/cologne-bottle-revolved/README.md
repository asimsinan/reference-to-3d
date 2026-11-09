# Worked example: a clear cologne spray bottle from one phone photo

See `../../references/single-photo-revolved.md`. One 1500 x 2000 phone photo of a 100 ml clear PET spray bottle
(cream wrap-around label, black ribbed collar, smoked overcap) on a wooden table, a grey wall and a white door behind
it. No EXIF, no size given (assumed 40 mm across the body; the solve then gave 89 mm body, 140 mm overall). The
photo is shown with both results in `docs/showcase/cologne-bottle.jpg`. Scripts carry this photo's numbers (rows,
columns, boxes), marked where they are.

What differs from the mug (`../mug-revolved/`), and why this example exists:
- **the photo is a crop and the camera is level**: the body's two silhouette edges stay parallel (332 -> 337 px over
  560 rows) while every horizontal circle sags more the lower it sits (collar bottom b/a 0.18, the foot ring 0.40).
  Only a level camera with its principal point far above the image centre (CY = 173 of 2000) fits both: depth along
  the optical axis sets a cylinder's apparent width, so a level camera shows a straight cylinder at one width
  whatever its height, while the sags come from the camera's height alone. An afternoon went into believing the
  pitched-camera model until this was written down. `solve3.py` frees CY (pitch and CY are told apart only by the
  edges' convergence), fixes CX, and solves F from the sags' ratios (3480 px: a 3x phone lens, or a crop of one);
- **a transparent body**: GrabCut only works on the cap, the collar and the label; the clear PET over the table has
  no edge at all for most rows, and the grey "foot" seen through the base is the thick bottom, not the outer wall
  (a first solve shrank the base radius to it). Edges are taken only where the background differs (the left edge
  along the dark table edge, the right edge where the floor is behind it), each straight part fitted as a line, and
  the foot ring is a feature circle with its own radius (`measure2.py`, `edges.py`);
- **label edges are not level circles**: the wrap-around label sits slightly skewed, its edge arcs were asymmetric
  (b = 42 px from the left side, 29 from the right) and the yellow band's soft edge gave a flat-bottomed arc. The
  camera uses moulded features only (collar bottom, shoulder outline, foot ring, straight edges);
- **the sprayer head is tilted 1.6 deg against the body**: solved as its own rotation about the viewing axis at the
  neck (PHI), so the body's roll (1.5 deg) is not contaminated; then set to zero in the product model (the user reads
  a crooked head as a flaw);
- **the real-material version is a clear double-walled bottle with a printed label**: the label rectified from the
  photo into a cylindrical texture (u = angle, v = height) with the cylinder's shading divided out per column (the
  median of a print-free cream band of the label: shading on a cylinder depends on the angle only, so the yellow band
  survives where a photo / blurred-photo ratio would flatten it); transmission and roughness as image maps, so the
  .glb keeps the label as paper on clear PET; liquid, dip tube and actuator inside;
- **the photo as the comparison backdrop for glass**: a clean plate (the bottle filled out of the photo) projected
  through the camera with Window texture coordinates onto a far backdrop (3 m, the room's real depth) and a ground
  plane, so the glass refracts the right content. With the raw photo the glass refracted its own collar into the
  clear band (-61 levels); with a near backdrop (0.6 m) the refracted rays landed on the floor.

Run from a working folder holding the photo as `photo.jpg` (`$EX` = this folder; `--no-project` keeps `uv` from
picking up a pyproject in a parent folder):

    py() { uv run --no-project --with opencv-python-headless --with numpy --with scipy --with scikit-image python "$@"; }
    py $EX/grid.py photo.jpg 560 420 1020 1580 20 1.0 g_all.jpg     # read rows/columns off grids first
    py $EX/masks.py                 # GrabCut: good on cap, collar, label; look at masks_vis.jpg
    py $EX/edges.py                 # label/collar arcs, body edge lines -> edges.json
    py $EX/measure2.py              # base outline, cap/collar edges -> obs.json
    py $EX/solve3.py                # camera + bottle (multi-start, F and CY free) -> cam.json
    py $EX/overlay.py               # model silhouette over the photo; model_mask.png
    py $EX/prep.py                  # tex_front.png / tex_back.png (print inpainted), crop + 2x
    STRAIGHT=1 Blender -b -P $EX/build.py -- final --final       # photo-projected version, kolonya.blend/.glb
    py $EX/cmp.py final             # IoU 0.966 (rows the mask is reliable on), colour diff 2.3/255
    py $EX/prep_pbr.py              # label_albedo_m/trans/rough.png (cylindrical, de-shaded), z of the label edges
    EXPO=0.4 SAMPLES=64 Blender -b -P $EX/real.py -- real --photo-only; py $EX/cmp_real.py real   # set EXPO by the numbers
    EXPO=0.4 SAMPLES=128 Blender -b -P $EX/real.py -- real_final --final                         # Cycles views, .blend, .glb
    Blender -b real_final/kolonya_gercek.blend -P $EX/fix_blend2.py       # Blended surfaces for the EEVEE viewport
    Blender "$PWD/real_final/kolonya_gercek.blend" --factory-startup -P $EX/../../scripts/shot_ui.py -- "$PWD/ui.png"

Result, photo-projected version from the photo's camera: IoU 0.966, mean colour difference 2.3/255 (cap 1.3,
collar 2.4, label 1.5). Real-material version, same boxes against the photo after exposure by measuring (EXPO 0.4,
key light from the photo's left, Standard view transform so the emission backdrop reproduces the photo): label
+1/+4/-4, yellow band +3, cap -1, collar -5 levels; the clear band above the label -61 (the glass refracts the room,
not the photo's own pixels).

Faults found by looking, in the order met (each fixed unless noted):
1. The camera fitted with pitch and the image centre wandered between solutions (D 0.15-0.6 m) and inverted the
   collar's top and bottom: tangent rays on a near-cylinder constrain radii, not heights; add each part's top and
   bottom circle side points, and start every F from the same x0 (chaining starts biased the scan).
2. A fillet placed on the wrong side of the top still "fitted" (rms 1.0) with the fillet radius at its bound and the
   body 12 mm too short: a parameter at a bound is a bug until proved otherwise.
3. The real-material first render: label 20-60 levels too bright and lit from the wrong side; AgX made the emission
   backdrop 30 % dark (Standard fixed it); the glass refracted the photo's own bottle (clean plate fixed it).
4. The smoked cap stays speckled in Blender's Material Preview (EEVEE transmission) whatever the render method, the
   viewport sample count or raytracing flag; the Cycles render is clean. Not fixed; told the user.
5. A lathe profile with two consecutive points on the axis (the cap's outer top and inner top) crashed the lathe;
   skip such pairs.
