# Worked example: a dining set and its room from one product photo

See `../../references/single-photo-scene.md` and "The bar: identical" in `../../SKILL.md`. Copy these scripts into a
working folder holding the photo as `ref.jpg` (they read and write next to themselves). The image coordinates in the
scripts (edge windows, feet, object readings, boxes) are this photo's: re-read them on your photo with `grid.py` /
`gradgrid.py` before running anything.

    # geometry
    uv run --with numpy --with opencv-python-headless python edges.py specs2.json e2.json     # top's edge lines
    uv run --with numpy --with scipy python solve.py --level                                   # -> cam_level.json (cp to cam.json)
    uv run --with numpy --with scipy --with pillow python overlay.py                           # check
    uv run --with numpy --with scipy python measure2.py; ... corner.py; feet.py               # aprons, corner radius, feet
    uv run --with numpy --with opencv-python-headless python grab.py                           # cushion masks (GrabCut)
    uv run --with numpy --with scipy --with opencv-python-headless python cushfit.py; cushfit2.py; cushfit3.py
    uv run --with numpy --with scipy python trayfit.py; legaxes.py; splay.py; misc.py
    uv run --with numpy --with scipy python prep.py                                            # -> scene.json
    Blender -b -P build.py -- --mode id --out r_id --shots photo; python idov.py r_id/photo.png   # every outline
    Blender -b -P build.py -- --mode match --out r_match --shots photo; python cmp.py r_match/photo.png cmp.jpg
    # materials from the photo, room
    uv run --with numpy --with opencv-python-headless python extract2.py leg fab               # legs, linen (quilting)
    uv run --with numpy --with opencv-python-headless python oak2.py                           # oak: photo palette + measured flow
    uv run --with numpy --with opencv-python-headless python env.py; floor.py                  # walls, curtains, floor
    uv run --with numpy --with opencv-python-headless --with pillow python textures2.py        # cup print, leaf
    # light fitted to colour AND contrast, then each material's albedo
    uv run --with numpy --with scipy --with opencv-python-headless python tune2.py 40 Medium_High_Contrast
    python albedo_cal.py r_cal/photo.png   (2-3 rounds, rendering between)
    python cstats.py r.png; python calib.py r.png                                              # contrast, regions
    Blender -b -P build.py -- --mode final ... --shots photo --res 4000 --border x0,y0,x1,y1   # 4x crops vs the photo
    zsh final.sh                                                                               # renders, .blend, .glb

`build.py` modes: `match` (the photo projected from the camera, emission; fit check), `id` (flat colour per object for
outline overlays), `final` (materials from `tex/*_cal.png`, the room, lights from flags in `light_args.txt`).
