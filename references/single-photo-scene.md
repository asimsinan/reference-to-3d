# One product photo of a furniture set with things on it, and its room

Worked example: a dining set from one 1000 x 1000 product photo (a flip-top table, a bench, two stools; two cups on
coasters, a wooden plate with two muffins and a napkin, a pink sphere candle, a pillar candle, a small spiky plant in
a pot; a room with a sheer-curtained window, a brown curtain, laminate floor). Scripts in
`examples/dining-set-single-photo/`. Read "The bar: identical" in SKILL.md first: this case is where the user had to
state it.

## Geometry

1. **Edges with colour-gradient peaks, not brightness steps.** Signed brightness steps found the wrong edge or the
   window's border; the peak of the Lab gradient magnitude across a window placed from a gradient-image grid
   (`gradgrid.py`) gave 0.1 px line fits (`edges.py` with a JSON of edge specs). A window whose peak sits on its
   border is a misplaced window, not an edge.
2. **Camera: level, principal point free.** Product photos are often perspective-corrected or cropped: the legs were
   vertical in the image while the top was seen from 0.5 m above. A free-pitch solve fitted 0.19 px but needed
   strongly splayed legs; the level solve (pitch fixed, cy free; it came out at row 86 of 1000) fitted 0.32 px with
   straight legs and a vertical curtain. Choose by what the rest of the photo says, not by the last 0.1 px.
   Unknowns: pose, f, cy, the top's L and W, its thickness, the leg feet rectangle (bx, by); data: the top's edge
   lines (both faces of the band), three leg feet (front-most point = centre + radius toward the camera). One size
   assumed (table height 0.75 m); say so.
3. **Parts under the top**: aprons from their bottom edge lines (one line gives only offset+height together: tie them
   by a second line or by the legs); the corner radius by scoring the gradient along projected arcs.
4. **Seats: fit the cushion's silhouette, not lines.** Lines on a puffy cushion and leg tops cut off by the tray's edge
   gave a 20 cm tray for a 35 cm seat. A GrabCut mask per cushion (seeded by a colour threshold; cut neighbours apart
   by a measured edge line) and a rounded box (plan a x b, corner radius, rim height, top height, rounded top edge),
   fitted by least squares on contour-to-hull distances, gave 3 px. A box's silhouette from one view fixes its centre,
   yaw, plan and both heights (6 hexagon vertices, 7 unknowns with the yaw). The second stool and the bench share the
   section; the bench's length from its feet when its far end is hidden.
5. **Splayed legs**: each leg's image axis (centre of its two edges per row) plus its foot; leg tops symmetric in the
   seat frame with a small frame offset. Put every visible foot exactly on its measured floor point.
6. **Objects on the top: placement by base pixel, then relations.** At a low viewing angle 1 px on the top is ~1 cm
   of depth: a cup and its coaster placed separately ended 5 cm apart, the cup on the coaster's rim; the user saw it
   at once. Place the sharper of the two (the cup's base edge), then enforce the physical relation (the cup stands on
   the coaster's disc; resize the coaster to cover the photo's outline) and check both outlines (`idov.py`).
7. **Every asymmetric part from its evidence**: a cup's handle was put "to the image's left" by default; the photo
   showed it overlapping the body and sticking out 1 cm, i.e. turned ~60 deg toward the camera, attached lower.
   Read protrusion, overlap and attachment heights on a 6x crop before building it.
8. **Small objects' shapes from photo-camera crops**: render the photo's camera with a border at 4x (`--border`) and
   put it under the photo crop. Muffins were mushroom caps on tall paper cups; the photo's are squat with a lumpy
   dome barely overhanging a fluted base hidden in a deep bowl. The plant was a grass tuft, then a ball on a visible
   stem; the photo's is a dense dome of thick needles sitting on the pot. The plate was a flat maroon platter; the
   photo's is a deep honey-brown bowl with a thick rounded rim. Each took one crop to see.

## Materials from the photo (not procedural, not averages)

