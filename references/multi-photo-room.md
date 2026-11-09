# A real room from several phone photos, made walkable (with the corridor outside and an openable door)

Worked example: `examples/office-room-multiphoto/` (a 2.55 x 5.38 x 2.81 m university office, 8 WhatsApp photos, then
7 more the user added on request: frontal shots of the bookcase, a chair, the printer and two corridor views). The user
judged it room by room and object by object, five rounds, each time with screenshots from the walk viewer. What they
rejected is the most useful part of this file: read "What the user rejected" before modelling anything.

Different from the laundromat (one render, one camera): here many cameras, none frontal enough to fix the room alone,
phone photos without EXIF, mixed 1x and 0.5x lenses, and the deliverable is walked through, so every object is seen
from every side.

## 1. One room, all cameras together

- **Read the room's structure first** in grid crops (`grid.py IMG x0 y0 x1 y1 scale out step`, labels in full-res px):
  chases, beams, pilasters, the door frame, window frames, cabinets. Write them as named 3D points of a parametric room
  (`obs.py`: `points(P)` from parameters such as W, L, H, beam depth, cabinet x/y/w/h) and read the same points' pixels
  in every photo that shows them.
- **Bundle adjustment** (`fit.py`): room parameters + per photo (position, yaw, pitch, roll, f), least squares with a
  soft-L1 loss; draw the solved edges over every photo (`overlay_*.jpg`) and look. Scale from one known size (the door
  frame's outer height, 2.12 m).
- **The f–distance degeneracy**: photos taken square-on to walls let focal length trade against distance, and the room
  length drifted 5 → 7 m between fits. Pin it with lens-class priors (iPhone 1x ≈ 1480–1540 px, 0.5x ≈ 790 px on a
  2048 px long side; read which lens from the field of view) **and with shared furniture** seen in several photos as
  unknowns of the same fit (coffee-table corners, a wall rail, the desk front), plus physical priors (desk depth
  ~0.7 m, a visible floor gap between desk and table). Without them the residuals looked fine and the room was wrong.
- **Mislabelled observations are the usual cause of a bad fit**: a cabinet that was really the bookcase, two ceiling
  lights swapped, a grid label misread. When one point keeps a 40–100 px residual, crop it again before adding priors.
- Later photos (corridor, close-ups) are solved alone against the fixed room: `pnp.py` (solvePnP with a focal scan) on
  known points, or a vanishing point + known cross-section (`solve_ek3c.py`) when the known points are all on one plane.
  A long corridor shot from far away needs the vanishing point: PnP on coplanar door/plate points gave a camera 4 m off.

## 2. Textures from the photos, by rectification

`camlib.py` (`Cam.rectify(img, origin, u, v, usize, vsize, ppm)`) for planes the room cameras see (window wall,
door leaf, wall plates, corridor end wall, a fire cabinet's front). For close-up photos of one object (the bookcase,
the printer), a **homography**: 4 hand-read corners per face (`prep_printer.py`), or **SIFT + RANSAC onto an
already-metric texture** of the same face (`prep_bookcase2.py`: the frontal bookcase photo warped onto the 400 ppm
front rectified from a room photo, 170 inliers) — sharp, and in metres.

- Inpaint what becomes 3D (door handle, cabinet handles) out of the texture first.
- Normalise faces of one object to one albedo (a printer's front was 2.4x darker than its side in the photos).
- Calibrate materials against the photos by measuring (`calib.py`): render each photo's camera, compare mean linear
  colour in the same boxes per material, scale textures in linear space relative to the white paint. Exposure: AgX,
  one global value found by sampling (here -3.3).

## 3. Props: what worked and what did not

| Object type | Worked | Rejected |
|---|---|---|
| books | one sheared prism per book: spine = photo on its front, cover colour on the sides, cream page block on top; book boundaries from the vertical-gradient profile along the shelf's lean; **leaning and upright groups read off the photo per shelf**, leaning tops limited by the first upright book and the side panel (`prep3.py`) | one block per run; one lean for the whole shelf (upright books pushed through the side panel) |
| small figurines, ball | simple real solids (balloon = scaled sphere, base = rounded box) with the **frontal photo planar-projected** on the front; a ball with its **own material texture** (pebbled leather) and thin seams | GrabCut-mask heightfields ("puff" solids): stair-stepped and streaky from the side; planar projection on a ball's sides (background pixels made a black patch) |
| boxes (pen box, knife box) | photo silhouette extruded, photo on the front | — |
| devices (rotary phone, desk phone, laptop, printer) | modelled from the photo's real proportions; body from its **side profile** extruded, bevelled (`bmesh.ops.bevel`, 6 segments), slightly tapered, smooth-shaded; handset = round cups + a flattened curved tube; dial/screen/keys from the photo or a drawn texture; printer faces by homography | rounded boxes glued together (a "toy" look), a handset as a block, keys as a decal |
| chairs | shape from a frontal photo (thick rounded seat, curved back, ribbed connectors), the fabric tiled from the photo; colour checked (they are black) | generic chairs in two colours |
| lettering (fire cabinet label) | redrawn crisp | the photo's 30 px wide blur |

Cut every dial/label texture straight from the sharpest photo of it; dark textures gain-matched from the wrong sample
turned a dial green.

## 4. Doors, corridor, walking

- The door leaf is a mesh under a hinge **pivot empty** (`Door pivot`); the viewer rotates it (E, click on the leaf, a
  button) and collides with it as a plan segment from the pivot. three.js renames `Door pivot` to `Door_pivot`: match
  names with regexes like `Door.pivot`.
- Wall thickness and the frame come from the corridor photo + the inside-out door photo together.
- Where the corridor goes is not where one photo suggests: the double glass door the user saw "opposite" was really
  the corridor's end wall beside the door; extra photos settled it. **Ask for the photos that would settle a layout**
  (the user has them on their phone) rather than guessing; say which part is a guess.
- Viewer: one self-contained HTML (GLB base64-embedded, three.js from a CDN, RectAreaLights for windows and battens,
  plan-box collision from floor-standing objects, preset views, mobile joystick). Expose `window.__room` with
  `update(dt)` and `render()`: the browser pane may be hidden, which stops requestAnimationFrame, so test walking by
  stepping `update` from javascript.

## 5. Check like the user will

- Render every photo's own camera and put each next to its photo (`sheet.py`), plus close-ups of every prop from the
  angles a walker gets (low, oblique, from the side, from below a shelf). The user found every defect in viewer
  screenshots from odd angles, never in the photo-camera views.
- Check overlaps numerically (a chair cutting 9 cm into the desk; a name-set pen through the side panel) — bounding
  boxes of neighbouring objects.
- Overlapping coplanar boxes render black in Cycles (frame casing over lining): build parts that touch, not overlap.

## What the user rejected (in their words, translated)

1. "Basit temsil istemiyorum, birebir istedim" — placeholder spheres/boxes for flowers, a clock, a phone.
2. "Kitaplıkta derinlik yok" — a photo on a flat front.
3. "Koltuklar siyah normalde", "telefon aynı değil", "bilgisayarın yönü tutmuyor", "dolabın üstündeki metalimsi şeyi kaldır".
4. "Dolaptaki o saçma sapan modeller ne?" — heightfield blobs; "koridorun sol tarafı alakasız", "yangın dolabı uymuyor".
5. "Objelerden ikişer tane var" — the bookcase photo had also been mapped onto the back panel's inner face, so every
   object appeared twice; plus books poking through the side panel.
6. "Topta bir siyahlık var", "telefon hala doğal değil".

The rule behind all of them: **every object comes from a photo of it, at its measured place and size, and is checked
from the sides; anything not seen is said to be a guess.** Never ship a stand-in silently.
