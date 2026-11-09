---
name: reference-to-3d
description: Turn reference images of an object (a multi-view turnaround sheet, or separate front/side/rear/top pictures, photos or AI concept art; or one picture of an interior such as a vehicle cockpit seen from one place; or one photo or render of a room, also made walkable; or several phone photos of a real room taken from different places, made walkable with the corridor outside and an openable door; or one ordinary photo of a real product of known size, such as a laptop on a table; or two photos (front and side) of a product whose size is unknown, such as a desk phone; or one photo of a turned object such as a pot, bottle or vase; or one photo of a container with things in it, such as a pen holder with pens; or one product photo of a furniture set with objects on it and its room, such as a table with a bench, stools, cups and a plate) into a 3D model in Blender that looks like the reference ("birebir", "exactly like the picture"): shape fitted to the reference silhouettes, the reference's own pixels projected on as its texture, measured view by view against the reference, then saved as a .blend and/or baked and exported (glTF) for a game engine with moving parts (wheels, doors) that keep their texture. Use this whenever someone wants a 3D model made from or matching images of a product, vehicle, prop, furniture, gadget, building element or character sheet, wants an existing model to match a reference more closely, or says things like "referanstaki aracın aynısını yap", "bu görselden 3B model", "resimdeki bilgisayarı 3d modelle", "ekteki resmi 3d modelle", "klasörde odanın fotoları var, 3d modelle, gezinebilir olsun", "make a 3D model from this concept art", "model this from these views", "photoreal model from the picture", even when they do not mention Blender or textures.
---

# Reference to 3D

A reference picture is the most precise description of a look anyone will ever give you. Modelling "something like
it" by eye and tuning colours by hand plateaus far from the picture (on one van model the mean colour difference
stalled at 26/255 after many rounds, and the user rightly rejected it twice). What gets to "identical" is to use the
reference itself: its silhouettes for the shape, its pixels for the surface, and numbers, not impressions, to judge.

## The bar: identical, and the loop that gets there (read first, every time)

