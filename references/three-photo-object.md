# Three ordinary photos (front, side, rear) of a curved product of a known type

A rotary desk telephone, a toaster, a kettle with a base: a moulded body with rolled edges, a part that rests on it
(a handset), a round printed part (a dial), three phone photos taken from different sides with the object turned
between them, no EXIF. Build on `two-photo-object.md` and `single-photo-object.md`; this file is what a curved body
and a third photo change, and what went wrong on the red rotary phone (`examples/rotary-phone-three-photos/`).

## Scale and cameras

- **Scale from a standard part.** The type's finger wheel is 3 in (76.2 mm) across; fix that and let everything else
  follow. Body 228 x 140 mm and handset 229 mm came out at the type's real size, which is the check.
- **A circle is the anchor** (`solve.py`): the residual of a hand-read rim point is its distance to the projected
  circle (720 samples), not to a matching point. The dial's two circles (wheel, number ring), its ten digits (their
  angles free), the feet and the cradle prongs solved three cameras and the dial's tilt to 2.3-2.5 px.
- **Count the parts before sharing them between photos.** The cradle has four prongs, two in front of the handset
  and two behind: the front photo sees one pair, the rear photo the other. Treated as one pair, the rear camera
  came out 33 cm up looking down 41 deg (the photo is nearly level).
- **A camera solved from silhouettes alone drifts off the printed part** (the dial moved 10 px). Re-solve with both:
  `fitcam.py` = (1 - IoU body) + 0.5 (1 - IoU handset) + 0.02 x dial RMS, from dolly-zoom starts.

## Masks: the first thing to distrust

- **A colour mask cuts every lit face.** Red segmentation + GrabCut left out the handset's top (white window
  reflection), the apron's lit facet and the body behind the dial. What that looked like: a fit that pulled the
  handset's top 4-8 mm down, a "handset that moved between photos" (10 deg of yaw that only one photo wanted), a
  "wrong side camera", and a handset IoU of 0.45-0.77. After adding hand-read polygons for those faces
  (`maskfix.py`) the same model scored 0.87-0.91 in all three photos with no yaw. **Draw the mask's outline over
  the photo and look at it before fitting anything to it**, and again when a number will not move.
- Fill the holes (a clear dial, highlights). Ignore regions for what is not the object or moves (the coiled cord)
  and for parts the mask cannot carry (the clear wheel).
- `cv2.fillPoly` with many polygons in one call is even-odd: front and back faces cancel and the silhouette is a
  hatch. Fill each face with `fillConvexPoly`.

## Fitting shape to silhouettes

- **Fit each part in its own zone.** With one union silhouette the body grew into a box that covered the handset
  (IoU up, model nonsense). Zones per photo: where red can only be the body, where it can only be the handset;
  the IoU is taken inside the zone and the same cut is applied to the model.
- **Never fit what no silhouette shows.** The top's profile is hidden behind the handset in every photo; left free
  it went to the prongs' tops. Measure it by rays instead: the prongs' bases through each camera onto the plane of
  their x (94.6 mm at the front pair, 67 mm at the rear pair) showed the top is a roof: the dial face rising to a
  ridge, then a deck falling 20 deg to the back.
- **Small bounds from a measured start** (Powell, +-3 to +-8 mm). Wide bounds found flat walls leaning 22 deg.
- **A raised part hides what is behind it.** The body's far shoulder showed beyond the dial ring in the model and
  not in the photo: the ring stands 5 mm proud of the face, not 2.5.

## A moulded body as a height field over its plan (`geom.py`)

Rings of the rounded-rectangle plan scaled toward a spine; each vertex's height is the least of the wall profiles
of the faces near it. The wall profile that matched: a drafted straight wall from the base, then **an arc rolling
onto the top surface** (`edge()`), its radius different for the front (33 mm: the apron), the rear (6), the sides
by x. Plan corners: subtract from both face distances the amount that makes them a rounded-box distance in the
corner square, so the two wall functions stay continuous (a blend by corner angle left spikes at the top corners).

## A part that rests on the body (the handset)

- **A silhouette fit is not the shape.** A bar draped over the cups scored best and looked wrong from every other
  angle (two balls under a thin bar, then a hood). What reads like the photos: a slender bar with a flat top and
  two boxy cup bulbs (lathed, axis tilted 10 deg inward) that the bar runs into. Decide between candidates on the
  shaded render next to the photo, not on IoU.
- Read the part's real outline on a 1.7x crop of each photo with the model's outline drawn over it (`ovpart.py`,
  `op.sh`): the cups were 61 mm across, not the 50 guessed from one photo's visible part.
- Render close-ups from angles no photo has before believing any of it.

## Printed and clear parts

- The number ring and the card are rectified through the front camera onto the dial plane (`prep_tex.py`): a round
  ring in the result is the camera check. Digits become a mask (low saturation, bright, within 6.5 mm of each
  digit's solved place) over the measured plastic colour; the card keeps its pixels.
- Marks exist only where a photo shows them: the white dots under the finger holes are under six holes, not ten.
- Embossed lettering: the photo patch's high-pass as a normal map on a raised plate (bump nodes do not export).
- **Write textures outside Blender** (`mktex.py`, OpenCV) and load them: `images.new` + `foreach_set` + `save()`
  wrote black files.
- Clear plastic over a printed plate: `visible_shadow = False` on the clear parts, or the plate under them is black
  and the wheel reads as chrome. Thick, with a one-segment bevel on the holes, so it catches light like the photo.

## Light

- Check what each glossy face mirrors: the view ray reflected off the tilted dial pointed at the ceiling, so a
  ceiling panel washed the dial white while the photo's dial is dark. One large window opposite the camera (it is
  in the photos' backgrounds), a weak fill, a dim world.
- The object was turned between the photos: the window is opposite the camera in each, so the rig turns per shot.
- One exposure value per photo (the phone's auto exposure), reported, not hidden.

## Numbers reached, and what stayed open

Silhouette IoU, body: 0.94 front, 0.97 rear, 0.89 side; handset zone: 0.91, 0.87, 0.90. Mean colour photo -> render:
115/69/75 -> 104/57/60 (front), 99/42/46 -> 90/46/47 (rear), 76/29/34 -> 76/36/38 (side). Open: the handset's end
chamfer is rounder than the photo's, the room's reflections are approximated, the cord's path is generic, the
underside and the cap faces are in no photo.
