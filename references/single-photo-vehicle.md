# One photo of a vehicle of a known type (an airliner, a car, a ship)

A known type gives real dimensions (length, span, track, heights), but one picture, maybe an AI one, will not agree
with all of them. Treat the type's dimensions as **priors with a sigma**, solve the camera with the uncertain ones as
extra unknowns, then let the photo's silhouette decide every shape. Worked example: `examples/airliner-single-photo/`
(a 737-800 at sunset; photo-textured 3.0/255, real materials 9.0/255 from the photo's camera).

## Steps

1. **Points that sit on known geometry.** Wingtips (both sides: they fix yaw), stabiliser tips, the fin's top
   corners, wheel ground contacts (z = 0: they fix height and pitch), the engine intake centre. Read them on zoomed
   grids. Ten points at 3 px RMS were not enough: the solve chose a 5600 px telephoto that drew the fuselage too
   thin. Add **silhouette residuals of a part whose cross-section is known** (the fuselage as an ellipse of the
   type's width and height): for each station, the two tangent points seen from the camera, projected, against the
   photo's top and bottom edge. The shape priors (stations, heights, track) go in with sigmas (6 px per sigma).
2. **Build the vehicle as parameters, not by hand.** Fuselage rings (nose powers, tail-cone start and end), aerofoil
   stations for wing (glove, kink, dihedral, sweep, a blended winglet arc and blade), stabiliser and fin (with a
   dorsal fillet), lathed nacelles, gear from primitives. Keep the section definitions pure Python (`secs.py`) so
   numpy can use them too.
3. **Fit the shape by rasterising in numpy, not by rendering.** Project the same rings through the solved camera,
   fill the quads (`cv2.fillConvexPoly`), take top / bottom / left / right edges per column or row and compare with
   the photo's (a GrabCut mask seeded by the model's own render; thin edge-on surfaces from the bright band per
   column). A fit of 26 parameters takes seconds. Two traps: pixel-quantised residuals need a finite-difference step
   of about 0.1 sigma (scipy's `diff_step` is relative to x, zero at x = 0: offset the normalised parameters), and a
   target window that takes in another part (the stabiliser at the tail cone's edge) drags the fit.
4. **Photo onto UVs through a depth test.** Bake every part's world position and normal into its UVs (EMIT of
   Geometry Position, float image set to Non-Color first), render the camera's depth, then in numpy: texel ->
   pixel, visible if its depth matches, weight = cos to the camera. Mirror partners (left wing / right wing, the
   fuselage's theta -> pi - theta) fill what the camera cannot see; each texel takes the better-facing view. For the
   photo-camera match use each object's own samples; the merged mirror texture is for the real version.
5. **Real materials from the photo.** Albedo = paint x (photo / its smooth shading, linear) on texels seen at a good
   angle (cos > 0.27): windows, doors and panel lines stay, the light goes. Ground: rectify z = 0, cut a sunlit
   patch at the slab-joint period, cross-fade its edges, divide by the irradiance a grey ground receives. Sky: the
   photo's sky rows as the sky's elevation profile for lighting, and the photo's sky at its true elevations for
   camera rays only (Light Path > Is Camera Ray), so the backdrop from the photo's camera is the photo.
6. **Light by measuring.** Sun direction from the shadow (project the baked points along the sun onto the ground,
   IoU against the photo's dark ground). Render unit passes (sun, low sky, high sky, a fill) and fit their colours
   linearly to the photo's pixels, each part weighted equally. Then per-texel albedo gain maps (photo / render,
   low-frequency, clamped) for what the light cannot do.

## What one picture's lighting can refuse

An AI picture may light the vehicle in a way no single scene can: here the shadow said sun 11 deg up behind the
right wing, while the wings' tops looked lit from high in front. Fit what is consistent, measure what is left, and
say so with numbers rather than bending the sun until the shadow is wrong.
