# Worked example: a red rotary desk phone from three phone photos (front, side, rear)

See `../../references/three-photo-object.md`. Three 1500 x 2000 phone photos of a red rotary telephone on a desk,
the phone turned between them; no EXIF. Scale: the finger wheel's 76.2 mm. The photo | model comparison is
`docs/showcase/rotary-phone.jpg`. The hand-read numbers (rim points, digit centres, feet, prong corners, mask
polygons, fit zones) are in the scripts.

Run from a working folder holding `front.jpg`, `side.jpg`, `rear.jpg` and these files:

    ./py.sh grid.py X0 Y0 X1 Y1 STEP out.jpg SCALE      # IMG=side.jpg ...: read points on a grid
    ./py.sh solve.py                                    # three cameras + dial/feet/prongs -> cam.json
    ./py.sh mask.py && ./py.sh maskfix.py               # colour masks, then the lit faces added by hand
    ./py.sh overlay.py ov [view]                        # every part's outline over the photos
    ./py.sh fit.py xf,xb,wf,wr,... 400 A 5 [views]      # body params on the body-only zones
    ./py.sh fit.py hz,hx,cyc,... 400 B 3 [views]        # handset params on the handset zones
    ./py.sh fitcam.py side                              # a camera from silhouettes + dial points
    ./op.sh                                             # handset outline over crops of all three photos
    ./py.sh prep_tex.py && ./py.sh mktex.py             # ring mask, card, logo normal map -> gen/
    Blender -b -P build.py -- --out r --shots front,side,rear,q1,q2,dial,cradle,top --blend p.blend --glb p.glb
    ./py.sh cmp.py r cmp.jpg                            # photo | render over the photo, colour statistics
    ./py.sh showcase.py r                               # rotary_showcase.jpg

`geom.py` is the parametric phone (numpy only, used by the fits and by Blender): `body()` a height field over the
plan with rolled edges, `handset()` a bar plus two lathed cups, `params.json` the fitted values. `mat.json` holds
the plastic's colour, the light and each photo's exposure.

Result: body 228 x 140 mm, ridge 96 mm, prong tops 122 mm, handset 229 mm. Silhouette IoU body 0.94 / 0.89 / 0.97
(front / side / rear), handset zone 0.91 / 0.90 / 0.87. Not identical: see the reference's last section.

What went wrong, in the order met:
1. The cradle's four prongs taken for two: the rear camera solved 33 cm up.
2. One union silhouette: the body swallowed the handset. Zones per part fixed it.
3. `fillPoly` on all faces at once: a hatched silhouette and IoU 0.6 on a good fit.
4. The top profile fitted to silhouettes that do not show it; measured by rays it is a roof with a ridge.
5. A ceiling light washed the tilted dial; textures written from Blender were black; the clear wheel read as chrome.
6. The handset fitted three times to masks that had cut its lit top; a bar-over-cups shape that scored well and
   looked wrong. The masks were patched by hand and the shape chosen on the shaded render.
