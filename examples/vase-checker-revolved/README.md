# Worked example: a checkered porcelain vase from one product photo

See `../../references/single-photo-revolved.md` (the fourth example there). One 600 x 900 e-commerce photo of a
hand-painted checkered vase (cream and grey squares, gold rim, gold band on a pedestal foot) on a mirror tray, red
flowers and a gold tray behind it. No size given: rim assumed 10.4 cm across, giving 30.6 cm tall. The scripts read
`../photo.jpg` and work in the current folder (this photo's numbers in them: GrabCut polygon, rim edge points, band
centre line, unwrap rows and columns).

    py() { uv run -q --with opencv-python-headless --with numpy --with scipy python "$@"; }
    py masks.py                 # mask_raw.png (GrabCut); look at masks_vis.png
    cp mask_raw.png mask_grabcut.png; py fix_rim_mask.py    # the gold rim's ears, hand-read (g_rimL/g_rimR via grid.py)
    py solve_cam.py             # cam.json: rim (fixed R), band arc, foot's bottom; prints an F scan (flat: F by lens)
    py profile.py               # profile.json, tangent rays, binned-median fit (a spline diverged)
    py fit_foot.py              # foot radii + camera + rim + band together; rewrites cam.json
    py profile.py; py overlay.py                            # IoU, ov.png
    py prep.py                                              # tex_body.png, tex_inside.png
    Blender -b -P build.py -- out                           # photo version, views
    py cmp.py out                                           # IoU, colour difference, out/compare.jpg
    py unwrap.py; py albedo.py                              # unwrap.png -> alb_cyl.png (360 deg checker)
    LOOK="AgX - Punchy" EXPO=0.6 Blender -b -P real.py -- real --photo-only; py cmp_real.py real/r_photo_cam.png c.jpg
    LOOK="AgX - Punchy" EXPO=0.6 Blender -b -P real.py -- real              # renders, vazo.blend, vazo.glb
    Blender -b out/vazo_foto_raw.blend -P pack_photo.py -- $PWD/out; Blender -b out/vazo_foto.blend -P fix_photo.py -- $PWD/out

Result: camera D 0.633 m, HC 0.427 m, pitch 20.7 deg, F 1332 px (2x phone lens); IoU 0.988, mean colour difference
3.7/255 (neck and belly 1.0, foot 3.3, rim and inside ~27: the opening's far wall and the lip). Real materials:
body boxes within +-10 levels, neck -17 (the photo's window glint), gold band +33.

What the user caught, in order:
1. "The mouth is narrower" — GrabCut dropped the rim's dark gold edges against the red background (15 px a side).
   The numbers had been good because the mask was the reference. Read the rim on a zoomed grid before solving.
2. "The colour is livelier" — near-white glaze through AgX Medium High Contrast: warmer albedo, AgX Punchy,
   exposure re-measured.
Found by looking: spline profile diverged; foot too wide at its sides (joint fit); lip's inner half took the outer
fold (own tag); ghost glints left in cleaned white cells (plain colour instead); gold pale on a white floor (mirror tray).
