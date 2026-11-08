# One picture of an inside (a cockpit, a room) seen from one place

A single perspective picture of an interior (the user's concept of a van's cockpit, a room, a shop counter) is not a
turnaround sheet: there are no other views to fit a shape to. But an interior is usually seen from one place (the
driver's seat, a fixed game camera). Then the picture can be made exact from that place, the way film sets use matte
paintings: **project the picture from the viewing camera onto simple surfaces at plausible depths.** Seen from the
camera it is the picture, pixel for pixel; turning the camera about its own point (looking round with the mouse) keeps
it exact, because turning adds no parallax.

A delivery van's cockpit, made for a game, is the case this section was learned on (its scripts are not included): mean
colour difference 5.0/255 against the picture from the game's camera (median 1.0), windows and live screens left out.

## Steps

1. **The camera is the viewer's, not the picture's.** AI concept pictures are not consistent perspective: on the van's
   picture no single camera placed the windscreen, the seat cushion and the steering wheel where they are (a solver
   ran to its bounds). Use the engine's own camera (its field of view; the van's: 90 deg horizontal) and choose its
   pitch from the picture's horizon (the far ground's line: 240 px over the middle at f = 836 px -> 16 deg down), its
   place so the main parts land plausibly (the wheel in front of the driver's seat, the windscreen's foot on the
   van's). Then the engine's cockpit view uses exactly this place and pitch.
2. **Mark the regions by hand** in a JSON of pixel polygons: windows (left out: the engine's glass and the world behind
   them show there), moving parts (a steering wheel and its openings), live screens and mirrors (their real outlines:
   a cluster's squared ellipse, a screen's rounded rectangle; rectangles over them "did not sit" in their frames).
   Draw them over the picture and look before going on.
   **Windows: only where the picture and the object both have glass.** Render the object's own glass from the camera
   (white on black) and intersect: where the picture shows a window and the object a wall, the trim round it fills it
   (a push-pull fill from the non-window pixels); where the object has glass and the picture trim, the picture's trim
   covers the glass. Otherwise the user sees the object's bare wall through the picture's window ("yan camlar tam
   oturmamış").
3. **A simple surface model of the inside**, in the object's frame: planes for the dash's top and face, the floor, the
   doors, the glass's inside (pillars and trim lie on it), the roof, the back. Cast every pixel's ray from the camera,
   take the first surface it meets within that surface's bounds. Keep everything in front of the object's other parts
   along those rays (the van's front tyres stood 0.72 m into the cab: the floor went up to 0.74 m; from the camera
   nothing changes).
4. **A mesh through the hit points** (a grid every 6 px: about 29,000 quads for 1672 x 941), each vertex's UV its
   pixel. Leave out cells that span a big step in depth (they stretch). Keep cells that are partly window and cut
   them with the texture's **alpha** (window = 0): the grid's steps along the windows' edges disappear.
5. **Moving parts on their own surfaces, solid.** The wheel: a plane through its hub, its distance and tilt chosen so
   that its outline, back-projected, is a circle of a real wheel's size (0.19 m round, tilt 71 deg); its own crop of
   the picture as its texture, its outline in alpha (smooth the hand-marked outline as a closed curve: a polygon of 17
   points showed facets). A flat cut-out looked "yarım" (half made) to the user once it turned: give it a back and
   sides, **extruded along the camera's rays** (from the camera no side shows, as in the picture; extruded along the
   wheel's axis they showed as a dark rim), and round the front by moving points towards the camera along their own
   rays (exact from the camera still). The front from every cell touching the outline (cut by alpha), the back and the
   sides from the cells wholly inside it. Write it in the frame the engine turns it in (hub at the origin, axis local
   z).
6. **What a moving part hides**, filled for the surface behind it. OpenCV's inpainting carried the wheel's own edges
   into the hole and left its ghost; a push-pull fill left a wheel-shaped blur. What worked: fill row by row between
   the colours just left and right of the part (a dash is horizontal bands), soften up and down, and keep the
   picture where the part's openings show what is really behind (the instrument binnacle through the wheel's top).
7. **Live screens**: flat shapes facing the camera, placed in front of the nearest point of their outline (else the
   dash's crease cut one in half), 0..1 UVs over their bounds; lay the engine's drawing out like the picture's screens.
   **Mirrors** the same, their u reversed, fed by scene captures looking back from the object's mirror pods (outside
   the pod's own mesh: inside it they saw its inside). Captures are expensive: two at 192 x 300 every frame cost the
   van ~10 frames a second; without global illumination, shadows, fog and bloom, 80 m at most, persistent exposure,
   one every third frame in turn.
8. **Check from the camera in Blender with emission only** (no lights, no specular: a Principled BSDF's reflections
   brightened the dash top from 97 to 163) and the Standard view transform; difference against the picture, the
   windows and screens left out, and a difference image: structure in it means misplacement, flat areas colour.
9. **In the engine**: masked, two-sided, the picture as emission at the screens' own level (the van: 400 by day, 3 at
   night) plus a little as base colour; the body's inside lining a matching grey (where the picture shows a window and
   the object has a wall, the lining shows).

