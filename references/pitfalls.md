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
- **A close phone photo is pitched**: a level camera could not fit a mug whose rim was seen at 10 deg and base at 30.
  Solve pitch, distance, height and focal by least squares on the rim's and base's contours; F is weakly determined
  there, so pick it by the phone's lens. Add the rim's front point by hand: the mask cannot see white on white.
- **The lowest rows of a silhouette are the base's front, not tangent rays**: a profile read from them came out
  30 px too wide at the bottom. Fit the base corner separately.
- **A spline evaluated outside its data** blew a tangent-ray profile iteration up (r of 10^28): search each ray only
  near its closest approach to the axis and clip the fit to its range.
- **The fold stretches a glossy body's reflections of its own handle** into a ghost (a D on the mug behind its
  handle): fold less on the handle's side (50 deg).
- **Marching-cubes slabs show the mask's pixel steps as ridges** across a bar-like handle; nearest-pixel margin fill
  adds streaks perpendicular to the edge. A swept tube along the mask's skeleton and a normalized-convolution fill
  fixed both. A mask seen from above holds the part's upper face: build from where both faces project inside it,
  then thicken (x1.12) and flare the roots; a skeleton's tips taper to nothing.
- **An inside textured by a per-face visibility test** shows staircase patches; project every inside vertex (near
  half mirrored to the far) into a texture that is the photo inside the opening and a plain colour outside it. The
  lip's inner half must take the inside's texture, or the back of the rim shows a white band.

## Real materials
- **A real material on a photo-lit model is set by measuring**: interior.exr at 1.0 plus area lights rendered a white
  mug all white on a white table. Compare the same boxes (body left, middle, right; the table) with the photo and set
  exposure and the key/fill ratio from the numbers.
- **Detail kept as photo / blurred photo** brings the photo's edge shading back as dark rings (silhouette, lip,
  opening): trust the ratio only away from them.
- **Polished metal reflects what is there**: in Blender's studio.exr (black curtains) a mirror lid rendered black;
  in a plain white world all steel is flat grey. Product look: bright world, black cards seen only in reflections
  (`visible_camera` off), a satin lid (roughness ~0.16). In the viewport use a built-in HDRI (interior.exr).
- **Steel seen from above mirrors the floor**, not the cards around it: flat white on a white floor, black on a
  floor dark in reflections. Give the floor dark sectors round the object in glossy rays only.
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

## Two photos, size unknown (the desk phone)
- **One photo cannot separate a top's slope, the camera's pitch and the body's height**: every slope 0-18 deg fitted
  the front photo within 0.6 px; the 10 deg prior made a 16/47 mm wedge of a 23/31 mm phone. Ask for a side photo.
- **A second camera solved only from a flat wall floats**: its lines slide along themselves (the side camera came out
  10 mm above the table). Add features both photos see (two buttons) as shared 3D unknowns.
- **Bounds 1e-6 apart make scipy's least_squares crawl** (minutes instead of 2 s): drop unused parameters from the
  vector instead of pinning them.
- **An invented feature is a fault even if the real product "usually" has it**: a cord socket on the handset's end;
  the photo showed the cord leaving the base's wall. Place features from the photo that shows them, or leave them out.
- **A groove cut into a lofted mesh breaks at every change of section** and renders thick; a parting line is a thin
  separate ribbon following the surface.
- **Scaling a lofted part's whole section to round its ends lifts its bottom** off what it rests on; round the top only.
- **De-lit albedo keeps shadows**: keys' own shadows (black smudges beside them), a part's shadow on a rim (read as a
  dent). Use the plain material wherever the photo has no printing.
- **Mid-turn image attachments are not written to disk**: a photo sent while a turn was running could be seen but not
  read by the scripts. Ask for it again in a new message, then copy it into the work folder at once.

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

## Tools
- **`shot_ui.py` given a relative output path** wrote no file (the screenshot resolves it elsewhere); pass absolute
  paths for both the .blend and the PNG.
- **Long jobs: keep the inputs and scripts outside the scratchpad** (a work folder next to the deliverables); a
  session restart once wiped an attached photo and a whole pipeline.

## A clear cologne spray bottle with a label (one cropped phone photo, 2026-11)
- **Parallel silhouette edges plus sagging circles mean a level camera and a cropped frame, not a pitched one.**
  Depth along the optical axis sets a cylinder's apparent width; a level camera shows a straight body at one width
  whatever its height, and the circles' sags come from the camera's height alone. Three solvers and an afternoon
  went into pitched models before this was written down. Check the straight edges' convergence first; free the
  principal row CY when the edges say level and the horizon is not where the image centre is.
- **Tangent rays on a near-cylinder constrain its radii, not its heights**: a collar's top and bottom came out
  inverted. Give each part its top and bottom circle side points. Start every focal-length trial from the same x0;
  chaining starts biased the scan. A parameter sitting at its bound (a fillet at 12 mm, the body 12 mm short) is a
  bug until proved otherwise: here the fillet's discs had been placed above the top instead of below it.
