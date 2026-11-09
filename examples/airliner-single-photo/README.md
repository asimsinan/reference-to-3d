# Worked example: an airliner from one photo

See `../../references/single-photo-vehicle.md`. One 1770 x 1187 picture of a white Boeing 737-800 (blended
winglets, two over-wing exits) on a concrete apron at sunset, seen from the front-left and a little above; most likely
an AI image. Known type, so the real dimensions are priors; the photo then decides every shape. Put the picture in
this folder as `ref.jpg`; the scripts work in the current folder. This photo's numbers are in them: the marked points
in `solve.py`, the edge targets in `fit_wing.py` / `fit_body.py`, the ground tile window in `groundtile.py`, and the
solved and fitted values in `cam.json`, `tweaks.json`, `sun.json`, `calib.json`.

    py() { uv run -q --with numpy --with scipy --with opencv-python-headless python "$@"; }
    B=/Applications/Blender.app/Contents/MacOS/Blender
    python3 grid.py 1100 120 1260 260 20 g_fin.jpg 3         # zoomed grids to read the points (tips, gear, fin top)
    py mask.py; py edges.py                                  # GrabCut seed mask, the fuselage's top edge
    py solve.py                                              # cam.json: pose, focal, the type's free dimensions
    $B -b -P build.py -- id out_id.png; py overlay.py out_id.png ov.jpg   # part outlines over the photo
    py mask2.py                                              # GrabCut seeded by the model's own render
    py fit_wing.py; py fit_body.py 80                        # tweaks.json: wing, nose, tail cone, fin, stabiliser
    bash run_match.sh                                        # bake P/N + depth, photo -> UV textures, match render, compare
    py sunfit.py                                             # sun from the plane's shadow on the ground
    py ground.py; py groundtile.py; py envmap.py             # concrete tile, sky for light, sky for the camera
    py albedo.py; bash calloop.sh                            # albedo with the light divided out; sun/sky/fill passes fit
    bash all.sh                                              # full chain incl. albedo_cal.py gain maps, final compare
    SAMPLES=96 $B -b -P build.py -- views x                 # other angles -> views/
    NORENDER=1 DELIVER=$PWD/ucak_737.blend GLB=$PWD/ucak_737.glb $B -b -P build.py -- final x
    NORENDER=1 DELIVER=$PWD/ucak_737_foto.blend $B -b -P build.py -- match x

Files: `secs.py` (pure-python sections: fuselage rings, wing / stabiliser / fin aerofoil stations, shared by Blender
and the numpy fitters), `geom.py` (Blender lofts with UVs: u along the part, v round the ring), `fitlib.py` (numpy
projection and rasterising through the photo camera), `mats.py` (match / real materials, ground, sky, sun, fill),
`texbuild.py` (photo -> each part's UV texels the camera sees, mirrored partners merged), `deliver.py` (tidy, pack,
glTF).

Result: camera 101 m from the aircraft, 13.8 m up, f 5608 px; ten marked points at 3.2 px RMS. Silhouette edges
1-4 px RMS after the fits (the photo's aircraft came out 36.5 m long against the real 39.5: its tail cone is short).
From the photo's camera the photo-textured version differs by 3.0/255 on average (median 1.0; fin 1.2, fuselage
2.4, far wing 2.7, engine 3.9, near wing 8.1). Real materials: 9.0/255 (median 3.0); fin 1.5, fuselage 5-8,
wings ~17, the stabiliser's top ~60.

Open difference, with its cause: the ground shadow puts the sun 11 deg up behind the aircraft's right side (shadow IoU
0.82), but the photo lights the wings' and stabiliser's tops as if by a high warm sun, and the side facing the camera
as by a cool sky. No sun-sky-fill set rendered both (a higher warm fill improved the light fit but raised the total
difference to 10.3 and was rolled back); albedo gain maps (clamped 0.55-1.8) took the rest down to 9.0.

Found by looking (each fixed): the first solve's telephoto camera made the fuselage too thin (fuselage silhouette
residuals added to the solve); a stretched grey fan (duct inside surfaces culled by their outward normals: |cos| for
the duct, and the fan as a flat disc with planar UVs, since a loft cap's fan UVs collapse a 2D image); the far wing
showing the near wing's pixels (match textures per object, the shared mirrored texture only for the real version);
a scipy finite-difference step of zero at x = 0 (parameters offset to 10); the depth pass all zero (camera-space z
sign: ABSOLUTE); EXR bakes stored as sRGB (Non-Color before baking); the nose gear bay as a black box sticking out
(a shallow dark panel instead).