10. **Looking round.** The picture covers only its own frame (the van's: 45 deg each side, 45 deg down to 13 deg up);
   if the viewer can turn the camera, everything outside it must exist too, or they see the bare shell ("kafamı
   çevirince ortaya çıkan görüntüler problemli"). Build plain surfaces there in the picture's own sampled tones and lit
   the same way: the doors up to over the side glass's stepped foot, the walls behind, the roof's lining, the floor,
   the seats; each ending where the picture's begin (its frame's edge, cast on the same surface) and a little behind
   it. Leave out the camera's own seat's back: the eye at its edge, it filled the view looking back. Shoot the engine's
   view turned (left, right, up, back) to check.

11. **Edges, zero jaggedness** (the user checks every edge at full screen; each of these was found there):
   - **Never resize an RGBA cut-out with Pillow in one go**: it resizes premultiplied, and every see-through texel
     comes back black. The engine's filter then mixes that black into every cut edge: a dark, ragged fringe round
     pillars and mirrors. Resize colour and alpha separately.
   - **Bleed the colours under the mask**: give every see-through or half see-through texel the colour of the nearest
     opaque one (`cv2.distanceTransformWithLabels`, `DIST_LABEL_PIXEL`). Otherwise the picture's window (rainy glass,
     lights) shows along the cut as light specks.
   - **Where the picture's own seal is thin** (1-2 px under the cut at a windscreen's foot, a door's sill), draw one
     even seal a few px thick along the fitted cut, its far edge antialiased. Stretched or snapped from the picture,
     it came out wavy and broken.
   - **Edges snapped to the strongest change catch raindrops** beside them (notches of 10-16 px). Smooth each edge as a
     chain (median over ~31 rows, then a mean over ~15, the windows shrinking symmetrically at the chain's ends).
     Close see-through slivers under ~15 px beside mirrors, and drop islands under ~300 px of either kind.
   - **The top of the view belongs to a 3D header, not to the picture**: cut along the picture's top, its roof
     console and frit gave a ragged edge. Bring the ceiling down to a fixed picture row across the windscreen, with a
     thin dark seal at its foot, rising smoothly (smoothstep over ~12 deg) over the pillars. Place it in front of
     every picture surface along each ray (a BVH of the picture meshes), and smooth those distances over the grid (a
     min over 9 x 9, then a small Gaussian), or it creases.
   - Where two pictures meet, give one of them a whole part (a mirror with its frame and stalk), with one blurred,
     smooth boundary; a hand-traced cut that leaves a corner shows the other picture's copy beside it.
   - **Pick, don't guess**: to name what a stray shape is, cast a ray from the camera through that pixel and list the
     surfaces it meets. A "second mirror" turned out to be a small corner window seen through.

12. **Several pictures of one inside, made consistent**. Pictures generated one by one never share a camera
   (asked for "the same cab, turned 60 deg left", the model also moved the camera: 46-100 px apart on common points).
   What works, with an image model that edits (Gemini 3 Pro Image via OpenRouter; about 0.24 $ a 4K picture):
   - Generate the front only, from the viewer's place (for a driver: behind the wheel's middle, or the seat "looks
     crooked"). Choose its pitch from the object: where its windscreen foot lies on the object's own (fitted 0.2 deg).
   - **Cast it into each turned camera from the same eye** (left, right, up, up-left, up-right), the rest flat
     magenta, and ask the model to fill only the magenta. Composite: the known pixels kept (aligned by ECC, feathered
     40 px), the fill beyond. Overlaps then agree by construction; each picture shows what the ones before it do not,
     its alpha fading 25 px into them, its mesh a hair nearer.
   - **Windows: ask for a copy with everything seen through the glass flat pure green** (aligned: 1.9/255 apart
     elsewhere); the mask is the green. Far better than tracing. Cast the green copy, not the photo, when making the
     up views: their glass comes back green too.
   - **Behind a moving part: ask for the picture without it** (the wheel removed: column, stalks, floor behind). The
     part's own mask: fitted outlines (superellipses for a squircle wheel, the openings from scans of |picture - clean
     plate|; region growing leaked through the hub, which matched the column).
   - **The model will not move structure.** Asked twice to raise a window's sill to the object's belt (the band
     magenta, then painted grey with a seal), it gave the window back both times. Lift it geometrically instead: per
     column the door's own top stretched up so its seal lies on the belt (skip the old seal, redraw a crisp 3 px seal
     at the belt), only on the door's side of a mirror; cast the result into the other pictures that show it.
   - Generated parts drift in tint (an up view's headliner came back pink, 128/108/115 against 104/103/110): correct
     the filled part only, not the cast pixels.
   - Where no picture reaches, a ceiling coloured at its foot as the picture under it, easing over 6 deg into one tone;
     its start a min over 1 deg where the reach jumps, or its grid leaves a wedge of nothing.

13. **After a picture is regenerated, refit everything made from the old one**. The van's v3 front kept the v2
   wheel's mask and clean plate: the wheel came out 13 % narrow, the old rim's edge left in the room as a ghost beside
   it, and the user called it "yarım yamalak". Check by differencing each derived mask against the new picture.
   - A moving part's outline from |picture - clean plate| (the plate aligned by ECC round the part, the windscreen's
     green left out): a superellipse first, then per angle the outermost run of difference walked out contiguously
     from just inside the curve (a faint dark underside against a dark floor had been cut 2-5 px), smoothed over about
     +-10 deg. Inner edges as the rim's width along the angle; near-level edges (a hub's trim, a rim's humps) traced by
     column on the picture's own step and chain-smoothed.
   - The part's alpha straight from the antialiased mask (drawn at 1/8 px), and its edge colours the picture's own
     shade into what is behind; bled from the part's inside, the edge came out light, hard and "hairy". Bleed only
     where the picture shows the key's green.
   - In the part's openings the picture itself, the plate only under the part: the plate, from an earlier picture, put
     its own details (a cluster hood) into the opening.
   - **Bleed only real cuts, never a fade.** A side picture's 24 px fade into the front had every texel under 250
     alpha, so all its colours were taken from the fade's far side: the dash's top and its light line ran 8-16 px lower
     there, a step at the seam ("ön panel çizgisi dümdüz değil"), and the earlier "tone seam".
   - The room's mesh leaves out cells wholly in the window: change the window before building the mesh. A wedge cut
     by glass_above behind the wheel (feet hidden by the rim) stayed a hole in the mesh after the texture was fixed.
   - A stalk or fin that the glass cuts off beside a mirror display reads as a leftover ("kalıntı"): make it glass and
     carry the seal straight on to the frame; paint the display's whole glass (its picture's reflections too) under the
     live mirror.

