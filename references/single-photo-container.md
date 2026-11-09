# One photo of a container with things in it (a pen holder, a vase, a basket, a jar)

Built on `single-photo-revolved.md` (read it first): the container is a body of revolution and its camera comes from
its circles. What is new: **things standing in it** (their positions from the photo alone), a **see-through wall**
(a wire mesh), and the **contents seen through that wall**. Worked example: `examples/pen-holder-mesh/`, a black
wire-mesh pen holder with two grey-capped pens, a red-checkered pen, a black marker, scissors, a teaspoon, a glue
stick and a nail file, one 1500 x 2000 phone photo on a desk, no size given (rim assumed 9 cm across, confirmed by the
user afterwards). Result from the photo's camera: holder silhouette IoU 0.988 below the rim, the pens above the rim
3.7/255 mean colour difference, the rim 17, the wall 10 (blurred). About two hours.

## Steps

1. **Mask and edge points** (`masks.py`). A dark threshold inside a box, closed with an 11 px kernel (the mesh's holes
   fill), holes filled, biggest piece. Two traps: short dark background blobs beside the object (a chair's seat
   behind it) join the mask — remove with a tall vertical opening (221 x 1), the holder's columns are long and the
   blobs are not; and the pens crossing the rim cut notches in the mask's top, so sample the rim's top edge only in
   columns free of them and compare IoU below the rim. Edge sets: the rim's outer top (back half, side columns), the
   base's lowest contour, the wall's left and right silhouettes between the rings' side points (the rings' ellipse
   side points sit ~100 px above the bottom front point; rows below them are the ring, not the wall).
2. **Camera** (`solve_cam.py`): D, YC, HC, pitch, **roll**, F, the rim height h, the base circle (zb, rb) and the
   wall radius rw, least squares with a soft-L1 loss from several starts, the rim radius R fixed as the size.
   Residuals: point-to-projected-circle for the rim and base, and for the wall's silhouettes the ray's distance from
   the axis minus rw, in pixels. Roll mattered (1.1 deg: without it the left and right rim points disagreed by 13 px
   and the two wall sides fitted opposite tapers). The ring's lower front edge was not usable (a dark chair behind the
   mesh on one side made the ring and the mesh one dark run): drop it, set the ring's tube radius by eye (~2.5 mm).
   F was weakly determined (rms flat from 2000 to 2300 px): fix it (`FIX_F=2100`, between an iPhone's 1x and 2x at
   1500 px wide) and say so. Put z = 0 at the base ring's lowest point (`ZOFF` in the script).
   **Check the Blender camera against `cam.proj`** with `world_to_camera_view` on a few known points before any
   render: the roll's sign was wrong once (`Rotation(+RO,'Z')` after `Euler(pi/2-TH, 0, pi/2)` is right for
   `r' = cos ρ r + sin ρ up`) and the whole model sat 12 px to the right of the photo while every number looked fine.
3. **The rings and the wall.** A ring's solved circle is its **contour**, not its tube centre: seen from elevation e
   the base ring's lowest contour is at `z = zc - rt cos e`, `r = Rc + rt sin e`, so place the torus from that
   (the first build put the base ring 15 px too low). The wall is a plain cylinder of radius rw between the rings
   (rw 40.7 mm here, the rim 45, the base ring 41.3: the rings protrude, as the photo shows).
4. **The lattice** (`unwrap.py`, `prep.py`). Unwrap the photo onto the wall cylinder (0.1 mm/px, angle x height) and
   read the cell pitch off the autocorrelation of a patch: vertical period = cell height (3.6 mm), horizontal = cell
   width (3.0 mm; its peak is weak, the 2x peak shows too; confirm by counting cells on a zoom of the unwrap). The
   rows are staggered: the lattice is two families of lines `y = ±(b/a) x + k b`, a tile a x b, strands within w/2
   of a line (w 0.48 mm here). Cells around the circumference: round(2 π rw / a) = 85, so the tile repeats seamlessly.
   The **strand width is tuned against the photo's wall tones** (blurred means per region in `cmp.py`): the first
   guess (0.62 mm) made the sides 20 levels too dark. At grazing angles the photo stays lighter than any painted
   alpha (the wires blur); accept the last ~10 levels at the far sides.
5. **The contents' texture** (`prep.py`). Where the front wall covers them (pixels whose ray hits the wall cylinder
   between the rings: computed, not drawn), replace the photo with a filter that removes the wires: the **80th
   percentile** over a 13 px disc, then a 5 px median. Not a closing (a max filter): it spread every specular line of
   the silver pens into solid white. Above the rim the photo as it is. The wall's own colour: the 15th percentile
   (the wire's tone), blurred, projected with the angle folded, so the lit side's wires are lighter, as in the photo.
   The rings: the photo with everything brighter than the ring inpainted (`rim_tex.png`), or the back of the rim
   carries the pens that hid it in the photo, visible from above.
6. **The items** (`build.py`). An item standing on the base: its **bottom pixel's ray intersected with the base plane
   gives (x, y) outright**; its top pixel at the same depth (plus a small `dx` lean if the photo shows one) gives
   the height and lean. Solving instead for a given length picked wrong roots (pens 15 deg off). Read the bottom
   pixels off a gridded "un-meshed" crop (`grid_body_unmeshed.jpg`); where the bottom is hidden, extrapolate the
   item's image axis to the base. Depth ambiguity remains (a pen's apparent width is the only cue): spread the items
   plausibly and keep every one inside rw minus its radius. Each item is a lathe (pens: body, a wider cap, a rounded
   top), a tube ring (scissors' finger loops, elliptical), boxes (blades, a file, a spoon handle) or a flattened
   ellipsoid (the spoon's bowl). UVs: the face's own projection when it faces the camera, else the mirror about the
   item's own axis plane; **tops and bottoms a plain colour** sampled from the photo below the top (projected pixels
   streak there, seen from above). Blender's Python has no cv2: sample colours through `Image.pixels` (rows bottom-up).
7. **glTF**: colour and alpha must be one image on one UV set. Two UV maps (photo colour + tiled lattice alpha)
   exported as a merged 1500 x 2000 image and the lattice vanished. Bake the wall to one RGBA texture (u = angle with
   the seam at the back, v = height; 6144 x 1536 here, 72 px per cell) and use it in Blender too. The alpha goes
   through a Math > Greater Than 0.5 node into the Principled Alpha (exports as MASK).
8. **Compare** (`cmp.py`): IoU from a solid render of the holder alone (the lattice's holes would ruin a direct
   one), colour difference over the model, and per region both raw and blurred (sigma 6): the raw number on a mesh is
   mostly the two lattices' phase difference and means little; the blurred one is the tone. Then the lit views and a
   top view: the top view found the rim's pen pixels and the items' streaked caps.
9. **Real materials** (`pbr.py`, on the saved .blend): black painted steel for the wall (base colour 0.012, metallic
   0.5, roughness 0.45, the lattice alpha kept), the rings a touch glossier (0.28), steel (metallic 1, roughness
   0.18) for the scissors, spoon and file, the pens keep the photo's printing as base colour with emission off,
   an interior HDRI (Blender's `studiolights/world/interior.exr`) plus the area lights, Cycles 96 samples.
   Delivered as the main file next to the photo-projected one.

## What this method cannot do (say so)

- Items' depths in the container are guesses; what hides behind other items (the scissors' blades, a second finger
  loop, a spoon's handle) is simple geometry.
- The back of each item is its front's mirror; the back of the container is the front's fold.
- The photo's lattice and the model's never register wire for wire; a per-pixel difference over the mesh is not a
  measure of anything.
- The size is assumed unless given; F is set, not solved.
