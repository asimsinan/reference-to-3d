# Worked example: a heritage tram from many web photos, inside and out

See `../../references/multi-photo-vehicle.md` (read its "What the user rejected" first). Istanbul's nostalgic
Taksim–Tünel tram: twenty pictures in three batches, of different cars and eras. The first six showed car No. 115
with a bow collector under the wire; the next nine car No. 34 after its conversion to batteries (no wire, a battery
box on the roof), with the saloon and the cab from inside; the last five, sent to point at faults, showed the doors,
the running gear (car 47), the side panels square-on and the rear corner. The delivered model is No. 34. The
photos are not in this folder: put them in `ref/` (`p1.png`..`p6.png`, car 115) and `ref2/` (`p7.png`..`p20.png`).

    py() { uv run -q --no-project --with numpy --with scipy --with opencv-python-headless python "$@"; }
    B=/Applications/Blender.app/Contents/MacOS/Blender
    tools/g.sh ref2/p9.png 0 0 864 758 1.1 g/n9.png 50        # gridded crops to read the points (tools/mont.py, marks.py)
    py solve.py                                              # car 115: six cameras + the body from pts.json (+ rails.json)
    HYP=equal py solve34.py                                  # car 34: cameras 9, 13 (+ 11, 12) from pts34.json, body priors from cams.json
    py ~/.claude/skills/reference-to-3d/scripts/solve_camera_vp.py ref2/p8.png --out cam8vp.json   # the saloon photo's camera
    V34=1 CAMS=cams34.json INT=1 $B -b -P idrender.py -- 8 9 13; V34=1 py idov.py 8 9 13   # part outlines over the photos
    V34=1 BK=bake34 CAMS=cams34.json DENS=400 AO=0 $B -b -P bake.py                         # positions/normals per part
    BK=bake34 REF=ref2 CAMS=cams34.json OCC=occ34.json NOGAIN=1 CXR=-0.18319 MIRROR=1 TEXD=tex34 py texbuild.py
    py cut34.py; uv run --with pillow python letters34.py; py boards34.py; py albedo34.py  # screens, logos, lettering, wood
    ./calloop34.sh 3                                         # paint/white/maroon albedo by photo/render ratio (photos 9, 13)
    ./intloop.sh 3                                           # saloon materials against photo 8 (window backdrop = photo 8)
    $B -b bake34/baked.blend -P final34.py -- real views     # showcase views; closeup34.py: next to photos 16-20
    $B -b bake34/baked.blend -P final34.py -- real save=$PWD/tram34.blend glb=$PWD/tram34.glb
    py showcase.py showcase.jpg

Files: `geom34.py` (the car: saloon walls with windows, posts and white-lined panels, both ends from one plan curve
with soft panel joints, the rolled white roof edge, fender, bi-fold doors with the scissor gate behind, steps, the
truck with springs and rods, battery box), `interior34.py` (seats measured on photo 8, wainscot, barrel ceiling with
ribs, grab rails and straps, lamps, glazed bulkheads, the cab console and its five screens), `final34.py` (materials,
decals, light, renders, .blend/.glb), `geom.py` (mesh helpers; also car 115's geometry), `final.py` (car 115; its
gate builder is reused), `solve.py` / `solve34.py` (joint point solves), `texbuild.py` (photo -> UV texels through
the depth test, 180-deg partner or mirror for the unseen side), `cut34.py` (rectified cuts: screens, logos, colours),
`letters34.py` (lettering redrawn in a Clarendon face), `intcal.py` / `cal34.py` / `albcal34.py` (measured
calibration), `nosefit.py` (nose outline over photos 9 and 13 at several corner radii).

Numbers (mean |photo - render| over the tram, 0-255, from each photo's own camera): photo 9 37.7, photo 13 40.7,
photo 8 (saloon) 40.9. Car 115's photo-projected version 33/255 over its six photos. Not identical: the glass (people
and reflections in every photo, none in the model) carries the largest share; the fender's flat top is narrower than
the photo's; the running gear is sparser than photo 16's; the cab is modelled from one photo.