The user's goal is a model **identical to the reference**, not one that resembles it. Two rules follow, and the user
had to state both after a delivery (2026-11-09, a dining set from one product photo: "bir daha gerçek dışı, average
color, ya da procedurally material olan şey üretme. Birebir aynı olması hedef" and "bu karşılaştırma arada fark
kalmayıncaya, gerçeğiyle birebir eşlene kadar devam etmeliydi"):

1. **Every material comes from the reference's own pixels.** Colour, grain, weave, speckle, gloss: take them from the
   reference (rectified or unrolled exemplars of that surface, light divided out, grown into a seamless tile; the
   palette mapped by luminance quantiles of the reference's pixels; band spacing and contrast measured on them). A
   flat average colour, an invented procedural texture, or a texture "in the right colour" is never the material.
   Procedural detail is allowed only below the reference's resolution (pores finer than its pixels) and only on top of
   the reference-derived pattern; check every tile at the reference's resolution next to its exemplar.
   `references/single-photo-scene.md`, "Materials from the photo".
2. **Compare until nothing differs, then compare again.** After every build render from the reference's camera and
   put the reference and the render side by side, as the whole frame and as close-up crops of every object and
   material (a border render at 4x through the same camera). Measure, per region and per object: mean colour,
   contrast (lightness spread), the dark and light ends (5th and 95th percentiles), saturation; draw every part's
   outline over the reference (object-ID render) for shape and placement. Fix the largest difference, render,
   measure again. **Do not hand over while a difference is visible or measurable**: keep iterating without being
   asked. Matching region averages is not "identical" (the dining set matched 13/255 on averages while its contrast
   was half the photo's: the user saw it as "soluk" at once). If a difference cannot be closed, say which one, with
   its numbers and why, never "close enough".

The user checks what you skipped: a cup standing off its coaster, a handle turned the wrong way, a plate, muffins and
a plant in the wrong shape, a matte sphere that is glossy in the photo, a whole render paler than the photo. Each was
visible in a side-by-side crop that had not been made. Make it before they do.

The scripts are in `scripts/`. Every one takes `--help`-style docs in its header; read the header before first use.
Python ones run with `uv run --with ...` (the header names the packages); `project.py` runs inside Blender
(`/Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/project.py -- ...` on macOS).

The object's frame, shared by all scripts: **+X its front, +Y its left, +Z up, x and y centred, the bottom at z = 0,
metres.** Views: `front` (seen from +X), `rear`, `left` (seen from +Y: the front at the image's left), `right`
(the front at the image's right), `top` (`--top-front` says where the front is in that image).

**One picture of an inside** (a cockpit, a room) to be seen from one place (a driver's seat, a fixed game camera) is a
different case: no views to fit a shape to, but one viewpoint to make exact. Project the picture from that camera onto
simple surfaces of the inside; read `references/single-view-interior.md` and skip steps 1-3 below. When the picture
is a real photo or render of a room and the room is to be **walked through** ("odanın içi dolaşılabilir mi"), read its
section "A photo or render of a room to walk around": the camera solved from the picture's lines
(`scripts/solve_camera_vp.py`), props as proxies with layered clean plates behind them, and the unseen sides built from
the picture's own repeats (`scripts/rectify_plane.py`; worked example `examples/laundromat-room/`).

**Several ordinary photos of a real room** (phone shots from different places, maybe asked for more of them later),
to be **walked through** with the corridor outside and a door that opens, is a sixth case: one parametric room and all
cameras solved together from hand-read structural points and shared furniture (lens-class focal priors against the
focal–distance trade), textures by rectification or homography from the sharpest photo of each surface, and every prop
modelled from a photo of it. Read `references/multi-photo-room.md` first, especially "What the user rejected"
(worked example `examples/office-room-multiphoto/`). Never put a stand-in object in the room silently: the user walks
round every prop.

**One photo of a real product whose size is known** (a laptop on a table, a phone, an appliance, a chair) is a third
case: no views to fit a hull to, but known dimensions and simple parts. Solve the photo's camera (and any joint's
angle, such as a lid's) from a few marked corners, build the product from its real dimensions, and rectify each
surface the photo shows into its own texture through that camera; raised details (keys) take the photo's pixels
along the camera's rays. Read `references/single-photo-object.md` (worked example and scripts in
`examples/laptop-single-photo/`) and skip steps 1-3 below; steps 4, 6 and 7 still apply.

**Two ordinary photos of a product whose size is unknown** (a desk phone, a printer, a kettle: front and side, no
EXIF, no published dimensions) is the third case with a second camera: solve both cameras and one body together
from the photos' straight edges (as image lines, not corners) and features seen in both (buttons), fix only the
width; fit a part that moved between the shots to each photo and both. Read `references/two-photo-object.md`
(worked example `examples/desk-phone-two-photos/`). When one photo leaves a height or slope unreadable, ask for the
side photo instead of shipping a prior. Every part's shape comes from a photo (plan, side arc, steps, where a cord
leaves); nothing is added because such products "usually" have it.

**One product photo of a furniture set with things on it** (a table with chairs, a bench and stools; cups, a plate,
candles, a plant on the table; a room around it) is a seventh case: a level camera with its principal point solved
from the table top's edge lines and the leg feet, each seat fitted to its cushion's silhouette as a rounded box,
splayed legs from their image axes and feet, every object on the top placed by its base pixel on the top plane and
its relations to the others enforced (a cup stands on its coaster), every material taken from the photo's pixels,
the room (floor, walls, curtains, the window) modelled from the photo because it lights and reflects into every
material, and the light fitted to the photo's contrast as well as its colours. Read
`references/single-photo-scene.md` (worked example `examples/dining-set-single-photo/`).

**One photo of a vehicle of a known type** (an airliner, a car, a ship; often an AI image whose proportions are not
quite the real type's) is an eighth case: the type's real dimensions become priors with sigmas, the camera is solved
from points on known geometry (tips, wheel contacts, the fin's top) plus the silhouette of a part whose section is
known (the fuselage), the vehicle is a set of parameters (rings, aerofoil stations, a winglet arc) fitted to the
photo's silhouette by rasterising it in numpy, the photo is unwrapped onto every part through a depth test and
mirrored to the unseen side, and the sun is solved from the vehicle's shadow. Read
`references/single-photo-vehicle.md` (worked example `examples/airliner-single-photo/`).

**One photo of a container with things in it** (a pen holder with pens and scissors, a vase with flowers, a basket, a
jar; the container itself turned, its wall possibly a see-through mesh) is a fifth case, built on the fourth: the
container's camera from its circles plus a roll parameter, each item standing on the base placed by intersecting
its bottom pixel's ray with the base plane, a mesh wall as an alpha-clipped lattice whose pitch is measured on the
photo unwrapped onto the cylinder, the contents behind the mesh textured from a percentile filter that removes the
wires. Read `references/single-photo-container.md` (worked example `examples/pen-holder-mesh/`) after the fourth
case's reference; steps 4, 6 and 7 still apply.

**One photo of a turned object** (a pot, a bottle, a vase, a lamp, a cup; with handles, knobs or a spout on its
sides) is a fourth case: the silhouette's two edges are its profile. Solve the camera from the ellipses of two of
its circles (base, rim), lathe the profile measured through that camera, make each side part a rounded slab or
(bar-like handles) a swept tube of its photo outline, and wrap the photo round the axis with the angle folded into
the part the photo sees well (the back the front's mirror, the logo left off it); a cup's inside from what the
opening shows. Read `references/single-photo-revolved.md` and skip steps 1-3 below; steps 4, 6 and 7 still apply.
Worked examples: `examples/pressure-cooker-revolved/` (a product shot on white, level camera read by hand) and
`examples/mug-revolved/` (a phone photo on a table: GrabCut mask, pitched camera by least squares, hollow inside,
tube handle, porcelain version), `examples/cologne-bottle-revolved/` (a clear PET spray bottle: a cropped photo
from a level camera, transparent body, skewed label, a head askew on the body, real materials with a printed label),
`examples/vase-checker-revolved/` (a hand-painted checkered vase on a busy background: rim mask repaired by hand,
foot and camera solved together, the pattern rebuilt 360 deg from the unwrapped photo, gold as metal bands).

## 1. Read the reference before anything else

1. Split the sheet: `split_sheet.py sheet.png --out panels` and look at `panels/index.jpg`. Name the panels
   (`--rename "0=front,2=left,3=rear,5=top"`). Three-quarter views are not used for the shape or texture, but keep
   them: they are the honest test of the result.
2. Decide each side view's name by where the object's front is, and the top view's `--top-front`.
3. Get one real size (height, length or width) from the user or from common sense (a mug ~0.1 m tall, a van ~1.9 m);
   the rest follows from the views' proportions.
4. Look for disagreements between the views, and expect them in AI concept sheets and photos: the same part at
   different widths or heights in different views, a top view out of proportion. These are usually **perspective**:
   a close camera makes near parts large (a van's front view showed its bumper 12 % wider than its top and rear
   views allowed). Note them now; later you will choose, with the user, which view rules where (step 5).

## 2. Build the shape from the silhouettes

Choose by the object:

- **Any object** (furniture, gadgets, figures, props): `hull.py` — the visual hull, voxels every silhouette agrees
  on, meshed smoothly. It handles holes seen in some view (a mug's handle). It cannot see hollows no view shows (a
  cup's inside, a seat's dip): add those after, by hand or with a boolean.
- **Long objects with a clear length axis** (vehicles, boats, aircraft, shoes, bottles lying down): `loft.py` —
  cross-sections along x from the side, front/rear and top views; light, clean topology. Separate moving parts
  (wheels, propellers, doors) as their own meshes (simple primitives placed at the positions measured on the side
  view), so they can turn and get their own texture later.
- If the user has image-to-3D credits (Meshy, Tripo, Rodin...) and asks for it, a generated mesh can replace this
  step; spending credits needs their approval. Everything after this step stays the same.

Check the fit before texturing: render silhouettes (`project.py ... --render DIR --shots front,left,rear,top --mask`)
and run `compare.py`. Aim for silhouette IoU above 0.97 on the views that matter; fix the shape first, because
texture on a wrong shape only moves the error.

## 3. Texture from the reference's pixels

1. `textures.py --panels panels --views front,left,rear,top --out tex` (fills each view's margin outward and
   upsamples it).
2. `project.py -- --mesh body.obj[,wheel_fl.obj,...] --tex tex --views front,left,rear,top --render out` renders the
   four flat views and three quarters. Each surface point takes the one view that faces it best (`--power 16`):
   blending views doubles every feature the views place differently.
3. `compare.py --panels panels --render out --views front,left,rear,top` → per view silhouette IoU and mean colour
   difference (0-255), side-by-side and difference images. Typical good numbers: 0.97+ IoU, under 15/255.

Options worth knowing (all in `project.py`'s header):
- `--top-min-nz 0.88`: the top view only on near-flat tops. Steep surfaces facing partly up (a raked windscreen) then
  take the front's pixels, which is what someone looking at the front expects.
- `--mirror off`: an object that is not left-right symmetric needs both side views; mirroring one side onto the other
  paints the wrong side (a mug's handle shadow appeared on its handle-less side).
- `--persp "rear=12,1.0"`: a view that was a close perspective shot, its camera D m beyond the object, H m up. Find D
  and H by rendering masks at a few values and keeping the best IoU (the van's rear: 0.913 flat, 0.978 at 12 m).
- `--under dark`: undersides no view sees, dark instead of a stretched side.

## 4. Look, measure, fix — one view at a time

Show the user the comparison sheet (reference left, model right), not just the model. When they point at a
difference, measure that region (mean colours of the same box in both, or the difference image), find its cause, fix
the cause, measure again. Causes seen so far, in `references/pitfalls.md`; read it when a number does not move.

Do not claim "identical" from a feeling. Say which views match how well, in numbers, and what still differs and why. This step
is a loop, not a check: it ends when no difference remains (see "The bar: identical" above), not when the numbers
look good.

Then look closer than the comparison views do, the way the model will really be seen: close-ups of the parts people
get near (wheels, lamps, handles, labels), and, for a vehicle or a room someone sits in, the view from the seat. The
whole-view numbers were fine on a van model while its wheels' treads carried the headlamps' pixels and its cab
was a box and a ring; the user found both in the game. Each close-up is a blunt critique: list what looks wrong, fix
the worst, render again.

## 5. Conflicts between views: decide with the user

When views disagree (step 1.4), no single shape matches all of them. Make the trade explicit: "matching the front's
bumper width makes the van widen towards the front when seen from above". Recommend one and let the user choose. A
common good split: the body's widths from the view whose surfaces are all at one depth (a flat rear), the nose's from
the front, each texture fitted to the model's own outline (`project.py` does this by default).

## 6. Deliver

- **Blender file**: `project.py ... --blend model.blend --pack` (textures inside: it opens anywhere). It opens
  framed on the model in Material Preview; Z → Rendered shows the scene's own lights. **Before handing over any
  .blend, open it with the interface and screenshot what the user will see** (`scripts/shot_ui.py`, absolute paths:
  `Blender "$PWD/model.blend" --factory-startup -P scripts/shot_ui.py -- "$PWD/ui.png"`): a file written by a render script opened as a tangle of camera frustums and light lines round a
  31 cm laptop on a 4 m floor, far away and grey. Remove the render shots' cameras, put the model under one parent
  in its own collection and lights/floor/camera in another, scale the floor to the object, select the model.
- **Game asset**: `project.py ... --export model.glb [--emission] [--decimate 0.1]` (a visual hull is dense: thin it) bakes each mesh to its own UV texture (so a
  wheel's pattern turns with it) and exports glTF. For engine specifics (names, pivots, windows and interiors, Unreal
  import), read `references/game-export.md`.
- Say what the method cannot do: the reference's lighting and reflections are baked into the texture (it will not
  react to a night scene like a real material), and surfaces no view shows are guesses.

## 7. Finishing

**The real-material version is part of the deliverable, not an offer.** The user said so (2026-11-09, a cologne
bottle: "bana yaptıktan sonra gerçek malzeme sürümü yapıyım mı diye sorma zaten bu olması gereken bişey"). Do the
photo-projected version first, for the fit check and its numbers, then go straight on to real materials and deliver
both, the real-material file as the main one. Also straighten accidental askewness seen in the photo (a crooked
sprayer head): in a product model the user reads it as a flaw. The other items below (printed matter redrawn, wear,
motion, a reference made from nothing) are still offers.
- **Parts the reference cannot carry**: wheels' tyres, glass, lamps, screens and interiors in real materials instead
  of projected pixels (a tyre's tread seen from ahead is not in any view; a lamp must light at night). Keep the
  reference's pixels where a view really shows the part (a rim from the side).
- **Real materials are the reference's materials**: their colours, textures and gloss come from the reference's pixels
  (rule 1 above), each material's albedo calibrated by measuring the same regions in the reference and the render
  under a light fitted to the reference's contrast, not only its averages. Model what surrounds the object in the
  reference (floor, walls, window, curtains) when it lights or reflects into the materials: a studio world turned
  the dining set's wood flat and its lacquer dull. `references/single-photo-scene.md`.
- **Real materials instead of the reference's light**: polished metal, plastic, glass that react to the scene (the
  photo's reflections are baked in and show the photographer's studio from every side). Keep printed matter as a
  mask baked into the base colour and roughness maps, not as shader nodes: the glTF exporter drops Gamma and Mix
  nodes. Polished metal needs something to reflect: a bright world and black cards that only reflections see.
  `references/single-photo-revolved.md`, "Real materials".
- **Printed matter**: logos, labels and lettering redrawn sharp (as vectors or a high-resolution image) when close-ups
  show the reference's pixels too soft.
- **Wear**: dust, grime in creases, chipped edges, from shader nodes (ambient occlusion, pointiness, noise), as a thin
  layer over the projected colour, never painted into it.
- **Motion**: a turntable (the camera round the object in 4-8 s, 24-30 frames a second, rendered to MP4) or a slow
  push-in, to show the result; a game asset's moving parts turning in it.
- **No reference at all**: make one first (a concept sheet from an image model, with the user's approval: it costs
  credits), then follow this skill from step 1.

## Files

- `scripts/split_sheet.py` — sheet to named panels and masks
- `scripts/hull.py` — visual hull mesh (any object)
- `scripts/loft.py` — lofted mesh (long objects)
- `scripts/textures.py` — panels to textures
- `scripts/project.py` — Blender: projection material, renders, .blend, bake + glTF export
- `scripts/compare.py` — IoU and colour difference per view, comparison sheets
- `scripts/shot_ui.py` — opens a .blend with the interface, screenshots what the user will see, quits
- `scripts/solve_camera_vp.py` — a room photo/render's camera from its vanishing points (f, pitch, yaw, scale) -> cam.json
- `scripts/rectify_plane.py` — one plane of the room rectified out of the picture through cam.json (textures, measuring)
- `references/pitfalls.md` — what went wrong before and why (read when stuck)
- `references/game-export.md` — game engine delivery (read before exporting for a game)
- `references/single-view-interior.md` — one picture of an inside, made exact from one camera (a cockpit, a room)
- `references/single-photo-object.md` — one photo of a product of known size: camera solve, rectified textures, raised details
- `references/single-photo-revolved.md` — one photo of a turned object: camera from two ellipses (level by hand, or pitched by least squares), lathed profile, handle slabs or swept tubes, folded-angle texture, a hollow inside, real materials (steel, glazed ceramic, clear plastic with a printed label); a level camera on a cropped frame, transparent bodies, parts askew on each other
- `examples/laundromat-room/` — a room from one render, made walkable (camera solve, proxies, layered plates, repeats, shader projection)
- `examples/laptop-single-photo/` — the MacBook Pro 14 worked example (edge measuring, camera solve, overlay, rectify, key layout fit, Blender build, compare, glTF export)
- `examples/pressure-cooker-revolved/` — a pressure cooker from one product photo (masks, camera from ellipses, profile, handle slabs, folded UVs, compare, steel/plastic version)
- `references/two-photo-object.md` — two photos (front, side) of a product of unknown size: joint two-camera solve from edge lines and shared features, parts that moved between shots, shapes read from the photos (plan, side arc, steps, parting-line ribbon), de-lit albedo without shadows, exposure by measuring
- `examples/desk-phone-two-photos/` — a corded desk phone from a front and a side phone photo (edge-line and key measuring, joint solve, handset fit, side-photo features, match/final/PBR builds, Cycles showcase)
- `references/single-photo-container.md` — a container with contents from one photo: camera with roll, items by base-plane intersection, see-through mesh wall, one RGBA wall texture for glTF
- `examples/pen-holder-mesh/` — a wire-mesh pen holder with four pens, scissors, a spoon and a glue stick from one phone photo (circle + wall-tangent camera solve, lattice pitch from the unwrapped photo, percentile un-meshing, real-material version)
- `examples/mug-revolved/` — a porcelain mug from one phone photo on a table (GrabCut mask, pitched camera solve, tangent-ray profile, base fit, swept-tube handle, inside texture, compare, porcelain version)
- `references/multi-photo-room.md` — a real room from many phone photos, walkable with the corridor and an openable door: joint room + camera solve (shared furniture, lens priors), late photos by PnP or vanishing point, rectified/homography textures, books as leaning prisms, devices from side profiles, colour calibration, viewer testing, and what the user rejected
- `examples/office-room-multiphoto/` — the office + corridor pipeline (obs/fit bundle adjustment, camlib rectify, pnp, corridor solves, prep_* textures, build/build_detail Blender scene, shots/sheet/calib checks, finalize, three.js walk viewer)
- `examples/vase-checker-revolved/` — a checkered porcelain vase from one product photo (GrabCut + hand-read rim, pitched camera with the foot fitted jointly, binned profile, unwrap to (angle, z), 360 deg checker albedo, gold bands, mirror tray, colour by measuring then by the user's eye)
- `references/single-photo-scene.md` — a furniture set with objects on it and its room from one product photo: level camera with principal point from edge lines and feet, cushions by silhouette fit, splayed legs, objects by base pixels with contact relations, materials from the photo's pixels (exemplars, quilting, quantile palettes), room from the photo, light fitted to contrast, per-material albedo calibration, the compare-until-identical loop
- `references/single-photo-vehicle.md` — one photo of a vehicle of a known type: dimensions as priors, camera from known points plus a fuselage silhouette, parametric parts fitted by numpy rasterising, photo onto UVs through a depth test with mirrored partners, sun from the shadow, light passes fitted linearly, albedo gain maps, what an AI picture's light can refuse
- `examples/airliner-single-photo/` — the 737-800 at sunset: solve (points + silhouette), secs/geom parametric aircraft, fit_wing/fit_body, bake + texbuild, sunfit, ground tile and sky, albedo + calfit + albedo_cal, deliver (.blend, .glb)
- `examples/dining-set-single-photo/` — the dining set (table, bench, two stools, cups, coasters, plate, muffins, candles, plant) pipeline: edges/solve, cushion and leg fits, prep -> scene.json, extract2/oak2/floor/env textures and room, build (match/id/final), tune2 light fit, albedo_cal, cstats/calib/idov checks, final.sh
- `examples/cologne-bottle-revolved/` — a clear PET cologne spray bottle from one cropped phone photo (level camera with the principal point solved, edges only where the background differs, per-part tilt, de-shaded cylindrical label, double-walled glass with liquid, photo clean plate as refraction backdrop, exposure by measuring)