14. **A part that turns about an axis: put the eye on the axis**. Its plane square to the eye's ray to the hub
   (tilt = the ray's own pitch; the van's came out 64.7 deg, not the 70 chosen "as a van's"). Then turned to any angle,
   from the seat it is the picture turned: its sides and its rounding along the eye's rays stay hidden. With the axis
   5.2 deg off the eye, turning brought them into view, a jagged dark fringe ("direksiyonu döndürünce kalitesi
   düşüyor"). Its texture from the image model's full-size output if there is one (the 4K source, 3.3x the working
   picture; despill the key's green there, its 1 px mask edge spans 3 texels); the outline's half-covered texels in
   the part's own colour (bled), only the openings' in the picture's; the plate 10 px round it (the picture's soft
   shade round the part stays on the dash otherwise). Add a command-line hold of the angle to shoot it turned.
   Bleed every edge's outer ~1.5 px (picture scale) from further in, outline and openings alike: those pixels mix the
   part with what was behind it. Smooth its outline as a short Fourier series of the angle (harmonics <= 12): a running
   mean left slow lumps. Cap its turn rate (a hand: ~300 deg/s) and turn motion blur off from the seat.

15. **A line several pictures share (a door's glass foot): one 3D line, cast into each**. Each picture's own key
   foot, cast onto the door and averaged per picture then between pictures, smoothed along the van; every picture cut
   on its cast to a fraction of a pixel (alpha = clip(row + 0.5 - y)), an even seal painted under it, the key's green
   left under the line painted as seal. Cut on each picture's own foot, the seal was dotted (whole rows, a step every 8
   columns) and stepped 4 px where one picture handed over to the next (a masked fade is a hard switch). And never put
   plain stand-in geometry (a seat) where a picture shows the same thing: a picture cast on the floor there is behind it.
   A picture whose line lies far from the shared one (the van's right picture: 83 px under the belt): fill the band
   between with the part's own tone (its first rows, smoothed along it), not by stretching (the whole door and its
   handle dragged up, grain in streaks). Only on the part's own side of anything standing on it (a mirror kept per
   pixel); where the picture's glass goes on well under the line (a windscreen's corner) keep its own glass. Never paint
   all leftover key green one colour: green far under a line takes the first colour below it.

