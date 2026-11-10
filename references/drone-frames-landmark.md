# A landmark from several drone frames (a building on an island, seen all round from the air)

Worked example: `examples/maiden-tower-drone-frames/` (the Maiden's Tower in Istanbul: a square stone shaft with an
octagonal lantern, a lead dome and a flagpole, a crenellated fort, a single-storey annex with a tiled roof, a terrace
with a parapet and benches, a quay, armour-stone rocks and a beacon; six screenshots of a drone video taken all
round it, 1290-1586 px wide, no EXIF). Built on `multi-photo-room.md` (joint solve from hand-read points) and
`single-photo-vehicle.md` (bake, project, light divided out); this file is what an outdoor landmark seen from the
air changes, and what went wrong.

## Cameras

- **Screenshots of a video are not one camera.** Each frame was cropped and scaled differently by the screenshot
  tool (six different sizes), so each needs its own focal length and principal point. One shared focal was the
  first assumption and it was wrong; per-frame focals came out 1554-1716 px.
- **Joint solve from hand-read points** (`solve.py`): the flagpole's gilded ball and its base, the fort's corners
  (top and foot), the shaft's vertical edges as image lines, the beacon's top, three wall openings. Free parameters:
  the fort's length and width, the wall height, the pole's heights, a batter at the foot. RMS 4 px.
- **Then refine each camera on the photo's edges with the points held** (`edgefit2.py`): sample the model's sharp
  3D edges (terrace and quay outlines, the fort's foot, the shaft's corners, the balcony octagon, the annex, the pole),
  project, and minimise the distance transform of the photo's Canny edges (soft-L1, capped at 15 px), with the
  hand-read points as residuals at 1.5 px. Without the points the edge fit pulled the cameras 9-17 px off them: it was
  compensating errors in the geometry. With them the median edge distance fell 1-2 px and the points stayed at
  2.6-4.6 px. Reject a camera whose points get worse (one did: 0.7 -> 11.5 px).
- **The base is where the cameras are weakest**: every hand-read point was at terrace level or above. Points on the
  waterline (the quay's foot, the rocks' edge) are what would pin it; the waterline's position disagreed between
  frames by 20-55 px before the edge refinement.

## Scale

- **Read it from a standard part, never from people.** Two doors (the fort's, the annex's) measured 2.0 model units
  by intersecting their top and bottom pixels' rays with their wall planes; doors are ~2.1 m, so the scale is 1.05.
  The first delivery used 1.3, guessed from people on the terrace (their shadows and the foreshortening from above
  make them unreadable): the model was 24 % too big, and it was reported as a measurement. Check the result against
  a published figure (the tower's ~23 m to the upper gallery: 24 m here).

## Silhouettes and masks over water

- **A colour threshold for "sea" is useless**: blue-grey stone counts as sea, the sun's glint as land. IoU on it was
  0.52-0.83 for a model that fitted well.
- **GrabCut seeded from the model's silhouette** (`gcmask.py`: definite foreground the model eroded 25 px,
  probable foreground the model, probable background a 61 px dilation, background beyond) gave 0.87-0.91. It still
  takes the shadowed water along a quay wall as land: a "photo extends lower" band there is the mask, not the model.
  **Read the waterline on a grid crop before moving geometry to a mask.**
- **The index render must hold out the sea** (a Holdout material on the water plane, not `hide_render`): with the sea
  hidden, everything below the waterline counted as model silhouette and "the model is too big" was the
  under-water skirt.
- **The waterline from the masks themselves** (`footprint.py`): back-project every frame's mask onto horizontal
  planes and intersect (a visual hull per height). The extents are widest at the waterline (here z = -2.0 m below the
  terrace); the outline at that height is the rocks' outer edge. The morphological opening and polygon
  simplification pull it in: grow it ~1 m (chosen by IoU: 0.5 / 1.0 / 1.5 m -> 0.895 / 0.898 / 0.894).
- Where the edge is a **quay wall**, it drops vertically into the water: no rock slope in front of it
  (distance to the quay polygon < 0.5 m -> vertical).