- **A transparent body has no mask**: GrabCut finds cap, collar and label; the clear wall over a same-toned table
  has no edge for hundreds of rows, and what shows through the base (the thick grey bottom) is not the outer wall.
  A first solve shrank the base radius to it. Measure edges only where the background differs, fit lines, extend
  them; inner features are circles of their own radius; judge IoU on the rows the mask is good on.
- **A sticker's edges are not level circles**: the wrap-around label was skewed; its arcs read 42 px of sag from
  the left and 29 from the right, and a soft printed band gave a flat-bottomed arc. Solve the camera from moulded
  features (collar rim, shoulder outline, foot ring, straight edges).
- **Parts askew on each other** (a sprayer head 1.6 deg off the body) need their own tilt in the solve, or they
  corrupt the camera's roll and shift the body's predicted edges 24 px at the base; straighten them in the model.
- **A glass object's comparison render refracts whatever is behind it**: the raw photo as backdrop put the photo's
  own collar into the clear band (-61 levels); use a clean plate (the object filled out) projected with Window
  coordinates onto a backdrop at the room's real depth (3 m) and a ground plane; a backdrop at 0.6 m sent the
  refracted rays to the floor. AgX dims an emission backdrop 30 %: Standard.
- **A label's shading divides out per column**: on a cylinder the photo's shading depends on the angle only, so the
  median of a print-free band per column (smoothed, normalised to the 97th percentile) flattens it without flattening
  a coloured band, where a photo / blurred-photo ratio would. Transmission and roughness as image maps on the same
  cylindrical UVs keep the label through glTF.
- **EEVEE's Material Preview speckles dark transmissive materials** (a smoked cap) whatever the surface render
  method, viewport samples or raytracing flag; the Cycles render is clean. Say so instead of fiddling.
