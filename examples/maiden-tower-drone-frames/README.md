# Worked example: the Maiden's Tower from six drone-video frames

See `../../references/drone-frames-landmark.md`. Six screenshots of a drone video taken all round the tower
(1290-1586 px wide, each cropped and scaled differently, no EXIF). The frames are not included; put them in `ref/` as
`r1.png` ... `r6.png` (RGB). The model's frame: +X the sunlit face with the fort's door, +Y the annex side, z = 0 the
terrace, units x 1.05 = metres (doors measured at 2.0 units). The showcase is `docs/showcase/maiden-tower.jpg`.

Run from this folder (Blender 5.2 at `/Applications/Blender.app`; Python with numpy, scipy, opencv; `PYX=...` for a
ready interpreter if `uv` waits on its cache lock):

    python grid.py ref/r5.png X0 Y0 X1 Y1 SCALE out.png STEP   # read points on a grid (full-res labels)
    python solve.py 40                                         # joint solve from hand-read points -> cams.json, geo.json
    python edgefit2.py                                         # each camera refined on Canny edges, points held -> cams_edge2.json
    python hit.py N axis value x,y ...                         # a pixel's ray onto a plane (doors, gables, the beacon)
    python planov.py 0 5 4 6                                   # the terrace plane rectified from frames, model outlines drawn on
    ./geoloop.sh                                               # geometry -> index renders -> GrabCut IoU (shape changes)
    python gcmask.py                                           # photo masks by GrabCut seeded from the model (once the shape is close)
    python footprint.py -2.0                                   # the masks' hull on a horizontal plane: the waterline outline
    python rocktex.py && python stonetex.py                    # rock tile, stone pattern from the shaded wall
    ./run2.sh [r1 r5 ...]                                      # bake -> project -> irradiance x2 -> albedo -> renders out/final_rN.png
    python stats.py final                                      # per frame and part: colour difference, p5/p95 lightness
    python pcrop.py final r5:quay r4:beacon                    # photo | render crops by the part's box
    Blender -b out/final_work.blend -P novel.py                # viewpoints no frame has -> out/nv_*.png
    Blender -b out/final_work.blend -P deliver2.py             # tidy, scale, pack -> out/kiz_kulesi.blend, out/kiz_kulesi.glb
    python showcase.py

`geom.py` is the parametric tower (`params.json`): shaft, corbel, octagonal balcony and lantern room with window
recesses, lead dome with seams, crenellated upper gallery, pole, finial and flag; the fort with merlons, the annex with
its roof and porch, terrace, parapet with benches, quay, rock skirt from the measured waterline, armour stones, the
beacon. `light.json` is the sun (azimuth, elevation from the fort's shadow) and the gradient sky; `gain.json` each
frame's exposure; `ignore.json` the boats and people masked out of every frame.

Result: silhouette IoU 0.887 over six frames (GrabCut masks, sea held out); mean colour difference 10/255. Not
identical: see the reference's last section.

What went wrong, in the order met:
1. One focal length for six screenshots: each frame is scaled differently.
2. A colour-threshold sea mask, then index renders with the sea hidden: both made a good fit look bad.
3. Lantern-room walls built quad by quad: half faced inward and were "unseen".
4. Albedo against diffuse light rendered with a specular layer, under a uniform sky: dark shaded surfaces too bright.
   A metallic dome fixed two frames and broke three.
5. The water level tuned on a mask that had swallowed the shadowed water along the quay.
6. The beacon's foot read too low (rocks hide it), its stripe projected and broken at the corners.
7. The scale guessed from people (1.3); doors say 1.05.
8. A part left out of its statistics group: a texture change "did nothing".