- **Exemplars**: rectify each surface the photo shows most frontally through the solved camera (the table's end
  apron, the long apron's near half, the tray fronts at ~1.65 mm per texel; the legs unrolled over the part facing
  the camera; the cushions' lit tops in image space, isotropic weave). Divide the light out (divide by a wide blur of
  luminance); match each exemplar's mean and spread to the best one; **colour order**: OpenCV is BGR, a target given
  in RGB turned every texture blue.
- **Leave out what carries no information**: the tabletop seen at a grazing angle under sheen had no grain left; as
  an exemplar it won every quilting match and flattened the result. Mask objects, seams, slots, legs crossing.
- **Growing**: toroidal image quilting with min-error cuts works for isotropic textures (linen, legs along the grain).
  Small strips of strongly figured wood quilted into visible repeating bands; for those, generate the flow (bands at
  the spacing measured on the exemplar, ~6.5 mm; waviness; cathedral loops) and **colour it by the exemplar's
  luminance quantiles** (the palette is the photo's, mean identical by construction), then compare at the photo's
  resolution next to the exemplar and fix spacing, waviness, mottling and line width until they read the same.
- **Every object its own palette**: the plate and coasters from their own pixels (rim, wall, inside, muffins masked);
  a palette from the shadowed front band alone made the plate maroon.
- **Gloss from the photo's highlights**: the sphere candle showed a soft specular highlight (satin wax, roughness
  ~0.22, coat 0.6); the lacquered top a sheen of the window; the laminate floor almost none (a glossy floor mirrored
  the sheer as bright streaks and washed the whole frame).
- **Calibrate each material's albedo** by the ratio photo/render (linear light) over its regions, damped (^0.7),
  bounded, a few rounds (`albedo_cal.py`, cumulative `gains.json`, calibrated copies `*_cal.png`); white materials
  floored at 0.7 (a white cup in shade must stay white). A tiny box at an edge oscillates: use boxes well inside.

## The room and the light

- **Model the surroundings the photo shows**: floor (plank direction and width measured on the rectified floor:
  Hough on thin dark lines with the legs masked, the angle checked by projecting candidate directions back into the
  image), walls from their floor junction lines (squared to 90 deg), curtains at their measured positions along the
  window wall, the sheer as a pleated emissive panel. Without them the materials sat in a studio world and read flat.
  Check every showcase camera is inside the room (two views rendered the back of a wall).
- **Fit the light to contrast as well as colour.** Fitting exposure and light energies to region mean colours only
  chose a strong ambient light: averages matched (13/255) while the furniture's lightness spread was 25 against the
  photo's 49 and its darkest 5 % at 108 against 65: "soluk". The objective that worked: per-region mean colour +
  per-region lightness spread + the furniture's 5th/50th/95th percentiles and spread (`tune2.py`), the tone curve
  Standard + Medium High Contrast, and the photographer's lights where the shading says they were: the window behind
  left (strong), a softbox above and in front of the camera (tops bright, fronts in shade), little ambient. Measure
  with `cstats.py` (saturation, lightness, spread, ends; whole frame, furniture, per piece) and map where the render
  is brighter or darker than the photo (red/blue lightness-difference image): it showed the vertical faces toward the
  camera too bright, i.e. a fill at camera height.

## What the user rejected (in order)

1. Procedural oak and linen, colours matched on 16 region averages: "malzemesini birebir niye yapamadın".
2. Cups standing behind their coasters: "bardaklar altlığın üstünde referansta".
3. Sphere matte, muffins and plant the wrong shape: "küre parlak, muffin ve bitkinin şekli farklı".
4. Plate wrong, left cup's handle the wrong way: "muffin tabağı da uyumsuz. Soldaki bardağın kulpunun konumu da yanlış".
5. The whole render paler than the photo: "bizimki daha mı soluk duruyor" (contrast half the photo's).
6. Then the rule itself: materials from the photo only, and the comparison loop until no difference remains.
All six were findable by the side-by-side crops and the contrast numbers before delivery.
