# One photo of an object whose real size is known (a laptop, a phone, a chair, an appliance)

A single photo of a real product is not a turnaround sheet: there are no silhouettes from the front, side and top to
fit a hull to. But a manufactured product has known dimensions (the maker publishes them) and is made of simple
parts (slabs, rounded boxes, cylinders) joined at known angles. Then: **solve the photo's camera from the product's
known geometry, build the product from its real dimensions, and take each surface the photo shows from the photo
itself, rectified through that camera.** Seen from the solved camera the model gives the photo back; seen from
anywhere else it is a real 3D object with the photo's surfaces on it.

Worked example: a 14-inch MacBook Pro on a table, one phone photo (2000 x 1500), open at an unknown angle. Scripts
in `examples/laptop-single-photo/`. Result from the photo's camera: mean colour difference 3.7/255 over the model
(median 1.0), screen 4.2, keyboard 3.5, palm rest 0.3, front edge 16.4 (body material on purpose, see the corner
fault below); from other views a clean slab model with raised keys and ports. The first version took under an
hour; five rounds of the user's close looks (a cluttered .blend, the lid's top, a corner, a tilted screen) found
what the numbers did not, and each is written below.

## Steps

1. **Real dimensions first.** Look up the product's size (MacBook Pro 14: 312.6 x 221.2 x 15.5 mm; base ~9.5 mm,
   lid ~6 mm). Work in millimetres while measuring, metres in Blender.
