# Worked example: a porcelain mug from one phone photo

See `../../references/single-photo-revolved.md`. One 1500 x 2000 phone photo (2x lens, portrait blur) of a white mug
on a wooden table, a wall and a door behind it, the camera ~29 cm away and pitched ~10 deg down. No size given
(assumed 8.5 cm across the rim, giving 11.6 cm tall). The photo is shown, cropped, in `docs/showcase/mug.jpg`; the
scripts are here, with this photo's numbers in them (GrabCut seeds, region boxes, root rows), marked "this photo".

What differs from the pressure cooker (`../pressure-cooker-revolved/`), and why this example exists:
- a real background (GrabCut, not a flood fill of white);
- a pitched close camera solved by least squares from the rim's and base's contours, not a level one by hand;
- the profile from tangent rays, the base corner fitted separately;
- a hollow inside, seen through the opening, textured from the photo;
- the handle as a swept tube along the mask's skeleton, not a marching-cubes slab;
- the fold angle asymmetric (the handle's side carries its reflection);
- the porcelain version's colour maps made by dividing out the photo's shading.

Run the scripts by their path (`$EX` = this folder) from a working folder holding the photo as `photo.jpg`; they
read and write the current folder (a shell function, not a `$PY` variable: zsh does not split one into words):

    py() { uv run --with opencv-python-headless --with numpy --with scipy --with scikit-image python "$@"; }
    py $EX/masks.py                 # mask_photo.png; look at masks_vis.jpg
    py $EX/solve_cam.py             # cam.json (prints the F scan: check F against the phone's lens)
    py $EX/profile.py               # profile.json
    py $EX/fit_bottom.py            # bottom.json
    Blender -b -P $EX/build.py -- out --body-mask              # out/body_mask.png (lathed body only)
    py $EX/prep.py                                             # textures, handle.json; look at masks_vis2.jpg
    Blender -b -P $EX/build.py -- final --final                # photo_view + views, kupa.blend, kupa.glb
    py $EX/cmp.py final                                        # numbers + final/compare.jpg
    py $EX/pbr_maps.py                                         # alb_*.png (porcelain colour maps)
    Blender -b final/kupa.blend -P $EX/porcelain.py -- porselen --photo-only   # set EXPO by measuring
    Blender -b final/kupa.blend -P $EX/porcelain.py -- porselen                # Cycles renders, .blend, .glb
    Blender "$PWD/porselen/kupa_porselen.blend" --factory-startup -P $EX/../../scripts/shot_ui.py -- "$PWD/ui.png"
    Blender -b porselen/kupa_porselen.blend -P $EX/showcase_renders.py -- showcase   # transparent-film views
    uv run --with pillow python $EX/showcase.py               # mug_showcase.jpg: the photo | the model (docs/showcase/mug.jpg)

(`masks.py` and `prep.py` take under a minute; the first `scikit-image` install can take longer.)

Result from the photo's camera: silhouette IoU 0.982, mean colour difference 1.4/255 over the model (median 0):
body 0.2, inside 3.1, rim front 1.6, handle 4.4, base 0.5. Camera: D 0.285 m, HC 0.158 m, pitch 10.0 deg,
F 2049 px. Body 21k vertices, handle 9.6k. Porcelain version: body boxes within ~5 levels of the photo at
exposure -1.6 (AgX).

Faults found by looking, in the order met (each fixed; the reference lists the general lesson):
1. GrabCut forced the table into the mask through a too-wide sure-object box; then it left the handle's shaded upper
   face out of the mask (it reads as part of the hole).
2. Profile iteration diverged (spline extrapolated); outliers at the handle's roots.
3. Base 30 px too wide in its lowest rows: those rows are the base's front, fitted separately.
4. The inside showed staircase patches (per-face visibility test); then a white band at the back of the rim (the
   lip's inner half took the outer texture).
5. A D-shaped ghost on the body behind the handle (the photo's reflection of the handle, stretched by the fold).
6. Stripes across the handle (marching-cubes ridges; nearest-pixel margin fill), fixed by the swept tube.
7. The tube's lower root a thin tail (skeleton tips thin out; the both-faces cut thins the arm): held and flared.
8. The first porcelain render all white (HDRI + lights, no measurement).
