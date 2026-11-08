# Pitfalls (each cost real time once)

## Judging and process
- **Hand-tuning plateaus.** Colours and shapes tuned by eye converged at ~26/255 mean difference on the van's front;
  using the reference's own pixels took it to ~14. Switch methods when three rounds do not move the number.
- **"Looks close" is not the bar** when the user said "identical". Show side-by-side at the same scale with numbers.
- **Measure regions, not just the whole view.** A whole-view mean hides the one region that is off; average the same
  box in both images (bumper top, windscreen, intake) to find it.
- **A rule that seems not to apply: render the mask itself.** Output the mask as emission (a debug material) instead
  of guessing; a "missing black band" turned out to be grazing reflections, another to be a smoothing modifier.

## Reference sheets
- **Views disagree** (AI concept art, photos): widths and heights differ between views; often perspective. Decide
  which view rules each part, with the user.
- **Panels too close** merge in `split_sheet.py`: lower `--merge`; a very wide panel is the sign.
- **A top view taken a little from one side** puts the roof's middle features (a solar panel, a stripe, a sunroof)
  off the body's centre line: the van's panel sat 4.9 % of the width to one side and looked "skewed" in the game.
  Measure the feature's edges and the body's in the top image and move each column's rows piecewise linearly so the
  feature is centred, the body's edges kept.

## Shape
- **Flat end caps ripple** under subdivision (one n-gon): use a grid/fan cap and enough stations near the ends.
- **Sections sampled by angle** crowd points on the long sides of flat sections and crease where they meet tall ones;
  sample in each section's own proportions (loft.py does).
- **Smoothing modifiers** can turn an upright face into a shelf; keep them weak and local.
- **The plan from a top view** can exceed the body's width (mirrors, flares): cap it.
- **A flat floor at sill height** shows from the front under a bumper as a dark band; check what is visible below.

## Texture projection
- **Blending views doubles features** (a lamp drawn twice at two heights on a corner): choose one view per point
  (power 16), and bias a region to the view that should own it if needed.
- **Raked surfaces** (windscreens) take the top view by plain argmax; restrict the top to near-flat surfaces.
- **One side view mirrored** onto an asymmetric object paints the wrong side.
- **The texture is fixed in world space** while projected: a rotating part's pattern does not turn. Bake to UVs
  before animating.
- **Small parts take the big views' pixels**: a wheel's tread faces forward and back, so it took the front's
  headlamps and the rear's tail lamps. Project a part only from the view that really shows it (a rim: the side), and
  give the rest a real material (the tyre: rubber).

## One photo, solved camera
- **Camera handedness**: seen from the front, the object's left (+Y) is on the image's right. Label marked points by
  the object's sides; a reflected initial rotation makes scipy refuse it ("non-positive determinant").
- **Rows reversed make an inside-out box**: building a part from texture rows (row 0 = the back) with its ends taken
  as (bottom row, top row) gave negative sizes, flipped normals and bevels in the wrong places; every key top took the
  side material. When a whole class of faces renders wrong, print material counts and a few normals.
- **A part placed at the solve's hinge axis** (a hinge barrel) poked out under the screen; put hidden parts where the
  real object hides them and look from the photo's camera.
- **Corners read by eye can be 20 px off** (a rounded lid corner against a busy background); the rectified screen
  then tilts. Measure edges with brightness profiles and intersect fitted lines; anchor the solve on a sharp
  rectangle of known size (a display's active area).
- **A solved outline a few px off puts the background into the texture's border** (a grey band along a laptop lid's
  top). Detect the photo's own edge in the texture, fit a line, paint what lies outside it with the edge's colour;
  never stretch the texture to the edge (the content moves off the photo).
- **Two materials meeting on a rounded corner** (a photo strip on the front wall, flat body colour on the sides)
  show as a step; give a thin wall the photo shows only as a reflective strip the body material all round.
- **Raised details over a photo texture** shift their labels unless each top takes the pixel along the camera's ray
  to the base surface.

## One photo, a turned object
- **Blender's camera shift for a principal point has a sign trap**: the model rendered far down and right of the
  frame. With `sensor_fit` HORIZONTAL: `shift_x = -(cx - W/2) / W`, `shift_y = (cy - H/2) / W`.
- **Mirroring the back (x -> -x) stripes the sides**: the photo's pixels next to the silhouette, stretched many
  times, became horizontal ripples from every three-quarter view. Fold the angle round the axis: the photo's own
  pixels within +-72 deg, the back their stretched mirror reaching the photo's centre at 180 deg.