- **A lathe profile with two consecutive points on the axis** (a shell's outer and inner top) crashes a ring-pair
  lathe; skip pairs of single vertices.
- **`uv run` inside another project's folder resolves that project's pyproject** (and failed on its pins): pass
  `--no-project`, or run from the work folder. **`echo =====` fails in zsh** (`=cmd` expansion); quote separators.

## A wire-mesh pen holder with its contents (one phone photo, 2026-11)
- **The Blender camera's roll had the wrong sign**: the whole model sat ~12 px to the right of the photo while
  cam.py's own projection was right. With roll as `r' = cos ρ r + sin ρ up` in cam.py, the Blender camera is
  `Euler(pi/2 - TH, 0, pi/2) @ Rotation(+ρ, 'Z')`. Print `world_to_camera_view` of a few known points against
  `cam.proj` before trusting any render.
- **A see-through mesh wall**: a lathed cylinder with an alpha-clipped diamond lattice (cell pitch measured on the
  photo unwrapped onto the cylinder, 3.0 x 3.6 mm here), the wire colour from the photo's low percentile, the
  contents behind it textured from a high-percentile (not max: a max filter spread every specular line of the
  silver pens into white) filter of the photo that removes the wires. Tune the strand width against the photo's
  blurred wall tones, region by region.
- **glTF needs colour and alpha in one image with one UV set**: two UV maps (photo colour + tiled lattice alpha)
  exported as a merged 1500 x 2000 image and the lattice was lost. Bake the wall to one RGBA texture (u = angle,
  v = height) before exporting.
- **The rim's back carried the pens' pixels** (hidden from the photo's camera, visible from above): inpaint
  everything brighter than the ring out of the ring's texture. Likewise the items' tops and bottoms: a plain colour,
  projected pixels streak there.
- **Items standing in a container**: a bottom pixel on the base plane fixes an item's (x, y) outright (ray ∩ plane);
  the top pixel at the same depth gives its height and lean. Solving for a given length instead picked wrong roots.

## A real office + corridor from 15 phone photos, walkable (2026-11)
- **Room length drifted 5 → 7 m** between fits with small residuals: square-on photos trade focal length against
  distance. Pin with lens-class focal priors (1x vs 0.5x) and shared furniture as unknowns in the same fit.
- **A stand-in object is a defect, not a step**: flower spheres, a box phone, a generic chair, a heightfield
  figurine — each was rejected angrily ("basit temsil istemiyorum", "saçma sapan modeller"). Model from a photo of the
  object, or ask for one, or say it is a guess.
- **The bookcase photo also landed on the back panel's inner face** (a helper mapped every -x-facing face): every
  object appeared twice, once as a picture behind. Exclude back panels from photo projection.
- **One lean for a whole shelf** pushed upright books through the side panel. Read leaning and upright groups per
  shelf and clamp each top to its neighbour and the panel.
- **Planar photo projection on a round object's sides** brings background pixels (a black patch on a ball); give
  round objects their own material texture. `bmesh.ops.create_uvsphere(calc_uvs=True)` needs the UV layer to exist
  first (`bm.loops.layers.uv.verify()` before the op), or the texture shows as flat colour.
- **Dial/label textures gain-matched from a wrong sample box turned green**: cut them straight from the sharpest
  photo and check the crop by eye; check orientation (a dial came out mirrored, then upside down: flip v, not u).
- **A layout guessed from one photo was wrong**: the double glass door was the corridor's end wall, not the far wall.
  Ask the user for photos that settle the layout; they had them.
- **Overlapping coplanar boxes render black in Cycles** (a frame casing over its lining); objects that intersect
  (chair into desk by 9 cm, pen through a panel) are found by bounding-box checks, not by the photo views.
- **three.js renames objects** (spaces → underscores): match with `Door.pivot`, not `Door pivot`. A hidden browser
  pane stops requestAnimationFrame: step the viewer's `update(dt)` from javascript to test walking and collisions.
- **The user finds defects from the walk viewer at odd angles**, never in the photo-camera views: render close-ups
  from low, oblique, side and below-shelf angles before delivering.

## GrabCut dropped a gold rim against a red background (vase, 2026-11-09)
The rim's dark gold edge next to saturated red was labelled background: the mask was 15 px narrower a side on the
rim rows only, the camera solve (rim fixed as the size) then shrank the mouth and the user saw "the mouth is too
narrow". The neck below was right. Check the rim rows of the mask on a zoomed grid against the photo before solving,
and fill hand-read edge points where they differ (`fix_rim_mask.py` pattern).

## One product photo of a furniture set (dining set, 2026-11-09)
- **Procedural or average-colour materials are a fault, not a draft**: the user rejected them outright. Take every
  material from the reference's pixels; see `single-photo-scene.md`, "Materials from the photo".
- **Region averages hide flat light**: means at 13/255 with half the photo's contrast. Fit and report spread and the
  5th/95th percentiles too; look at a lightness-difference map.
- **Depth along the view is the weak direction on a table top** (~1 cm per pixel): objects placed separately lose
  their contact (a cup off its coaster). Enforce the relation, then check both outlines.
- **Default orientations of asymmetric parts are guesses** (a handle "to the left"): read them on a crop.
- **Quilting a thin strip of figured wood repeats in bands**; a grazing, sheen-covered surface has no grain to give.
- **BGR vs RGB**: a target colour in RGB applied to an OpenCV image turned the textures blue.
- **One-line edits to a Blender script can swallow the next statement into an `if`**
  (`if MODE=="id": a; film_transparent=True` made the match render opaque): check renders' alpha after edits.
- **Blender 5 node names**: `ShaderNodeTexWave` (not `ShaderNodeWaveTexture`). Looks for the Standard view
  transform: "Very High Contrast", "High Contrast", "Medium High Contrast", "Medium Contrast"; pass them through zsh
  with underscores (a space split the argument).
- **`json.dump` refuses numpy float32**: cast before saving a tuner's results, or the run's last minutes are lost.
- **A room changes the showcase cameras**: views placed outside the walls render the walls' backs.

## A round landmark from drone frames (Galata Tower, 2026-11-11)
- **Rotated copies of the seen side are patches**, whatever the frame-camera numbers say: vertical seams at every
  copy's edge, a window column repeating at the copy's period, a sawtooth where the foot band was copied. The user
  saw it from one look. Fill a non-periodic surface by quilting (`scripts/quilt.py`), a periodic one by whole bays,
  and render the unseen side from close before handing over.
- **Quilting's failure modes, each seen once**: one strip repeated (source pool too strict), kaleidoscopes (mirrored
  strips), ghost windows (photo tone mixed with synthesised detail), windows bunched (no spacing rule), a cable
  copied (no excluded columns). See `drone-frames-landmark.md`, "The side no frame shows".
- **A frame from another era** (before a restoration) solves into a different building: check each frame's state.
- **The denoiser blurs projected textures** in renders compared with photos; so does a 1.5 px pixel filter.
- **An albedo floor of 0.01** becomes 25/255 in sRGB: every dark opening turns grey.
- **Smart-UV bakes: unused texels have alpha 1 and P = 0**; filter on |P| before statistics by angle or position.
- **Flattening light towards a median of everything** pulls the well-seen part towards the poorly-seen part: take
  the target from the part the frames see best.

## A heritage tram from twenty web photos (2026-11-11)
- **Web photos of one line show several units and eras** (No. 115 under the wire, No. 34 on batteries, No. 47): the
  first delivery modelled the wrong car. Read fleet numbers and details on every photo; ask which unit.
- **Front-only points leave a camera's yaw free** (the rectified side smeared); a free focal without a prior went to
  208 px. Points along the side and a log-focal prior per photo.
- **Neither facets nor one oval** for a rounded end: soft joints between panels, the roof edge rolled, measured on the
  frontal photo; the all-oval version raised the frontal error 37.5 -> 42.8/255.
- **Flat door panels, a black box under the floor, glossy leather, seats facing the wrong way, lettering cut from a
  slanted photo**: each rejected; see `multi-photo-vehicle.md`.
- **A palette box over a floor takes hatch frames and glare** (white streaks in the wood): filter wood pixels by hue
  and saturation first; a rectified floor tile ran across the car instead of along it (check the tile's axis).
- **An edit that did not apply, then a measurement of the previous render**: the number "did not move". Delete the
  output before rendering, check the log for Error/Traceback, grep the edit.
