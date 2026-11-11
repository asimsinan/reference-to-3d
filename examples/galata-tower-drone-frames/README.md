# Worked example: the Galata Tower from four drone-video frames

See `../../references/drone-frames-landmark.md`, section "A round tower". Four screenshots of drone videos round the
Galata Tower (Istanbul), 250-456 px wide, each cropped and scaled differently, no EXIF. Frames 2-4 are present-day
(overcast, the dark lead cone with its flared eave, from the 2020 restoration); frame 1 is older (golden hour, a
lighter cone without the flare) and is used for the unchanged shaft only, never for the cone or the textures. All three
present-day frames look at the tower from the same side (the Golden Horn behind it): about 230 deg of its
circumference is in no frame. The frames are not included; put them in `ref/` as `r1.png` ... `r4.png` (RGB).

The model's frame ("solve units"): the tower's axis is z, z = 0 at the bottom of the lower cornice, the scale fixed by
the shaft's radius under the cornice (8.0). `scale.json` holds the ground (`zg`, read on frame 3's foot) and the
factor to metres (`s` = 0.955, from the published 16.45 m base diameter). Check: the cone's apex comes out 61.9 m
above the ground (published 62.59 m), the finial's tip 68.5 m (published ~66.9 m).

Run from this folder (Blender 5.2 at `/Applications/Blender.app`; Python with numpy, scipy, opencv, pillow):

    python grid.py ref/r4.png X0 Y0 X1 Y1 SCALE out.png STEP   # read points on a grid (full-res labels)
    python peaks.py ref/r4.png row Y X0 X1 [n]                 # strongest gradient peaks along a row (or col): edges by number
    python track.py ref/r4.png L X0 Y0 Y1 > out/t4L.json       # follow a silhouette edge row by row (the cone)
    python solve.py                                            # joint solve: lathe profile + a camera per frame -> cams.json, solve.json
    python overlay.py                                          # the solved rings and silhouettes drawn on every frame
    python invert.py                                           # silhouette points -> (radius, height): the cone's profile
    python unwrap.py && python uwzone.py upper 7.3 7.9 12.6    # frames unwrapped onto the cylinder (angle, height)
    python blobs.py                                            # windows on the unwrapped shaft -> win_obs.json (shared points)
    Blender -b -P idr.py                                       # geometry (geom.py, params.json) -> index renders id/rN.png
    python idov.py                                             # the model's outlines on every frame
    ./run_all.sh                                               # bake -> project + synthesise -> irradiance -> albedo -> final renders -> light fit -> stats
    python stats.py final                                      # per frame and part: colour difference, p5/p95 lightness
    Blender -b out/final_work.blend -P backviews.py -- NAME    # close views round the unseen side -> out/bv_NAME_<deg>.png
    Blender -b out/final_work.blend -P topviews.py -- NAME     # the same for the upper storeys and the cone
    Blender -b out/final_work.blend -P deliver.py [-- photo]   # tidy, metres, pack -> deliver/galata_kulesi(.blend|.glb|_foto.blend)
    python showcase.py

`geom.py` is the parametric tower: the tapered shaft, the lower cornice, the arcade storey with 14 arches cut as
recesses with a window recess in each, the corbelled balcony slab, the iron railing and 14 stone posts, the upper
storey with 14 arched openings, the flared eave and the cone (a quadratic profile measured from the silhouettes, joined
to the eave by a Bezier flare), four dormers and the finial (neck, ball, bulb, rings, spike). Arches, openings and
dormers share one angle (`th0` = -8 deg), measured on the unwrapped frames.

`texbuild.py` projects frames 2-4 through a depth test, each view weighted by cos^2 and its resolution (f/z)^2, so the
closest frame dominates where it sees. What no frame sees: `quilt.py` (also in `../../scripts/`) for the shaft and the
cone, whole bays copied from the best-seen bay for the 14-fold storeys, posts and dormers. Two shaft and cone textures:
`tex/<part>_photo.png` keeps every texel a frame sees (the photo-projected version, matched from the frames' cameras),
`tex/<part>_q.png` keeps only the crisp core and synthesises the rest (the material version, seen from anywhere).
`albedo.py` divides the light out, mirrors the clean upper-storey wall down over the people behind the railing,
gives the unseen recess sides the photo's stone pattern and the openings dark glazing, and flattens across the angle
the soft sun two frames left on the shaft. `lightpass.py` + `lightfit.py` fit each frame's light from 17 linear passes
(sky + 16 soft suns, NNLS) to measure what the frames' own light would add.

Result: the photo-projected version 3.9/255 mean colour difference over the three frames, the real-material version
4.8/255 (per part 1-15). Not identical: the people on the balcony are not modelled (upper storey 15/255 in two
frames), the railing's density trades the closest frame against the two farther ones, frames 2-3 were shot under a
soft sun the delivered overcast light does not have, close-ups are soft (the frames carry ~18 px per metre on the
tower), and the side no frame shows is synthesised from the seen side, its window positions a guess.

What went wrong, in the order met:
1. Frame 1 was a different era (before the 2020 restoration): its cone and finial would have broken the solve.
2. The solve fell into a minimum with the balcony above the eave: bounds on every height, and each ring needs its
   front point (y) as well as its extremes (x).
3. A ring's extremes read on the cornice's wide top and its front on its bottom: one feature, two edges. Read the same
   edge in every frame, or drop it.
4. Cross-correlating the unwrapped frames for their azimuth failed (NCC 0.06-0.13); the windows as shared 3D points
   with unknown angle and height fixed it (r3 -13.3 deg, r4 -9.9 deg from r2), and the arches then lined up.
5. One frame 38 % brighter: gains from co-seen texels, applied as gain^2.2 in linear light.
6. The denoiser and a 1.5 px pixel filter softened the stone: no denoising, filter width 1.0.
7. A lamp post, a sign and people in front of the foot came out as ghosts on the shaft: mask them.
8. An albedo floor of 0.01 lifted every window and arch recess to 25/255: 0.002.
9. The unseen side filled by rotating 25.7 deg copies of the seen side: the user saw patches at once (vertical seams,
   a window column repeating, a sawtooth at the foot). Image quilting replaced it; then, in turn, a too-small source
   pool repeated one strip, mirrored strips made kaleidoscopes, mixing the photo's tone with synthesised detail
   doubled windows, and windows bunched until a 30 deg gap was enforced.
10. Smart-UV bakes leave the unused texels with alpha 1 and P = 0: they counted as one huge bay at angle 0.
11. The material version first flattened the angle-wise light to the median of all angles and darkened the front
    (10.3/255): the target is the best-seen angles' row median.
