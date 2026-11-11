# A landmark from several drone frames (a building on an island, seen all round from the air)

Worked example: `examples/maiden-tower-drone-frames/` (the Maiden's Tower in Istanbul: a square stone shaft with an
octagonal lantern, a lead dome and a flagpole, a crenellated fort, a single-storey annex with a tiled roof, a terrace
with a parapet and benches, a quay, armour-stone rocks and a beacon; six screenshots of a drone video taken all
round it, 1290-1586 px wide, no EXIF). Built on `multi-photo-room.md` (joint solve from hand-read points) and
`single-photo-vehicle.md` (bake, project, light divided out); this file is what an outdoor landmark seen from the
air changes, and what went wrong.

Second worked example: `examples/galata-tower-drone-frames/` (the Galata Tower in Istanbul: a round stone shaft, an
arcade storey, a corbelled balcony with an iron railing, an upper storey, a flared lead cone with four dormers and a
gilded finial; four screenshots of drone videos, 250-456 px wide, all but one from the same side). A round tower
changes the cameras, the angles and above all the side no frame shows: section "A round tower" at the end.

**Before anything else, look at every surface no frame shows, from close, the way the user will** (render views all
round, on the unseen side, at the distance a viewer stands). The Galata Tower's frame-camera numbers were good while
its back was rotated copies of the front: the user saw patches at once.

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

## A round tower (the Galata Tower)

Four frames, three of them present-day and from the same side, one older. What a turned landmark changes:

### Frames, eras and scale

- **Check that every frame shows the same building.** A landmark gets restored: frame 1 showed the Galata Tower before
  2020 (a lighter cone without the flared eave, an older finial). Use such a frame only for what did not change (the
  shaft), never for the changed part or for textures, and tell the user which state the model shows.
- **Scale from a published dimension of a part the frames measure well** (the base diameter, 16.45 m), then check it
  against another published figure (the apex height: 61.9 m here, 62.59 m published). A round tower has no door in
  view; its radius is what the solve measures best.

### Cameras and profile

- **Solve the lathe and the cameras together** from: axis points (finial tip, ball, apex), each ring's left and right
  extremes (x only) and its front point (y at the axis), and silhouette points (x at a row). Project the rings
  numerically (1440 samples a ring, a silhouette as the extreme of rings at many heights, vectorised): extremes and
  silhouettes of a circle under perspective are not its diameter's ends. 1.8 px RMS over the four frames.
- **Bound every height and keep their order**: the first solve put the balcony above the eave. A ring with extremes
  only has no height; give it its front point.
- **One feature, one edge.** The cornice's extremes were read on its wide top and its front on its bottom: the solve
  could satisfy neither. Read the same edge in every frame or drop the observation.
- **Read edges by number, not by eye**: the strongest gradient peaks along a row or a column (`peaks.py`), and a
  silhouette followed row by row from a seed (`track.py`). Grids drawn every 2 px hide the picture; every 10 px at
  2-3x is the readable density.
- **The profile from the silhouettes**: invert each tracked silhouette point to (radius, height) through its frame's
  camera (`invert.py`) and fit the cone to them (quadratic here, not straight); the flare to the eave as a curve
  tangent to the cone, ending at the eave ring the solve measured.
- **A turned object's azimuth is a gauge freedom.** Cross-correlating the frames unwrapped onto the cylinder did not
  find the frames' relative angles (NCC 0.06-0.13: stone is noise). Windows did: dark blobs on the unwrapped shaft,
  matched by order across frames, as shared 3D points with unknown angle and height in the joint solve. The arches
  of two storeys then lined up across the frames, which is the check.
- **Count and place repeated parts on the unwrap**: 14 arches in both arcaded storeys (25.7 deg), the dormers every
  90 deg, all on one angle (-8 deg). The unwrap (angle, height) through each frame's camera shows them level and
  aligned when the cameras are right.

### Projection

- **Weight each view by its resolution as well as its angle** ((f/z)^2 x cos^2, then ^6 to pick): the closest frame
  then dominates where it sees (10-17/255 per pixel from its own camera, against 24-35 for an equal-weight blend).
