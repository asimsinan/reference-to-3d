# Worked example: a wire-mesh pen holder with its contents, from one phone photo

See `../../references/single-photo-container.md` (and `single-photo-revolved.md` before it). One 1500 x 2000 phone
photo of a black mesh pen holder on a desk: two grey-capped pens, a red-checkered pen, a black marker, scissors (one
finger loop showing), a teaspoon, a glue stick with a flag-striped label, a nail file. Rim assumed 9 cm across
(confirmed afterwards). The photo | model comparison is `docs/showcase/pen-holder.jpg`; this photo's numbers (pixel
coordinates of the items' tops and bottoms, region boxes, thresholds) are in the scripts, marked where they are.

Run from a working folder holding the photo as `photo.jpg` (`$EX` = this folder):

    py() { uv run --with opencv-python-headless --with numpy --with scipy --with scikit-image python "$@"; }
    py $EX/masks.py                                   # mask_photo.png, edges.json; look at masks_vis.jpg
    W_RINGBOT=0 FIX_F=2100 py $EX/solve_cam.py        # cam.json (prints the F scan; the ring's lower edge dropped)
    py $EX/vis_cam.py                                 # cam_vis.jpg: the solved circles over the photo
    py $EX/profile.py                                 # wall radius per side (a check: both sides should agree)
    py $EX/unwrap.py 0.0407                           # unwrap.png + lattice pitch from autocorrelation
    WIRE_W=0.48 WIRE_RGB=40,38,35 py $EX/prep.py      # contents_tex, wall_tex (RGBA), rim_tex, lattice_tile, tex_info
    Blender -b -P $EX/build.py -- final --final       # photo_view, holder_mask, six lit views, kalemlik.blend/.glb
    py $EX/cmp.py final; py $EX/iou_vis.py final      # numbers, compare.jpg, side_by_side.jpg, iou_vis.jpg
    Blender -b -P $EX/check_glb.py -- "$PWD/final/kalemlik.glb"   # one texture per material, alpha kept?
    Blender -b final/kalemlik.blend -P $EX/pbr.py -- final        # real materials: kalemlik_pbr.blend/.glb, Cycles views
    Blender "$PWD/final/kalemlik_pbr.blend" --factory-startup -P $EX/../../scripts/shot_ui.py -- "$PWD/final/ui.png"

Camera: D 0.336 m, HC 0.149 m, pitch 9.8 deg, roll 1.1 deg, F 2100 px (fixed). Holder: rim R 45 mm, height 98.5 mm,
wall r 40.7 mm, base ring r 41.3 mm, lattice 3.0 x 3.6 mm, 85 cells around, strands 0.48 mm.
Result from the photo's camera: holder IoU 0.988 below the rim (0.958 with the pens' notches in the photo mask),
pens above the rim 3.7/255, rim 17, base 11, wall 10 (blurred).

Faults found by looking, in the order met (each fixed; the reference has the lesson):
1. Dark background blobs (a chair) joined the mask; the ring's lower edge could not be told from the mesh on that
   side (both dropped from the solve).
2. Left and right rim points 13 px apart: roll added to the camera.
3. The whole model 12 px right of the photo: the roll's sign in Blender (checked against `cam.proj` since).
4. The base ring 15 px too low: the solved circle is the ring's contour, not its tube centre.
5. Pens 15 deg off in depth: items placed by base-plane intersection, not by a given length.
6. Silver pens solid white behind the mesh: percentile filter instead of a closing.
7. The sides of the wall 20 levels too dark: thinner, lighter strands, tuned against the photo's blurred tones.
8. The lattice gone from the glb: two UV maps merged by the exporter; the wall baked to one RGBA texture.
9. The rim's back carried the pens' pixels, the pens' caps streaked from above: inpainted rim texture, plain caps.

Showcase strip (`docs/showcase/pen-holder.jpg`): `Blender -b final/kalemlik_pbr.blend -P $EX/showcase_renders.py -- showcase`
(the photo's camera and three views, Cycles), then `python3 $EX/showcase.py`.