16. **A part that moves: its edge is its mesh, not its alpha**. Trace the mask's half level at 1/4 px, resample
   as chains every 2 px (the outline and each opening), and triangulate with the openings as holes (Shewchuk's Triangle,
   `pq28a10`, edges kept with `Y`; its wheels stop at Python 3.12); the texture opaque. Cut by alpha the edge shimmered
   as it turned and showed what was behind (a light-blue dash). Bleed the picture's dark only on the rim's inner edge,
   not on the hub's (bled from its light trim it speckled).

17. **Before blaming the model, check the pixels the user sees**. Four rounds of edge fixes on the van's wheel did
   not satisfy the user, because the game on a Mac's Retina screen drew 1280 x 720 and the screen stretched it twice:
   every edge in steps whatever the mesh. Capture the real backbuffer (not a supersampled HighResShot, which hid it) at
   the user's window size and log the viewport's size and DPI. In Unreal: `bAllowHighDPIInGameMode=True`, the window's
   size doubled once (it is asked in pixels then), `r.ScreenPercentage 50` with TSR (the same cost), the HUD canvas
   scaled by the backing scale and the mouse and projected points divided by it. Picture textures BC7 and never
   streamed (BC1's 4 x 4 blocks broke thin seals and light lines).
   And a part that turns is better modelled than cut: the wheel's rim as a tube (radii per angle from the picture,
   Fourier-smoothed; its middle ~0.35 of its depth behind the plane so its outline from the eye matches the picture's),
   its colour one profile across it from the picture's two tones (the picture's light differs round it by 150 levels;
   cut from the picture it carried the background's shade and specks), only the hub and spokes from the picture, their
   edge at a traced feature (the spoke frame's chrome line, fitted to 0.5 px), and dipping under the tube gradually.

## A photo or render of a room to walk around (the laundromat)

A different case from the cockpit: the picture is a real photo or a game/CG render (consistent perspective), the
room is meant to be **walked through**, not only looked round from one seat. Worked example and scripts in
`examples/laundromat-room/` (a coin laundry at night, 1920 x 1080): exact from the picture's camera (0.61/255 mean,
median 0) with every prop a proxy of real depth, and the sides the picture never shows built from its own pieces.

1. **Solve the camera from the picture itself** (`scripts/solve_camera_vp.py`). With real perspective the cockpit's
   warning does not apply: LSD segments, the depth vanishing point by RANSAC over the oblique ones, the vertical one by
   least squares over the near-vertical ones (verticals converging 2-3 deg at the sides: the camera looks 4 deg down),
   principal point at the centre, f from their orthogonality (f^2 = -(vd - c).(vv - c)). The laundromat: f 1254 px,
   75 deg across. One known size sets the scale (a door 2.0 m: camera 1.375 m up, room 3.65 x 7.0 x 2.40 m; machines
   1.35 m, table 0.80, bench seat 0.45 came out right unasked, which is the check). Then draw the room's edges and
   every proxy's outline back over the picture and look: a bucket 0.06 m off showed at once.
2. **Project with a shader, not per-vertex UVs.** An empty at the camera; Texture Coordinate -> Object (that empty)
   gives each shaded point in camera space; u = 0.5 + (f/W) x/(-z), v = 0.5 + (f/H) y/(-z), emission only, Standard
   view transform. Exact per pixel on any face size (per-vertex UVs on big quads interpolate affinely and slide), no
   grid mesh. From the camera: 0.48/255 mean on the first try.
3. **Props as proxies, measured by rays**: a point's pixel and one known coordinate (a foot on the floor z = 0, a face
   on the plane x = 1.60) give the point. Repeated parts from profiles: brightness sampled across the bench seat at 25
   positions along its length, median-ed, gave 6 slats and their gaps; door circles from their top and bottom on the
   machine face. Thin open parts (a wire cart) as real tubes, not an alpha card: the tophat-mask card caught the
   table's edges and the floor's shadow, and a card shows the same wires on its front and back faces.
