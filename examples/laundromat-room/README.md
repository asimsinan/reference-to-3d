# Worked example: a laundromat room from one render, made walkable

See `../../references/single-view-interior.md`, section "A photo or render of a room to walk around". The picture
was a 1920 x 1080 game render of a coin laundry at night (one camera, consistent perspective). Result: exact from
the picture's camera (mean 0.61/255, median 0), proxies with real depth for every prop, and the parts the picture
never shows (the entrance side, the floor under the eye) built from the picture's own repeating pieces.

Copy these files into a working folder holding the picture as `ref.png` (they read and write next to themselves).
The values in them (camera, door height, slat positions, door circles, tile periods, washer unit edges) are this
picture's: re-measure them for another room. The `*.json` files are this run's outputs, kept for reference.

    # 1. camera (geo.py holds the result; refit it for a new picture)
    uv run --with numpy --with opencv-python-headless python ../../scripts/solve_camera_vp.py ref.png \
        --out cam.json --overlay lines.png --scale 1000,700,1000,337,2.0          # door 2.0 m
    uv run --with pillow python crop.py X0 Y0 X1 Y1 SCALE out.png STEP           # grids for reading pixels
    # 2. room box and first proxies (overlay.png: their outlines over the picture: check every one)
    uv run --with numpy python measure.py                                         # -> room.json
    uv run --with numpy --with opencv-python python proxies.py                    # -> scene.json, propmask.png, overlay.png
    uv run --with numpy --with opencv-python python plate.py                      # -> plate.png (first pass)
    uv run --with numpy --with opencv-python python tones.py                      # -> tones.json (each surface's own tone)
    # 3. detail: door circles, slat profiles, the plant's cut-out, the detailed parts
    uv run --with numpy --with opencv-python python measure2.py                   # -> doors.json, prof_*.npy
    uv run --with numpy --with opencv-python python mask_plant.py                 # -> alpha_plant.png
    uv run --with numpy python detail.py                                          # -> scene2.json
    # 4. what each depth layer covers, then the layered clean plates
    for L in A AB ABC; do Blender -b --factory-startup -P build2.py -- mask:$L; done   # -> cover_*.png
    uv run --with numpy --with opencv-python python plates.py                     # -> plate_B, plate_C, plate.png
    # 5. repeatable textures for what the picture does not show
    uv run --with numpy --with opencv-python python tiles.py                      # -> tiles/*.png, tiles.json
    # 6. build, look, measure, deliver
    Blender -b --factory-startup -P build2.py                                     # -> laundromat_build.blend
    Blender -b laundromat_build.blend -P shots2.py -- cam,walk,cart,eye_left,eye_back,entrance,from_back
    uv run --with numpy --with opencv-python python cmp.py                        # camera view vs ref.png
    Blender -b laundromat_build.blend -P finalize.py -- out/laundromat.blend      # packed, opens in camera view
    Blender out/laundromat.blend --factory-startup -P ../../scripts/shot_ui.py -- ui.png

`rect.py` is the session's own rectifier (tiles.py imports it); `../../scripts/rectify_plane.py` is the same as a
command-line tool reading `cam.json`.

Depth layers (build2.py `LAYER`): A = bench, book, card, bucket, cart (nearest); B = washers, table; C = the rest.
A layer's texture is the picture with the nearer layers' coverage filled; the room's is the picture with all of it
filled. Change the split for another room so that every prop is in a later layer than whatever stands in front of it.
