# Worked example: a corded desk phone from two phone photos (front and side), size unknown

See `../../references/two-photo-object.md` (and `single-photo-object.md` before it). Two phone photos of a cream
Tesan desk phone on a desk: `ref.jpg` (1500 x 2000, from the front-left, above) and `side.jpg` (1200 x 1600, the
handset side, low). No EXIF, no published size. The photo | model comparison is `docs/showcase/desk-phone.jpg`;
this photo pair's numbers (key centres, edge scan rows, the handset's outline points, the cord hole's pixel) are in
the scripts, marked where they are.

Run from a working folder holding `ref.jpg` and `side.jpg` (`$EX` = this folder):

    py() { uv run --with numpy --with scipy --with opencv-python-headless --with pillow python "$@"; }
    py $EX/grid.py X0 Y0 X1 Y1 STEP out.jpg SCALE         # IMG=side.jpg for the side photo: read points on a grid
    py $EX/measure.py; py $EX/keys_meas.py                # front: body edge lines, each key's edges -> lines.json, keys_meas.json
    py $EX/smeasure.py                                    # side: band, floor, rim, corners -> slines.json (cleaned)
    py $EX/jsolve.py 140 hs=0                             # both cameras + one body -> cam.json (needs a start cam.json: the one here)
    py $EX/overlay2.py                                    # overlay.jpg, overlay_side.jpg: the body's edges over both photos
    py $EX/hsfit.py                                       # handset vs each photo and both -> handset.json (with the top arc)
    py $EX/measure_side_parts.py                          # grille / hooks / cord hole through cam2; side_match.jpg (gain-matched)
    py $EX/delight.py                                     # albedo maps for real materials + the key-label mask
    Blender -b -P $EX/build.py -- --mode match --out r_match --shots photo,sidephoto
    py $EX/cmp.py r_match/photo.png cmp.jpg; py $EX/cmp_side.py r_match/sidephoto.png cmp_side.jpg
    Blender -b -P $EX/build.py -- --mode pbr --out renders_pbr --shots front34,left,top,handset,front --blend p.blend --glb p.glb
    Blender -b -P $EX/build.py -- --mode pbr --engine cycles --out r_show --res 1000 --shots photo,show_q,show_rear,show_top
    py $EX/showcase.py                                    # phone_showcase.jpg
    Blender "$PWD/p.blend" --factory-startup -P $EX/../../scripts/shot_ui.py -- "$PWD/ui.png"

`build.py` modes: `match` (pure emission, both photos projected, for the numbers), `final` (photo textures lit) and
`pbr` (real materials, the main delivery: cream ABS albedo with the photo's printing kept, black keys with a label
mask, plain plastic where the photo carried shadows).

Result (width 140 mm assumed): body D 161 mm, front 23 mm, back 31 mm (slope 2.9 deg), band top 17.5 mm at the back
to 6 mm at the front, a 2 mm step under it; f 1450 px (front, assumed), 1160 px (side). Key centres 3.8 px RMS.
From the front camera (match mode) 6.7/255 mean, 0.3 median; keypad 4.5, top 0.8. From the side camera 37/255: the
side photo is much brighter (window light) and the handset's flank is plain colour there. Real-material version:
the front face within 1 %, the top 15-20 % brighter than the photo (studio key light from above), exposure -1.35.

What the user corrected, in the order met (each fixed; the reference has the lessons):
1. One photo could not separate the top's slope, the camera's pitch and the front height: a 16/47 mm wedge came out
   where the phone is 23/31 mm. The side photo, solved jointly, fixed it.
2. The side camera floated (a flat wall pins little); the FLASH and REDIAL buttons, seen in both photos, pinned it.
3. The handset was given a waist in plan; the reference is straight from above. Its top was straight; the side photo
   shows an arc (flat at the back, dipping to the front) and a crown across.
4. The parting line cut into the mesh as a groove broke at every change of section and read thick: a separate thin
   ribbon following the top's arc is straight and even.
5. The handset's ends lifted off the pocket floor (end rounding applied to the bottom too); the arch's walls were
   too gentle. The ends now round only at the top; the arch walls blend over 3 mm.
6. The base's lower wall stepped in under the band in the reference: the body is now a 2 mm step there, not flush.
7. A cord socket on the handset's end was invented (not in either photo); the cord leaves the base through a hole low
   on the left wall, located on the side photo through cam2.
8. Dark smudges beside the keys, a "dent" on the rim by the pocket, patchy handset: the photos' shadows carried into
   the de-lit albedo. Keys' shadows masked out of it, the handset and the body's handset side plain plastic.