- **A blend cannot match every frame.** Two low-resolution frames rendered from a texture the close frame dominates
  stay ~24/255 per pixel: their own sharpening, light and 1-2 px registration. A photometric registration of their
  cameras to the texture found them already at the minimum: the rest is local, not a camera error.
- **Mask what stands in front of the building**: a lamp post, a sign and people at the foot came out as ghosts on the
  shaft (from the other frames' parallax).
- **No denoiser and a 1 px pixel filter on renders that are compared with photos**: the denoiser softened every stone.
- **People on a balcony are not the building.** For the material version, mirror the clean wall above the railing's
  top down over them; say that the photo version keeps them and that this costs ~15/255 on that storey.

### The side no frame shows

- **Never fill it by rotating copies of the seen side** (here by the arches' 25.7 deg): every copy's edge is a
  vertical seam, a window column repeats at the copy's period, and the foot band's copy made a sawtooth. The user
  saw it from one look: "sanki yama yapmis gibi".
- **A non-periodic surface on a lathe (the shaft, the cone): image quilting** (`scripts/quilt.py`). Full-height
  strips from the crisp, best-seen angles, rows kept level (courses and bands continue), each joined by a vertical
  minimum-error cut; the last strip also cut into the seen texture on its right. The foot band no frame sees: one copy
  of the stones just above, joined by a horizontal cut.
- What each variant of the strips did:
  - too strict a source (cos > 0.76): two distinct strips repeated round 270 deg, as visible as the rotation;
  - mirrored strips: kaleidoscope symmetries where a strip met its mirror;
  - mixing the photo's coarse tone with synthesised fine detail on the slanted band: doubled, ghost windows;
  - no window rule: windows bunched every 20 deg; a minimum gap of 30 deg between big windows fixed it;
  - the lightning-rod cable copied with every strip: exclude such columns from the sources (one is real).
  What worked: strips 160 px wide with a 56 px overlap, sources cos > 0.7, one of the five best matches at random,
  none from the last four, no mirroring, the window gap.
- **Keep and source are two thresholds, and there are two textures.** Texels seen only at a slant (cos 0.4-0.7) are
  stretched and soft: in the photo version keep them (it is compared from the frames' cameras: 3.9/255), in the
  material version synthesise everything outside the crisp core (cos > 0.68) so the model looks the same from every
  side (4.8/255 from the frames' cameras).
- **A periodic structure (arcades, a corbel course, posts, dormers): copy whole bays** from the best-seen bay, the
  bay boundaries at the pier centres (at the arch centres for posts that stand on the piers), so seams fall where
  the structure changes anyway.
- **Light left in the frames across the angle** (a soft sun on one side in two frames): flatten it in the material
  albedo per row, towards the best-seen angles' row median, not the median of all angles (that darkened the front
  and doubled the difference to 10.3/255).
- **Smart-UV bakes leave the unused texels with alpha 1 and position 0**: exclude |P| = 0 before any per-angle
  statistics (they counted as one huge bay at angle 0 and chose the wrong source bays).

### Materials and light

- An **albedo floor of 0.01** lifts every window and recess to 25/255 in sRGB: use 0.002.
- **Lead under an overcast sky**: specular 0.06, roughness 0.6. A brighter specular reflected the sky and lifted the
  cone 12-25/255.
- **An iron railing's density decides its band's tone**: bars every 13 cm matched the closest frame and not the two
  farther ones, every 5.5 cm the reverse; 9 cm splits it. Its paint is dark and rough (albedo 0.015, roughness 0.7).
- **Per-frame light from linear passes**: renders of the sky alone and of 16 soft suns, fitted to each frame by
  non-negative least squares on the blurred tower pixels. It measured the soft sun in two frames (from the side the
  shaft is brighter on) but improved the mean only from 5.4 to 4.7/255; the delivered light stays overcast.

Numbers reached: mean colour difference 3.9/255 (photo version) and 4.8/255 (material version) over the three
present-day frames, per part 1-15. Open: the people on the balcony, the railing's pattern (bars, not its ornament),
frames 2-3's soft sun, close-ups (~18 px per metre), the window positions on the unseen side.
