# One photo of a turned object (a pot, a bottle, a vase, a lamp, a cup)

A body of revolution needs only its profile, and one side-on photo shows the profile twice, as the silhouette's left
and right edges. What it does not show is everything behind the silhouette and every side handle's depth. So:
**solve the camera from the ellipses of the object's own circles, lathe the profile measured through that camera,
build side parts (handles, spouts, knobs) as rounded slabs of their photo outlines, and wrap the photo round the
axis with the angle folded into the part the photo sees well.**

Worked example: a stainless pressure cooker, one 554 x 554 product photo, no size given. Scripts and the commands in
order in `examples/pressure-cooker-revolved/`. Result from the photo's camera: silhouette IoU 0.98, mean colour
difference 8.3/255 over the model (median 1.0, body 1.5); from other views a clean pot with the photo's own
reflection bands all round. A second version swaps the photo's light for real materials (polished steel, plastic).
About an hour, most of it in the four faults below that only looking found.

## Steps

1. **Size.** Ask, or assume from the product (a 10 L pot ~27 cm across) and say so. Everything else is in
   proportion, so a wrong guess scales the model, nothing more.
2. **Masks.** The silhouette: flood fill of the background from a corner (white, low saturation), so bright
   highlights inside the object stay in it. Each side part: dark pixels inside a box you set from a grid over the
   photo (`examples/laptop-single-photo/grid.py`), so the object's own dark reflections (a steel pot's edges are dark
   strips) do not join the handle. Add a part's light brackets (metal) by box. **Look at every mask over the photo**
   (`masks.py` writes `masks_vis.png`): a box edge cut a tab's bottom 7 px off, and a thin dark line (the lid's edge)
   joined the tab's mask; both showed up later as smears on the lid. Open thin lines away, keep the biggest piece.
3. **The camera from two circles.** A level camera at (D, 0, Hc), focal F px, principal point (cx, cy) (a level
   camera keeps the verticals vertical; the crop's offset is the principal point). Under perspective a horizontal
   circle of radius r at height z shows as an ellipse whose front point lies below its side points by about
   `F (Hc - z) r / (D (D - r))` px. Read that drop on two circles at different heights (the base: 23 px; the lid's
   flange: 8 px), and the scale at the axis k = F/D from one known radius: two equations give D and Hc
   (1.55 m and 0.295 m; F = 1550 px, a long product lens). cx is the silhouette's centre column; cy follows from
   the base's side rows. Write it in `cam.py` with `proj(x, y, z)` and `unproj0(u, v)` (the plane of the axis).
   Two ellipses read by eye are worth a few px; a 2-4 px band where parts meet (below) is what that costs.
4. **The profile.** For each clean row (no handle, no base ring), the half width hw gives r = hw (D - x_t) / F with
   x_t = r^2 / D (the silhouette is where the ray grazes the surface, a little in front of the axis; iterate), and z
   from the row at x_t. Fit what is simple (the cooker's wall was linear: r = 0.1196 + 0.0775 z, residual 1.4 mm).
   Read the short features (base corner, rim roll, lid flange, dome) off zoomed grids, each checked by its front
   point's row. Lathe it (160 segments) as separate objects for separate parts (pot, lid).
5. **Side parts as rounded slabs.** From each part's mask: a half-thickness h(u, v) that rises over r (8 mm) from
   the outline as a quarter circle, the solid |x| <= h, meshed by marching cubes at 2x the photo's resolution, the
   vertices placed with `unproj0` (the parts sit in the plane of the axis). The thickness is a guess (the photo is
   side-on): 30-40 mm for handles. Dense (150k vertices): decimate to ~12 % before saving.
6. **UVs through the camera, angle folded.** Each vertex's UV is `proj` of a point on the same circle at a folded
   angle: within +-A (72 deg) the vertex's own angle (the photo's pixels as they are); beyond, the back is the mirror
   of that part, stretched to reach 0 (the photo's centre) at 180 deg, so the seam closes. Outside +-A use a plate
   with the logo removed (each column interpolated across it), so the logo is not repeated, mirrored, on the back.
   Handles: faces towards +-X take the photo (the back mirrored, |x|), the rest a plastic material. The undersides
   (normal down) a flat material. Body texture: the photo with the handles inpainted where they cross the body, the
   margin outside the silhouette filled outward from the nearest object pixel.
7. **Compare from the photo's camera** (emission, Standard, film transparent): IoU above the floor's shadow, colour
   difference over the model and per region (`cmp.py`). Then look from three-quarters, above and close to a handle.
8. **Deliver** the tidy .blend (Material Preview, framed, model and studio in collections) and a .glb; open it and
   look (`scripts/shot_ui.py`).

## Real materials, when asked

The photo's reflections are baked in: the pot shows the photographer's studio from every side and does not react to
a scene. Offer the swap (it moves away from the photo's pixels, so ask): polished stainless (metallic 1, roughness
0.08), the lid satin (0.16), the base matte (0.3), handles black plastic (roughness 0.5, specular 0.3) with the
photo's details on their faces, darkened. Keep the printed logo: the clean back plate minus the photo is its mask;
upsample 4x, smooth, and bake it into a base colour and a roughness map (dark satin print). Light it as a product
shot: a bright world and black cards that only reflections see (`visible_camera` off), which draw the dark vertical
bands that read as steel. In the viewport use a built-in HDRI (interior.exr) and hide the cards. `steel.py`.

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

## What this method cannot do (say so)

- The back is the front's mirror: a feature on one side only (a label, a valve, a dent) is either repeated or left
  out (the logo: left out).
- Side parts' depth is a guess; their back faces are their front's mirror.
- Inside (a pot's interior, a bottle's neck) is not seen; close it or ask.
- The photo's reflections are baked in (until the material swap).
