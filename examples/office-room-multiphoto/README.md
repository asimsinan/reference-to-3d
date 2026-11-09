# Worked example: an office and its corridor from 15 phone photos, walkable, with an openable door

See `../../references/multi-photo-room.md`. The values in these files (room parameters, pixel readings, shelf
groups, prop positions) are this room's; re-measure them for another room. Photos are not included (private).
Photo names the scripts expect: `left right long win win2 door corridor doorout` (room set) and `ek1..ek7`
(bookcase, chair, long corridor, glass door, printer x3).

    # 1. room + 6 cameras (hand-read points in obs.py), overlays to check
    uv run --with numpy --with scipy --with opencv-python-headless python fit.py        # -> room.json, cams.json, overlay_*.jpg
    cp room.json room_final.json; cp cams.json cams_final.json
    uv run --with numpy python measure_props.py                                          # ray-plane prop positions
    # 2. extra cameras against the fixed room
    uv run --with numpy --with scipy --with opencv-python-headless python solve_corridor3.py   # corridor photo + wall thickness
    uv run --with numpy --with opencv-python-headless python solve_ek4.py                      # glass-door photo (PnP, focal scan)
    uv run --with numpy --with scipy --with opencv-python-headless python solve_ek3c.py        # long corridor: vanishing point + section
    # 3. textures
    uv run --with numpy --with opencv-python-headless python rect_all.py                 # walls, door, bookcase, floor
    uv run --with numpy --with opencv-python-headless python prep_tex.py                 # floor tile, decals, maple
    uv run --with numpy --with opencv-python-headless python rect_corridor.py            # door leaf, plates, corridor
    uv run --with numpy --with opencv-python-headless python prep_bookcase2.py           # frontal bookcase photo -> metric (SIFT)
    uv run --with numpy --with opencv-python-headless --with pillow python prep2.py      # blinds, bookcase front, clock, keyboard
    uv run --with numpy --with opencv-python-headless python prep3.py                    # books (leaning/upright), outdoor panes
    uv run --with numpy --with opencv-python-headless python prep_items.py               # box silhouettes
    uv run --with numpy --with opencv-python-headless python prep_printer.py             # printer faces by homography
    # 4. build (build.py execs build_detail.py), render photo cameras + close-ups, calibrate, deliver
    Blender -b --factory-startup -P build.py -- "$PWD/oda_build.blend"
    Blender -b oda_build.blend -P shots.py -- "$PWD/renders" door long win left right --scale 0.33 --samples 48
    uv run --with numpy --with pillow python calib.py                                    # material ratios photo/render
    python3 sheet.py cmp.jpg door long win                                               # photo | render sheets
    Blender -b oda_build.blend -P finalize.py -- "$PWD/oda.blend" "$PWD/oda.glb"
    python3 embed.py                                                                     # viewer_template.html + GLB -> one HTML

`shots.py` takes photo names (their solved cameras) or named walk/close-up views, `--hide PREFIX` (e.g. the end wall
when rendering a photo taken from behind it) and `--exposure`. The viewer exposes `window.__room` (update, render,
toggleDoor, go) for testing while the browser pane is hidden.
