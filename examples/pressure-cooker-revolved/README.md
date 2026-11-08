# Worked example: a pressure cooker from one product photo

See `../../references/single-photo-revolved.md`. One 554 x 554 product photo (a stainless pressure cooker on white,
seen from the side, a little from above); no size given (assumed ~27 cm across). The photo is not included (it is
the maker's); the scripts are, with this photo's numbers in them (boxes, rows, profile points), marked "this photo".

Run the scripts by their path (`$EX` = this folder) from a working folder holding the photo as `photo.jpg`; they
read and write the current folder:

    uv run --with opencv-python-headless --with numpy python $EX/masks.py      # silhouette + handle masks; look at masks_vis.png
    uv run --with opencv-python-headless --with numpy python $EX/profile.py    # wall radius r(z) -> wall.json
    uv run --with opencv-python-headless --with numpy --with scipy --with scikit-image python $EX/prep.py
                                                                              # textures + handle slabs (handles.json)
    Blender -b -P $EX/build.py -- out --final                                 # lathe, UVs, renders, .blend + .glb
    uv run --with opencv-python-headless --with numpy python $EX/cmp.py out     # numbers + out/compare.png
    uv run --with opencv-python-headless --with numpy python $EX/pbr_maps.py   # logo mask, steel maps, darker handle
    Blender -b out/pressure_cooker.blend -P $EX/steel.py -- steel              # real materials, Cycles, .blend + .glb

`cam.py` holds the camera (found by hand from two ellipses; its header shows the arithmetic). The first `prep.py`
run installs scikit-image and can take over 2 minutes: run it in the background.

Result from the photo's camera: silhouette IoU 0.98 (above the floor's shadow), mean colour difference 8.3/255 over
the model (median 1.0), body 1.5, main handle 9.3, helper handle 15.8, lid region 31.4 (the lid tab's and main
handle's lower edges hide behind the dome in a 2-4 px band: the hand-solved camera's elevation is a little off
there). Other views: a clean revolved pot, the photo's vertical reflection bands all round, rounded handles.

Check the delivered file the way the user will open it:

    Blender steel/pressure_cooker_steel.blend --factory-startup -P ../../scripts/shot_ui.py -- ui.png
