# A vehicle from many photos found on the web, outside and inside (a heritage tram)

Worked example: `examples/tram-multi-photo/`. Twenty pictures of Istanbul's nostalgic Taksim–Tünel tram, sent in
batches: street photos from all sides, the saloon and the cab from inside, and later photos sent only to point at
faults. Built on `drone-frames-landmark.md` (a camera per picture, joint point solve) and `single-view-interior.md`
(an inside made exact from one camera). What a vehicle seen in many unrelated photos changes, and what the user
rejected, in order.

## Before anything: which vehicle

- **Web photos of "the same" vehicle show different units and eras.** The first six photos showed car No. 115 with
  a bow collector on the wire, varnished window frames, a bare scissor gate; the next batch car No. 34 after its
  conversion to batteries (no wire, a battery box on the roof, maroon frames, glazed bi-fold doors, IETT/İBB logos);
  later photos car 47. Read the fleet number and the details on every photo before solving, and ask the user which
  unit the model is (here: 34). Use the others only for what did not change (body dimensions, running gear).
- Attachments sent while a turn runs are not written to disk: two batches had to be sent again. Copy every new
  picture into the work folder as soon as it is on disk.

## Cameras and size

- **One camera per photo, focal and principal point free** (web photos are cropped): a joint least-squares solve of
  all cameras and the body's dimensions from hand-read points (lamps, headlamp, sign, window corners, the side's
  posts), soft-L1, a weak prior on the principal point and a log-focal prior (sigma 0.25) per photo. Without the
  focal prior one camera came out at f = 208 px.
- **Points only on the front end leave the yaw free**: the side rectified smeared. Add points along the side
  (door posts, window posts, the far end).
- **Equal repeats as a hypothesis**: the side's three windows were compared as free / equal / with or without an end
  panel by the solve's residual; the user's frontal side photo later settled it (a narrow panel at both ends).
- **Scale from a standard part the photos show**: here the rail gauge (assumed 1 m, unverified, said so). The rails'
  image lines in each photo, back-projected to z = 0, also fix the camera's height above the rail.
- **The interior photo's camera from its vanishing points** (`scripts/solve_camera_vp.py`), the position from the
  window posts back-projected onto the wall planes. Hand-placed cameras looked right and were 0.4 m off.

## Shape: what the user had to point at

- **The nose is neither facets nor one oval.** First three flat facets with sharp corners ("ovalimsi, sen keskin hatlı
  yapmışsın"); then one big oval curve: the error from the frontal photo went up (37.5 -> 42.8/255). What matched:
  the walls three panels with soft joints (radius 0.20 m to the side, 0.06 m between panels, white lining at the
  joints), the **white roof edge** a vertical band that rolls over with a small radius, the fender flat-fronted with
  round corners. Measure the band's limits on the frontal photo by ray-plane intersection (the hood's bottom was
  2.62 m; a guess of 2.70 made the cab windows short).
- **Build every part of the curved end along one plan curve** (arc-length strips: dash, cab band, posts, glass,
  lining, decals); then a radius change is one parameter, and decals follow the curve.
- **Doors are not panels.** Flat black doors were rejected ("kapılar dümdüz, gerçeği telli"): glazed bi-fold
  leaves with a thin frame, hinges and a grab bar, tinted glass with alpha, and the scissor gate behind them as real
  bars (vertical flats and crossed links in two bands), so the gate shows through the glass as in the photos. The
  doors reach down to the step, and the opening's width is measured, not filled between posts.
- **The running gear is open on a heritage tram** ("tramvay altı öyle olacak", a photo with a box drawn on it): a
  riveted solebar, a truck side frame nearly flush with the body side, axle boxes, pairs of coil springs, long rusty
  brake rods, curved lifeguard bars. A black box or a battery case between the wheels read as wrong at once.
- **The end corner beside the door**: no fender lip may run alongside the door (photo of the rear corner); steps stay
  within the body's width when seen from ahead.
- **Seats from the interior photo, through its camera**: orientation (all facing one way, not face to face), pitch
  (0.60 m), width (0.32 m), back height (0.75 m above the floor), measured on the window posts and the brass grips
  found as highlight peaks along each row's line to the vanishing point. The first seats faced the wrong way, were
  too big, and the user said so.

## Surfaces

- **Glossy leather is a fault when the photo's is satin**: roughness ~0.5, no coat; back and cushion measured
  separately (the cushion is darker).
- **Wood from the photo's pixels, but only wood pixels**: a palette box over the floor took the metal hatch frames
  and the window glare (white streaks); filter by hue/saturation first. The floor rectified from the photo through
  its camera, hatch lines inpainted, glare columns skipped, tiled along the car (the first tile ran across it).
- **Lettering redrawn, not cut**: cuts from a three-quarter photo are soft and skewed ("yazılar eğri"). Redraw sign,
  route number and warnings in a matching face (macOS SuperClarendon Bold, condensed) on transparent images;
  logos cut from the most frontal photo only.
- **Panel layout from the most frontal side photo**: white-lined rectangles on flat red (not raised rails), the end
  columns white with a red round-topped panel; the logos in the lower row in the photo's order.
- **Paint: one red, measured** (photo/render ratio over the red pixels of two photos); reflections in the side
  photos are not the paint.

## Light and comparison

- **Interior comparison from the photo's camera with the photo behind the panes** (an emission material on the
  glass with Window coordinates, camera rays only): the street then matches and the materials can be calibrated.
  Overcast rain light = a neutral grey sky and ground bounce, no sun.
- **Each exterior photo has its own sun**: sweeping the sun direction per photo changed the error by only 2-3/255;
  most of the difference was geometry and glass.
- **Measure by part group through the ID render** (glass, paint, white, frame, roof, under): glass carried ~20-30 %
  of the error (people and reflections behind it in every photo).

## Tooling that cost a round each

- **String-replace edits of a long Blender script silently failed or broke indentation**, and the next measurement
  read the previous render (an unchanged number after a "fix"). Delete the output before every render; grep the
  edit; check the log for "Error|Traceback".
- **A saved scene's output format sticks**: novel views came out as EXR; set PNG explicitly.
- **A mirror helper whose rotation centre is wrong** put the rear end on top of the front (CX computed from the
  wrong ends); preview the whole vehicle from far away after every plan change.
- `numpy.trapz` is gone in numpy 2 (`trapezoid`).

## What the user rejected (in order)

1. The wrong vehicle had been modelled from the first photos (115 under the wire; the user wanted the battery 34).
2. "Gerçek malzeme gerçeğe benzemiyor, kapılar dümdüz, gerçeği telli" — doors as flat panels, no gate behind.
3. "Oturaklar karşılıklı" / seats measured wrong; "koltuk dokuları aşırı parlak".
4. "Kapılar daha büyük", "tramvay altı öyle olacak", "arkası dümdüz gitmiyor kavisli".
5. "Öndeki far da farklı" — a plain drum: the lamp has a bolted flange, a ring bezel, a silver reflector.
6. "Ön tarafın tasarımı ovalimsi... hem üst beyaz hem kıvrımlar", "doku gerçeğe yakın değil".
7. "Tramvay üstündeki yazılar düzgün görünmüyor, bazı yerlerde eğri".
All were visible in side-by-side crops from the photos' angles; render them before handing over.
