# Two ordinary photos of a product (front and side), its size unknown

A desk phone, a printer, a kettle, a radio: a boxy product with simple parts, two phone photos from different sides,
no published dimensions, no EXIF. Build on `single-photo-object.md` (its camera solve, edge measuring and rectified
textures all apply); this file is what the second photo changes and what the user caught on the desk phone
(`examples/desk-phone-two-photos/`).

## Why one photo is not enough

From one photo, a sloped top's angle, the camera's pitch and the body's height trade off against each other: every
slope from 0 to 18 deg fitted the front photo's keys and edges within 0.6 px. A 10 deg prior gave a 16 mm front and a
47 mm back; the side photo showed 23 and 31 mm. When a part's height or slope cannot be read from the photo you have,
say so and ask for a second photo from the side, low; do not ship the prior as if measured.

## The joint solve (`jsolve.py`)

- **One body, two cameras.** Unknowns: both poses, the body's depth, front and back heights, the band's two heights
  and thickness, the keypad's origin, pitch and key depth, and every feature seen in both photos. Fix the width (the
  scale) and the front camera's focal length (a phone's ~25 mm equivalent); the side camera's focal length barely
  mattered (1000-1800 px changed the body by under 2 mm).
- **Observations as lines, not corners.** Rounded corners have no point. Fit image lines to brightness steps along
  scan columns or rows (`measure.py`, `smeasure.py`) and make the residual each model segment's distance to its line.
  Scans catch the cord, a table seam, the coil: keep only samples with small residuals, read corners on a grid.
- **Pin the second camera with features both photos see.** A flat side wall gives lines that slide along
  themselves: the side camera came out 10 mm off the table, looking up. Two buttons visible in both photos (their
  centres as 3D unknowns) brought it to 52 mm and a believable pitch.
- **Each key gives four numbers**: its centre, the top face's back edge, the front edge, the front face's bottom
  (`keys_meas.py`). Their spacing fixes the key height and the top's slope locally.
- **Parts that moved between the shots disagree.** The handset sat ~10 mm higher in one photo than the other while
  the body fit both. Fit such a part to each photo alone and both together (`hsfit.py`); report the disagreement and
  take the joint fit, not either photo's.
- **Speed.** The whole solve is ~2 s. When it suddenly took minutes, unused parameters were pinned by bounds 1e-6
  apart (scipy's trf crawls at a bound); take them out of the parameter vector instead.

## Shape: read the reference for every part, never fill in from "what phones look like"

Each of these was a user correction:
- **Straight in plan.** A handset given a waist (narrower grip) looked wrong from above; the photo from the front
  shows parallel sides. Width from the photo, not from a template.
- **The top's arc from the side photo.** A straight top between two heights read as a box. The side photo's top
  edge, mapped onto the handset's flank plane through cam2 and fitted with a quadratic, gave the real curve (flat at
  the back, dipping to the front); add the crown across (3 mm) that the side photo's highlight shows.
- **A parting line is a ribbon, not a groove.** A groove cut into a lofted section broke at every change of section
  (the arch's walls) and rendered 2-3 px thick. A separate closed ribbon 0.5 mm tall, 0.12 mm outside the surface,
  following top(x) minus a constant, is straight and even from every side.
- **Ends sit on the floor.** Rounding a lofted part's ends by scaling the whole section lifts the bottom too; the
  handset floated with a gap below. Round only the top (`h * (0.25 + 0.75 k)`, base kept). Arch walls: a 3 mm blend,
  not 8: the reference's are near vertical.
- **Steps the photo shows.** The base's lower wall stepped 2 mm in under the band; a flush wall was wrong, and an
  inward-pulled band (the first attempt) tilted the lower wall instead. Move every vertex below the band's top edge
  inward by the step.
- **Features exist only where a photo shows them.** A cord socket was put on the handset's end because desk phones
  "have one there"; the side photo shows the cord leaving the base low on its left wall. Locate such a feature on the
  photo that shows it, through that photo's camera (`measure_side_parts.py`: the cord hole's pixel onto the wall
  plane). If no photo shows it, leave it out and say so.

## Textures from two photos

- **One photo per face, chosen by facing and by what is in front.** The side photo only on faces whose normal points
  to its side (`n.y < -0.5` here): on the top it carried the wall and the table behind, as white blotches.
- **Gain-match the second photo** to the first on the same surface (`side_match.jpg`: the side photo was ~15 %
  brighter, window light), and still expect a seam where they meet.
- **Mask cords and coils** in each photo before projecting (pixel boxes and a polyline buffer); a cord carried onto
  the body reads as a stain.

## Real materials (delivered by default)

- **De-light by dividing by a wide blur of the bright pixels only** (`delight.py`: weight out pixels darker than
  0.3, sigma 35, then scale to the plastic's albedo, half the photo's mottling kept). A plain blur lets the black
  keys darken their surroundings' mean and leaves halos.
- **Shadows survive de-lighting.** Each key's own shadow stayed in the albedo as a black smudge beside it; the
  handset's shadow on the body's rim stayed as a grey patch the user saw as a dent; on the curved handset photo
  faces next to plain faces made a patchwork. Where the photo carries no printing, use the plain material: the keys'
  surroundings (dark pixels in the keypad box set to the plastic), the handset, the whole handset side of the body.
  Keep the photo only where something is printed (logo, labels, a grille).
- **Keys**: a white-on-black label mask from the photo's luminance on the tops, black plastic on the sides.
- **Exposure by measuring.** Render the real-material model from the photo's camera in Cycles and compare boxes
  (top, front face, handset) with the photo: the first render was 1.6-2x too bright and clipped; -1.35 EV brought the
  front face within 1 %, the top within 20 % (the studio's key light is above).

## Look where the user will look

The user found every fault above in a close orbit of the .blend, not in the comparison numbers (6.7/255 from the
front camera throughout). Before delivering, render close-ups of: the side at eye level (parting lines, steps, gaps
under parts), the corner where two parts meet (the pocket's rim), the side the second photo shows, and the top
straight down (plan straightness).