2. **Mark a few unmistakable image points.** A labelled grid over the photo (`grid.py`: crop, scale, lines every
   10-100 px, view at 2-4x) is for finding them; their positions come from `edge_profile.py`. Rounded corners have
   no point: measure the straight edges either side and intersect them. The laptop used 10 points: the deck's two
   front corners, the lid's two top corners, the lid's two bottom corners where it meets the deck, and **the
   display's four corners**.
   - **Measure edges with profiles, not by eye.** The lid's top-left corner read by eye was 19 px too high; the
     screen came out tilted (the user: "soldan sağa doğru kayma var") and the menu bar slanted. Take the steepest
     brightness step along a few columns (top edge) or rows (side edges) where the background is bright, fit a line
     per edge, and intersect them (`edge_profile.py`; residuals under 0.5 px on the laptop's lid).
   - **A printed or lit rectangle of known size on the object is the best anchor**: the display's active area
     (MacBook Pro 14: 302.5 x 196.5 mm, centred across the lid) has sharp corners and a known shape. Add the lid's
     length and the display's offset from the lid's top as unknowns. With it the solve went from 6.1 px RMS (6
     points, one misread) to 2.4 px (10 points), lid length 222.7 mm, display top 5.9 mm below the lid's top.
3. **Solve the camera with the unknown articulations as extra unknowns** (`solve.py`, scipy `least_squares`): pose
   (rotation vector + translation), focal length (principal point at the image centre), and every free joint (the
   lid's opening angle, the lid's length, the display's offset). 10 points = 20 equations for 10 unknowns. Start from several guesses (pitch 20/35/50 deg,
   distance 400/550/700 mm) and keep the best. Expect 2-3 px RMS (the laptop: 2.4 px; f = 2011 px; lid 108 deg;
   camera 41 cm in front, 23 cm up). Weight the sharpest points up (display corners 1.5) and the vaguest down (where
   the lid disappears into the hinge 0.5).
   - **Handedness.** OpenCV's camera: x right, y down, z forward. Looking at the object's front, the object's left
     (+Y) is on the image's **right**. The initial rotation (rows = camera axes in object coordinates) for a level
     camera looking at the front is `[[0,1,0],[0,0,-1],[-1,0,0]]`; `[[0,-1,0],...]` is a reflection and scipy refuses
     it ("non-positive determinant"). Label points by the object's own left and right, not the image's.
4. **Check the solve by drawing the model's edges over the photo** (`overlay.py`): deck outline, front edge's bottom,
   lid's two faces. The base's bottom edge (not used in the solve) landing on the photo's is the honest test.
5. **Rectify each flat surface the photo shows into its own texture** (`rectify.py`): for every texel, its 3D point
   on the surface, projected by the solved camera, `cv2.remap` from the photo (cubic, border replicate). 6 texels/mm
   was enough (the photo has ~5.5 px/mm at the nearest edge). The laptop: deck top (keyboard, trackpad), the lid's
   inner face (screen and bezel); not the base's front edge (see the corner fault below). Look at each: straight key rows and a rectangular trackpad
   mean the camera is right. Fill what the photo cannot show (the deck behind the lid: copy the first visible row
   back, its limit the lid's *visible* bottom edge as used in the solve, not the hinge axis: with the axis the fill
   crept over the function keys after a re-solve; the strip under the photo's table edge: copy a clean row over it).
   **Check that straight lines of the object come out straight** in each rectified texture (a menu bar, key rows):
   a slant means the camera is wrong, and painting or stretching the texture only hides it.
6. **Build the object from simple parts in its real dimensions** (`build.py`): rounded-rectangle slabs (bmesh cube,
   bevel the vertical edges for the plan radius, then small bevels on the top and bottom loops), joints as object
   rotations about the real hinge axis, small parts (ports, feet, a hinge barrel) as primitives. UVs per face from the
   face's normal: the faces the photo shows get their rectified texture's planar UV, the rest a measured flat material
   (sample the photo's body colour in a shadowed area: space black was ~50/255).
7. **Raised details** (keys, buttons, a grille): find their outlines in the rectified texture and give them depth.
   - A high-pass of the texture (`gray - GaussianBlur(sigma 25)`) shows the caps clearly; connected components did
     not separate them (labels and glow join caps), and per-row gap profiles were noisy. What worked: the product's
     **known layout** (key widths in key units per row: the ISO Turkish-Q MacBook rows each add to 14.5 u) fitted by
     four numbers (left edge, right edge, first gap, row pitch) and drawn over the texture to check
     (`keys_layout.py`). Search the four numbers instead of guessing them (`keys_fit.py`: caps' high-pass brightness
   inside each rectangle minus the gap strips just above and below it); re-fit after any change to the camera,
   since the rectified deck moves with it. Special shapes: ISO Return as two boxes (upper wide, lower narrow, bridging the gap), half
     height arrows.
   - Each raised part's top takes the texture **where the photo camera's ray through that point meets the base
     surface**, not straight below it: the labels then stay where the photo has them (keyboard difference 3.4 with
     0.75 mm keys instead of a visible shift). Sides get a dark material.
8. **Compare from the solved camera** (`cmp.py`): emission only, Standard view transform, film transparent; mean and
   median difference over the model's pixels, per region boxes (screen, keyboard, palm rest, front edge), and a
   2 x 2 sheet (photo | composite / edges over photo | difference x3). Then look at close-ups from other angles; each
   found a fault the photo view could not (below).
9. **Final look**: lit materials for viewing from other angles (photo texture as base colour plus some emission, the
   screen as emission with a weak, rough specular), modest lights, a mid-grey floor. Deliver `.blend` (packed) and
   `.glb`, plus the renders and the comparison sheet.
   Before saving the .blend, tidy what it opens to (`build.py`'s `tidy_scene`): delete the render shots' cameras,
   the model under one parent in its own collection, lights/floor/photo camera in a `studio` collection, the floor
   scaled to the object, the camera's display size small, every 3D view framed on the model in Material Preview
   (Rendered does not survive saving), extras overlay off. Then open it and look
   (`scripts/shot_ui.py`): the first version opened as wires round a tiny grey box.

## Faults found only by looking (each fixed)

- **A part placed from the solve's convenient point pokes out.** The hinge barrel at the hinge axis showed as a grey
  band under the screen from the photo's camera; it belongs inside the base's back edge, just under the deck.
- **Lights strong enough for a showroom blew the screen to white**: a glossy screen mirrors area lights. Key light
  energy 14 W (not 60), screen roughness 0.3 and specular 0.12, world 0.25, floor mid-grey (not near white).
- **A box built from texture rows with the rows' direction reversed is inside out**: row 0 is the back
  (x = -D/2), so `x = -D/2 + row/H * D`; computing the box's ends from (bottom row, top row) gave xa > xb, a
  negative-size cube, flipped normals, and bevels in the wrong places. Every cap's top went to the side material
  (keyboard difference 15.3). Check the material counts and a few normals in a short debug script when a whole
  class of faces renders the wrong material.
- **The wall behind the lid showed as a grey band along the lid's top** (the user saw it in a glTF viewer): the solve
  put the model's lid top up to 19 texels (3 mm) above the photo's at the left, 0 at the right, so the screen
  texture's top rows were the wall, and its bevel and corners too. Fix in `rectify.py`: find the photo's edge per
  column (first texel darker than 25: the rim, also where the wall behind is dark), fit a line, paint above it the
  rim's colour sampled just under it; the same from the left and right edges. Do not stretch the columns to move the
  edge up: that moved the screen's content off the photo (screen difference 4.2 -> 14.2). **Check every rectified
  texture's border** (top, sides, corners) for whatever was behind the object before delivering.
  The root cause was the lid corner misread by eye (step 2); after the re-solve the band was ~1 mm and even, and
  the painting is only a safety net.
- **A photo strip on one wall of a rounded box shows a step at the corners** (the user: "köşe niye böyle"): the
  front edge took the photo's strip (brownish, the wooden table reflected in it), the sides the body material
  (neutral black), and the two met halfway round each rounded corner. Narrow walls that the photo shows only as a
  thin, reflective strip get the body material all round; the photo-view difference on that strip rose 1.3 -> 15.0,
  the corners became continuous. Look at every corner where two materials meet before delivering.
- **The photo's table shows under the front edge** in the rectified strip (the bevelled bottom edge): replace the
  texture's bottom rows with a clean row.

## What this method cannot do (say so)

- Surfaces the photo does not show (the lid's back, the bottom, the sides) are a measured flat colour, not the
  object's; a logo there is left out unless the user asks.
- The photo's lighting (the screen's glow on the keys, reflections on the screen) is baked in.
- The texture's sharpness is the photo's: close-ups of labels are soft.
- Cables and things lying on the object are not the object: leave them out, and say so.
