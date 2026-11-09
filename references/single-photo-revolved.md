# One photo of a turned object (a pot, a bottle, a vase, a lamp, a cup)

A body of revolution needs only its profile, and one side-on photo shows the profile twice, as the silhouette's left
and right edges. What it does not show is everything behind the silhouette and every side handle's depth. So:
**solve the camera from the ellipses of the object's own circles, lathe the profile measured through that camera,
build side parts (handles, spouts, knobs) as rounded slabs or swept tubes of their photo outlines, and wrap the photo
round the axis with the angle folded into the part the photo sees well.**

Three worked examples; where they differ, the steps below say which fits your photo:
- **A product shot on white with a level camera**: a stainless pressure cooker, one 554 x 554 product photo, no size
  given. `examples/pressure-cooker-revolved/`. From the photo's camera: silhouette IoU 0.98, mean colour difference
  8.3/255 over the model (median 1.0, body 1.5); a second version in real materials (polished steel, plastic). About
  an hour, most of it in the faults below that only looking found.
- **A phone photo from close and above, on a real background**: a white porcelain mug on a wooden table, one
  1500 x 2000 phone photo, no size given. `examples/mug-revolved/` (camera, profile, base and handle mostly automatic
  where the cooker's were read by hand; a hollow inside; a loop handle). From the photo's camera: IoU 0.982, mean
  colour difference 1.4/255 (body 0.2, inside 3.1, handle 4.4); a second version in real porcelain.
- **A cropped phone photo of a clear bottle**: a 100 ml PET cologne spray bottle with a wrap-around label, a black
  ribbed collar and a smoked cap, on a table, one 1500 x 2000 photo that is a crop (the principal point came out at
  row 173). `examples/cologne-bottle-revolved/`. Level camera with the principal point solved, silhouette edges
  only where the background differs, the sprayer head's own tilt, a de-shaded cylindrical label. Photo-projected:
  IoU 0.966, 2.3/255; real materials (double-walled clear PET, liquid, printed label, smoked cap) within 5 levels of
  the photo on the label, cap and collar.

## Steps

1. **Size.** Ask, or assume from the product (a 10 L pot ~27 cm across, a mug's rim ~8.5 cm) and say so. Everything
   else is in proportion, so a wrong guess scales the model, nothing more.
2. **Masks.** On white: flood fill of the background from a corner (white, low saturation), so bright highlights
   inside the object stay in it. Each side part: dark pixels inside a box you set from a grid over the photo
   (`examples/laptop-single-photo/grid.py`), so the object's own dark reflections (a steel pot's edges are dark
   strips) do not join the handle. Add a part's light brackets (metal) by box. **Look at every mask over the photo**
   (`masks.py` writes `masks_vis.png`): a box edge cut a tab's bottom 7 px off, and a thin dark line (the lid's edge)
   joined the tab's mask; both showed up later as smears on the lid. Open thin lines away, keep the biggest piece.
   **On a real background** (a table, a wall): GrabCut with a box round the object, bright low-saturation pixels as
   probable object, and sure-object polygons drawn well inside the outline (a sure box that crossed the mug's
   tapering bottom pulled the table into the mask). Then repair what GrabCut gets wrong: a thin bright table edge
   joined the outline (open it with a tall 31x1 kernel), and a part's **shaded upper face**, grey against the beige
   seen through a handle's hole, was left in the hole: inside the hole, low saturation is object.
   A side part's mask can then be the silhouette minus the **lathed body's own silhouette**, rendered alone from the
   solved camera (steps 3-4 first): no hand-drawn boxes.
   **A transparent body** (a clear bottle) has no mask: GrabCut finds the opaque parts (cap, collar, label) and
   nothing of the clear PET over a same-toned table (the bottle's right edge was invisible for 500 rows), and what
   it sees through the base (the thick grey bottom) is not the outer wall. Take each straight part's edge only on
   the rows where the background differs (the left edge against the dark table edge, the right edge where the floor
   showed behind it), fit a line per edge and extend it; treat inner features seen through the plastic (the foot
   ring) as circles with their own radius, never as the silhouette. Judge the IoU on the rows the mask is good on.
   **A sticker's edges are not level circles**: the wrap-around label sat skewed, its edge arcs were asymmetric (a
   sag of 42 px read from the left side, 29 from the right) and a soft printed band gave a flat-bottomed arc. Use
   moulded features for the camera (a collar's bottom rim, the shoulder's outline, the foot ring, straight edges).