## Shape details that cost a round each

- **Separate quads have no inside.** The lantern room's walls were built quad by quad around window recesses;
  `recalc_face_normals` cannot orient disconnected faces, half pointed inward, and the projection called them
  unseen (37 % seen; the texture was invented by the hole filling). Merge the vertices, then orient every wall face
  away from the axis. Check each part's "seen %" after projecting.
- **Armour stones** are icospheres (subdivision 1, vertices jittered -24..+20 %, squashed, flat-shaded) scattered on
  the skirt at the size read on the photo (0.6-0.9 m), textured from a tile quilted out of the photo's rock band.
  Subdivision 2 with smooth shading read as pebbles.
- **A painted band at a constant height** (the beacon's red stripe) projected from several frames breaks at the
  corners. Rebuild it: the paint colours measured on the projection, the band's limits read as fractions of the
  trunk on two frames.
- **What hides the foot**: the beacon's trunk looked as if it reached the water on one crop; the rocks hide it from
  -0.3 m. A model with its foot lower stood 25 % too tall.
- Crop by the **part's bounding box in the index render** (`pcrop.py`), not by guessed coordinates: guessed crops
  missed the part twice.

## Light and materials

- **Sun**: from a shadow's length on a horizontal surface (the fort's shadow on the terrace: 4.1-5.1 m from a 5.3 m
  wall -> 47 deg). The glint on rough water is spread over a third of the frame; its centre gave 15 deg, wrong.
- **The sky that lights is not uniform**: a uniform sky over-lit every upward-facing shaded surface (the dome's shade
  side twice the photo). A zenith-to-horizon gradient (dark blue overhead, hazy at the horizon) fixed it; the
  colour shown to the camera stays separate.
- **Albedo divided by diffuse irradiance, then rendered with a specular layer, is too bright on dark surfaces**: the
  photo's pixels already hold the sky's reflection. Keep the specular low (IOR level 0.12) on photo-derived albedo.
- **A metallic dome is the wrong fix** for a lead roof that is dark in back-lit frames and light grey in front-lit
  ones: it matched the back-lit frames (3-5/255) and broke the front-lit ones (52-89/255). Round geometry, a matte
  material and the gradient sky matched both.
- **Faces the photos clipped to white** (sunlit limestone) have no texture to project. Take the stone's pattern from
  the same stone in shade (a clean band of the fort's shaded wall, divided by its own blur so only the pattern is
  left), tile it in world space on the wall plane at the photo's resolution, at the albedo measured on unclipped
  sunlit stone.
- **One frame's tone curve is not the material**: in the back-lit frame the same terrace in shade was 24-59 where
  another frame had 70-100, with the lit parts equal. That is the camera. One exposure per frame from the co-seen
  texels, the rest reported, not "fixed" in the albedo.

## Measuring

- `stats.py`: per frame and per part group, the mean colour difference and the 5th/95th lightness percentiles of the
  photo and the render, through the index render. **Put every new part in its group**: the boulders were left out of
  "rocks" and a texture change "did nothing".
- Novel views (`novel.py`: from the quay, low from the west, close to the dome, from above, at the annex's porch)
  showed what the photo-camera views hid: the crumpled rock skirt, the white clipped walls, the smooth dome, the
  blurred annex windows.

## Numbers reached, and what stayed open

Silhouette IoU (GrabCut masks, sea held out) 0.887 over six frames; mean colour difference 10/255 (2-14 per part
in five frames, 15-28 in the back-lit one). Open: the annex's windows are texture, not frames and recesses; the quay
is darker than the photo in one frame; the annex roof does not show between the merlons where it should; the foam
along the waterline is not modelled; the annex's quay side and the fort's courtyard are in no frame.

## Tooling notes

- `uv run` waited on the cache lock held by another project's long job; the scripts here call a cached
  environment's python directly (`pyx.env`) when that happens.
- `run2.sh` is the whole chain (geometry -> bake -> project -> irradiance x2 -> albedo -> extras -> renders); a shape
  change needs `geoloop.sh` (geometry -> index renders -> IoU) first, three minutes against ten.
