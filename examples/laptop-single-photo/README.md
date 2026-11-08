# Worked example: MacBook Pro 14 from one photo

See `../../references/single-photo-object.md`. Copy these scripts into a working folder holding the photo as
`ref.jpg` (they read and write next to themselves), then:

    uv run --with pillow python grid.py X0 Y0 X1 Y1 STEP out.jpg SCALE        # find the edges
    uv run --with numpy --with opencv-python-headless python edge_profile.py ref.jpg "h:..." "v:..."   # each corner
    uv run --with numpy --with scipy python solve.py                          # -> cam.json (pose, f, lid angle)
    uv run --with numpy --with scipy --with pillow python overlay.py          # check: model edges over the photo
    uv run --with numpy --with scipy --with opencv-python-headless python rectify.py   # -> tex/deck,screen,front.png
    uv run --with numpy --with opencv-python-headless python keys_fit.py      # grid search -> L R TOP P
    uv run --with numpy --with opencv-python-headless python keys_layout.py 92 1780 36 119.5 13  # -> keys.json
    Blender -b -P build.py -- --mode match --out r_match --shots photo         # emission, photo camera
    uv run --with numpy --with opencv-python-headless python cmp.py r_match/photo.png cmp.jpg
    Blender -b -P build.py -- --mode final --out renders --res 1600 \
        --shots photo,screen,front34,front34r,rear34,side,keys,ports,corner_l,corner_r --blend m.blend --glb m.glb

The image points in solve.py, the dimensions and the key rows are this photo's and this product's: replace them.
rectify.py also writes tex/front.png, which build.py no longer uses (the front wall is body material).

Check the delivered file the way the user will open it:

    Blender m.blend --factory-startup -P ../../scripts/shot_ui.py -- ui.png

Export only the laptop from the saved .blend (no floor, lights or camera) to glTF:

    Blender m.blend -b -P export_glb.py -- m.glb