3. **The camera from two circles.**
   *Level camera, read by hand (product shot).* A level camera at (D, 0, Hc), focal F px, principal point (cx, cy)
   (a level camera keeps the verticals vertical; the crop's offset is the principal point). Under perspective a
   horizontal circle of radius r at height z shows as an ellipse whose front point lies below its side points by
   about `F (Hc - z) r / (D (D - r))` px. Read that drop on two circles at different heights (the base: 23 px; the
   lid's flange: 8 px), and the scale at the axis k = F/D from one known radius: two equations give D and Hc
   (1.55 m and 0.295 m; F = 1550 px, a long product lens). cx is the silhouette's centre column; cy follows from
   the base's side rows. Write it in `cam.py` with `proj(x, y, z)` and `unproj0(u, v)` (the plane of the axis).
   Two ellipses read by eye are worth a few px; a 2-4 px band where parts meet (below) is what that costs.
   *Pitched camera, least squares (a phone photo from close and above).* A level camera does not fit it: the mug's
   rim was seen at ~10 deg, its base at ~30 deg (the base ellipse half as tall as wide, the rim's a sixth). Solve
   D, YC, HC, pitch, F, the object's height and its base circle (one radius fixed as the size): sample the rim's
   back-half contour and side points and the base's front-half contour from the mask, and minimise each point's
   distance to its projected circle (`examples/mug-revolved/solve_cam.py`, rms 1.2 px). Add the rim's **front
   point** read off a zoomed grid (white on white, the mask cannot give it): without it the elevation was off by 8 px
   there. F is weakly determined (fits at 1700-2300 px differed by 0.1 px rms): print that scan and pick by the
   phone's lens (an iPhone photo 1500 px wide: 1x ~1130 px, 2x ~2050 px; portrait-mode blur means 2x). An uncropped
   phone photo has its principal point at the centre. Roll: the mug's 0.3 deg was not worth a parameter, but the
   pen holder's 1.1 deg was (without it the rim's left and right edge points disagreed by 13 px and the wall's two
   sides fitted opposite tapers): solve it whenever the two sides disagree, and get its sign right in Blender
   (`references/single-photo-container.md`).
   *Level camera, cropped frame, least squares (the cologne bottle).* **Check the straight edges' convergence
   first.** A cylinder's apparent width is set by its depth along the optical axis, so a level camera shows a
   straight body at one width whatever its height, and the sags of its circles then come from the camera's height
   alone. The bottle's edges stayed parallel (332 -> 337 px over 560 rows) while its circles sagged more the lower
   they sat (collar bottom b/a 0.18, foot ring 0.40): a pitched camera with the principal point at the centre cannot
   do that (it would have narrowed the base 5 % or put the horizon far below the frame), and an afternoon went into
   trying. The photo was a crop: free the principal row CY (the edges' convergence tells pitch from CY, so keep both
   in the solve), fix CX, and let F come from the sags' ratio at two heights with the known radius (3480 px here,
   D 0.42 m, camera 0.19 m up, pitch 2.5 deg). `examples/cologne-bottle-revolved/solve3.py`: body edges as tangent
   rays, each part's top and bottom circle side points (tangent rays on a near-cylinder constrain radii, not
   heights: without them the collar's top and bottom inverted), the collar's bottom arc, the shoulder's outline and
   the foot ring as a feature circle; multi-start over pitch and F from the same x0 (chaining starts biased the
   scan), and read the overlay before believing the rms. **A part askew on the body** (the sprayer head leaned
   1.6 deg more than the body) gets its own rotation about the viewing axis at the joint, or it contaminates the
   camera's roll; set it to zero in the product model and say so.
4. **The profile.** *Level camera:* for each clean row (no handle, no base ring), the half width hw gives
   r = hw (D - x_t) / F with x_t = r^2 / D (the silhouette is where the ray grazes the surface, a little in front of
   the axis; iterate), and z from the row at x_t. Fit what is simple (the cooker's wall was linear:
   r = 0.1196 + 0.0775 z, residual 1.4 mm). Read the short features (base corner, rim roll, lid flange, dome) off
   zoomed grids, each checked by its front point's row.
   *Pitched camera:* rays are not horizontal, so use each edge pixel's ray and find where it grazes the surface: the
   minimum over the ray of (distance to the axis - r(z)), iterated against a smooth fit of r(z)
   (`examples/mug-revolved/profile.py`). Search only near the ray's closest approach to the axis and clip the fit to
   its data's range: a spline evaluated beyond its data blew the iteration up. Leave out the rows where a handle's
   roots join the edge, and reject outliers.
   Either way, **the lowest rows are the base's front edge, not tangents**: the mug's profile came out 30 px too wide
   there. Fit the bottom corner on its own (`fit_bottom.py`: a superellipse from the foot ring up to the profile,
   compared row by row with the mask; a solid of revolution's silhouette is the union of its projected discs, so no
   render is needed). Lathe (160-180 segments) as separate objects for separate parts (pot, lid).
5. **Side parts.** *Rounded slabs* (flat handles, tabs, knobs): from each part's mask, a half-thickness h(u, v) that
   rises over r (8 mm) from the outline as a quarter circle, the solid |x| <= h, meshed by marching cubes at 2x the
   photo's resolution, the vertices placed with `unproj0` (the parts sit in the plane of the axis). The thickness is
   a guess (the photo is side-on): 30-40 mm for handles. Dense (150k vertices): decimate to ~12 % before saving.
   *Swept tubes* (a mug's loop handle, a bail, a spout: anything bar-like): the slab showed ridges across the mug's
   handle (the mask's pixel steps) and weighed 270k vertices. Instead take the in-plane shape S on a grid in the
   part's plane (metres), its skeleton (longest path) as the centre line, smoothed and resampled every 0.5 mm, its
   distance transform as the half thickness, and sweep a superellipse section (exponent ~2.6) with the guessed depth
   (12.5 mm for the mug); carry the ends a few mm into the body and cap them there. 9.6k vertices, clean shading.
   What the mask hides:
   - **seen from above, a part's mask holds its upper face too**: take S where both faces (x = +-0.7 depth/2)
     project inside the mask, not the mask itself;
   - that cut and the skeleton make it thin: the mug's handle needed x1.12, the skeleton's tips taper to nothing
     (hold the thickness from 3 mm off the body), and real roots flare (lower +50 %, upper +30 % over 6-7 mm);
   - check its outline from the photo's camera over the photo, edge by edge, after each change.
6. **UVs through the camera, angle folded.** Each vertex's UV is `proj` of a point on the same circle at a folded
   angle: within +-A (72 deg) the vertex's own angle (the photo's pixels as they are); beyond, the back is the mirror
   of that part, stretched to reach 0 (the photo's centre) at 180 deg, so the seam closes. Outside +-A use a plate
   with the logo removed (each column interpolated across it), so the logo is not repeated, mirrored, on the back
   (and any dirt specks: inpaint them on that plate). Handles: faces towards +-X take the photo (the back mirrored,
   |x|), the rest a plastic material; a tube's faces take their own projection when facing the camera, else the
   x-mirror's. The undersides (normal down) a flat material. Body texture: the photo with the handles inpainted where
   they cross the body, the margin outside the silhouette filled outward from the nearest object pixel.
   - **Fold less on a side part's side**: near the silhouette a glossy body mirrors its handle; stretched by the
     fold, the reflection became a D-shaped ghost on the mug's body behind the handle. Fold at 50 deg on the
     handle's side, 72 on the other.
   - **Fill a part's margin smoothly** where its side faces read pixels near its edge (a tube's flanks project onto
     the outline): nearest-pixel fill makes streaks perpendicular to the edge, which show as stripes across the
     part. Erode the part's mask ~5 px (edge pixels are mixed with the background) and fill by normalized Gaussian
     convolution, finest scale first.
7. **A hollow inside** (a cup, a pot without its lid, a vase's mouth): the photo sees the far wall's top band through
   the opening. Lathe the inside with the outside as one closed profile (outside, lip, inside wall, floor; wall
   3.5-4.5 mm for porcelain). Project every inside vertex through the camera, the near half mirrored to the far half
   (x -> -x). The inside texture is the photo within the opening (the rim's inner circle projected, eroded), blended
   over a few px into a plain inside colour (the median just above the opening's front edge) outside it: whatever
   the photo does not see reads the plain colour, with no seam. A per-face visibility test instead gave staircase
   patches. **The lip's inner half belongs to the inside**: with the outer texture it drew a white band along the
   back of the rim.
8. **Compare from the photo's camera** (emission, Standard, film transparent): IoU (above the floor's shadow, if
   any), colour difference over the model and per region (`cmp.py`). Then look from three-quarters, above, from the
   handle's side and close to it: the D ghost, the handle's stripes and its thin root were all fine from the photo's
   camera and only showed there.
9. **Deliver** the tidy .blend (Material Preview, framed, model and studio in collections) and a .glb; open it and
   look (`scripts/shot_ui.py`, with absolute paths).

## Real materials (always: the second half of the deliverable)

The photo's reflections are baked in: the object shows the photographer's room from every side and does not react
to a scene. Make the swap without asking (SKILL.md step 7): the photo-projected version is the fit check, the
real-material version is what the user keeps.

**Steel** (the cooker): polished stainless (metallic 1, roughness 0.08), the lid satin (0.16), the base matte (0.3),
handles black plastic (roughness 0.5, specular 0.3) with the photo's details on their faces, darkened. Keep the
printed logo: the clean back plate minus the photo is its mask; upsample 4x, smooth, and bake it into a base colour
and a roughness map (dark satin print). Light it as a product shot: a bright world and black cards that only
reflections see (`visible_camera` off), which draw the dark vertical bands that read as steel. In the viewport use a
built-in HDRI (interior.exr) and hide the cards. `steel.py`.

Cards in front serve a low camera only. From 20-25 deg above, polished steel mirrors the **floor**: a white floor
made the body flat white, a floor dark in reflections made it black. What reads as steel from any side: the floor
white to the camera but, in glossy rays (Light Path "Is Glossy Ray"), light with dark sectors round the object
(smoothstep of sin(5 x angle)), which a cylinder shows as vertical dark bands; and a ring of tall black cards for
the upper part. `showcase.py`.

**Glazed ceramic** (the mug): glaze roughness 0.07, IOR 1.52; the unglazed foot ring matte (0.65), a little warm.
Keep the photo's small details (dirt specks, water marks) without its light: base colour = flat white x (photo /
photo blurred at ~18 px), the ratio clipped and trusted only away from the silhouette, the lip and the opening's
edge (their shading came back as dark rings all round), fading to 1 elsewhere (`pbr_maps.py`). Light: interior.exr
plus a key from the photo's side. **Set the exposure by measuring**: the first render (HDRI at 1.0 and the lights)
was all white. Render the photo's camera only, compare the mean of the same body boxes (left, middle, right) and a
table box with the photo, and set exposure (AgX: -1.6) and the key/fill ratio until each is within a few levels.
`porcelain.py`.

**Clear plastic with a printed label** (the cologne bottle): a double-walled lathe (PET 0.6 mm, IOR 1.57, roughness
0.03, transmission 1), the liquid as its own solid overlapping the inner wall by 0.05 mm (IOR 1.36), a dip tube and
an actuator inside, the cap a 1 mm smoked shell (base 0.10, transmission 0.7), black plastic 0.008 / roughness 0.5.
The label is a cylindrical texture (u = angle with the front at 0.5, v = z / height) rectified from the photo through
the fold, with the cylinder's shading divided out **per column**: the median of a print-free cream band of the label
along each column, smoothed, normalised to its 97th percentile (shading on a cylinder depends on the angle only, so
a coloured band survives where the mug's photo / blurred-photo ratio would flatten it). Transmission (1 - mask) and
roughness (0.03 / 0.55) go in as image maps on the same UVs, never through Mix nodes, so the .glb keeps paper on
clear PET; the inner wall and the bottom take the plain PET material. `prep_pbr.py`, `real.py`.
**The comparison render of a transparent object needs the room behind it**: project a *clean plate* (the object
filled out of the photo) through the camera with Window texture coordinates (per-vertex UVs on a big quad are not
projective) onto a backdrop at the room's real depth (3 m) and a ground plane at the table. With the raw photo the
glass refracted the photo's own collar into the clear band (-61 levels); with the backdrop at 0.6 m the refracted
rays landed on the floor. Use the Standard view transform: AgX dimmed the emission backdrop 30 %. Set the lights by
the numbers (key from the photo's bright side, EXPO 1.0 -> 0.4 here) until the label, cap and collar boxes are
within a few levels; the clear band will stay off, and that is right.

## Faults found only by looking (each fixed)

- **The camera's shift came out with the wrong sign**: the model sat far down and to the right of the frame. With
  `sensor_fit` HORIZONTAL, `shift_x = -(cx - W/2) / W`, `shift_y = (cy - H/2) / W` (`cam.blender_shift()`).
- **Mirroring the back (x -> -x) striped the sides**: the photo's pixels within a few degrees of the silhouette,
  stretched many times, became horizontal ripples from every three-quarter view. Fold the angle instead (step 6);
  a narrow true range (+-45 deg) cost the photo view (the lid's ends took pixels from the wrong height), +-72 kept
  both.
- **A rotationally symmetric lid top** (every angle sampled from the front centre column) caught a dark catch below
  the lid's rim as a black ring, and the dome went white. Keep the fold on tops too.
- **A part hidden by its own mask's cut**: see step 2. The fix is the mask, not the texture.
- **The lid's handles hide their lower edge behind the dome** from the photo's camera (2-4 px): with the parts in
  the axis plane and the dome in front, the hand-solved elevation is a little high. Not fixed (moving the handles
  forward would be wrong elsewhere); say so with the number.
- **Black lid, grey handles, flat viewport** after the material swap: see "Real materials".
- The mug's, in the order met: the table pulled into the mask by a sure box, the handle's upper face left out
  (step 2); the profile iteration diverging, the base 30 px too wide (step 4); staircase patches inside and a white
  band at the back of the rim (step 7); the D ghost and the handle's stripes (step 6); the handle's root a thin
  tail (step 5); the first porcelain render all white ("Real materials").
- The bottle's: the camera solved with pitch and the image centre wandered (D 0.15-0.6 m) and inverted the collar's
  heights (step 3); a fillet built on the wrong side of the top still fitted with its radius at the bound and the
  body 12 mm short (a parameter at a bound is a bug); the clear PET's right edge and the base's outline were not
  where the mask said (step 2); the label's arcs were skewed (step 2); the glass refracted the photo's own bottle
  ("Real materials"); the smoked cap stays speckled in Blender's Material Preview whatever the render method, the
  sample count or the raytracing flag (EEVEE transmission); the Cycles render is clean: not fixed, told the user.

## What this method cannot do (say so)

- The back is the front's mirror: a feature on one side only (a label, a valve, a dent) is either repeated or left
  out (the logo: left out).
- Side parts' depth is a guess; their back faces are their front's mirror.
- An inside is seen only as the far wall's top band through the opening (step 7); the rest is a plain colour. A
  closed neck (a bottle's) is not seen at all: close it or ask.
- The photo's reflections are baked in (until the material swap).