- **A rotationally symmetric top** sampled from one column caught a dark catch under the rim as a black ring.
- **A mask cut by its box's edge, or joined to a thin dark line**, leaves the part's pixels in the inpainted body
  texture as a smear (a tab's bottom 7 px; the lid's edge line in the tab's mask). Look at every mask over the
  photo; open thin lines away and keep the biggest piece.

## Real materials
- **Polished metal reflects what is there**: in Blender's studio.exr (black curtains) a mirror lid rendered black;
  in a plain white world all steel is flat grey. Product look: bright world, black cards seen only in reflections
  (`visible_camera` off), a satin lid (roughness ~0.16). In the viewport use a built-in HDRI (interior.exr).
- **Black plastic in a bright studio turns grey** at roughness 0.38; 0.5 and specular 0.3.
- **The glTF exporter drops Gamma and Mix nodes**: a handle darkened with a Gamma node came out light in the .glb,
  and a logo mixed by a Mix node would vanish. Bake adjustments into the images; check the .glb by reading its JSON
  chunk (materials, which textures each uses).

## One room, one picture
- **Per-vertex projected UVs on big faces slide**: UV interpolation is affine, the camera's mapping is not. Project
  in the shader (an empty at the camera, Texture Coordinate -> Object), exact on any face.
- **The clamped edge outside the frame** (EXTEND) streaks one row of pixels across every surface the picture does
  not show; fade into the surface's own tone or a repeat cut from the picture.
- **A clean plate from the props' outlines** wipes what shows between their legs; mask with their rendered coverage.
- **Dilating a thin prop's mask** breaks the camera view at its antialiased edges (wire cart 5.6/255); fill only
  fully covered pixels for thin parts.
- **A tile with one stain** repeats the stain at its period; flatten and calm concrete before tiling.

## Rendering for comparison
- **Use the Standard view transform and emission** to get the reference's pixels back; AgX/Filmic pale bright blues to
  white and change every colour.
- **Shadow catchers seen in reflections** cut holes in a transparent film; hide the catcher from glossy rays.
- **Big lights mirrored** in glossy dark glass turn it white; keep key lights out of glossy rays when matching. For
  the final look too: a laptop screen went white at 60 W area lights; 14 W, screen roughness 0.3, specular 0.12.
- **Single-surface glass with IOR > 1** bends the interior behind it (seats appear shifted); use IOR 1 for a pane and
  put the reflection in a coat layer.

## Handing over a .blend
- **The file opens the way the script left it**: every camera made for a render shot (frustums drawn at 1 m, longer
  than a laptop), each light's ground line, a 4 m floor selected, the default view metres away. The user saw only
  wires ("blend dosyası niye böyle"). Delete shot cameras, group model and studio in collections, small camera
  display size, frame each 3D view on the model, extras overlay off if the gizmos still cross it.
- **Viewport shading saved as Rendered reopens as Solid** (grey, every texture gone); Material Preview is kept.
- **Check by opening it**: `scripts/shot_ui.py` (Blender with the file, a timer runs `bpy.ops.screen.screenshot`, quits).

## Tooling
- **zsh does not split unquoted variables** (also in loops: `for a in "x y z"; do cmd $a` passes one argument; use
  `${=a}`): `A="--persp 4,1.0"; cmd $A` passes one argument. Write the arguments out
  or use arrays; a sweep that "changes nothing" may not be running the values at all.
- **Background Blender jobs collide** with other GPU work (a game, another render); a silently missing output file is
  the sign. Run one at a time.
- **OpenCV's LSD returns (N,1,4) or (N,4)** depending on the version: `detect(g)[0].reshape(-1, 4)`.
- **The first `uv run --with scikit-image` takes over 2 minutes** (a 120 s tool timeout moved it to the
  background with nothing written yet); start such a step in the background and wait for it.
- **`uv run --with matplotlib` can take minutes** to download on a fresh cache (a profile plot timed out at 120 s);
  draw quick plots with OpenCV (`cv2.polylines` on a white canvas) instead.
- **Blender 5.x's EEVEE is `BLENDER_EEVEE`** (4.2-4.x: `BLENDER_EEVEE_NEXT`); check the enum, not a guess.
- **`read_factory_settings(use_empty=True)` keeps the workspaces' screens**: a script can set every 3D view to the
  camera and Material Preview before saving, without the interface.
- **A mode flag checked two ways** (`MODE == 'mask'` in one place, `MODE.startswith('mask')` in another) rendered a
  coverage mask in the picture's colours: thresholded, dark props vanished from it. One predicate per flag.
- **A helper named like a standard module** (`inspect.py`, `json.py`) in the folder a Python tool runs from replaces
  that module: `pygltflib` failed with "No module named 'bpy'" because a Blender helper was called `inspect.py`. Name
  helpers distinctly and run checks with `python -I`.