4. **The room behind the props: layered clean plates.** Without them a prop's pixels stay painted on what is behind
   it and slide off when the camera moves (the cart's handle lay on the table top).
   - The mask is the props' **rendered coverage** from the camera (props white emission, room black), not their
     outlines: an outline also wipes the background seen between a stool's legs.
   - **Depth layers**: A nearest (bench, cart, bucket), B (washers, table), C (the rest). Layer B's texture is the
     picture with A's coverage filled (push-pull), C's with A and B's, the room's with all. The table then shows no
     cart handle, the washers no bucket.
   - **Thin parts: fill only the pixels they cover fully.** Dilated, their antialiased edges mixed the wire's pixel
     with the filled blur and the cart differed 5.6/255 from the camera; filling only fully covered pixels (found by
     opening the coverage 7 x 7: thin parts drop out) gave 1.6, big parts still dilated 7 px. The price: wires the
     proxies miss stay painted faintly behind; give the room's plate the strict mask, the prop layers a 5 px dilation.
5. **Outside the picture's frame: never the clamped edge.** Its pixels streak across every surface outside the frame.
   Fade (smoothstep over 0.06 of the frame) into the surface's own texture: first its median tone (object colour
   read by Object Info), then, for walking round, **repeats cut from the picture** (`scripts/rectify_plane.py`):
   - Rectify each plane through the camera, cut its repeating unit and map it in world space (Geometry -> Position,
     dot with the plane's axes, REPEAT). The laundromat: a window bay (1.05 m) along the window wall and the entrance,
     a washer unit (0.833 m, its edges from the gaps between units) for the row continued to the entrance, the floor,
     the ceiling's and walls' concrete, the bench's slats along its length, the light fixture.
   - **Floor tiles: the period by autocorrelation** (0.2875 m), the cut from a grout line to the grout line two tiles
     on in both directions: then it repeats without a seam.
   - **Concrete: flatten and calm it** (divide by a blur of sigma 10-15 px, pull 30-45 % towards the mean): a 0.6 m
     sample with one stain repeated it every 0.6 m along the wall ("a row of the same stain").
   - Fill the magenta (unseen) texels along the structure: row by row under a horizontal beam, column by column along
     slats; pink specks showed on the bench otherwise.
   - Repeated machines all carry the copied unit's number and price ("400"); copy one without a hanging sign.
   - Continue the geometry the picture implies: the machine row and the bench to the entrance, the lights at their
     spacing, a front wall (the window bay again).
6. **Generated fills instead of repeats** (step 12 above) need an image model's credits: check the balance first
   (here: 0 credits, no other key), and offer the repeats as the free way.
7. **Check by walking**: render the turned views from the eye (left, right, back, down) and two walking views (from
   the entrance, from the back looking out), not only the picture's camera; that is where a stretched edge, a repeated
   stain and a ghost show.

## Limits to say

- Exact from the one place only: seen from outside through the windows it is a set (flat doors, a raised floor).
- A walked-through room built from repeats shows them on a close look (the same machine, the same window bay); a
  prop's far side is the picture's near side stretched, and a few faint ghosts of thin parts stay behind them.
- The picture's lighting is fixed (its dusk, its ambient lights); it does not change with the scene's.
- Where the picture shows a window and the object has a wall (or the reverse), they disagree; say where.
