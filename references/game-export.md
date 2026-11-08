# Delivering to a game engine

## What the engine needs from the model
- **Baked textures.** Engines cannot run the projection shader; `project.py --export` bakes each mesh into its own
  UV texture (smart UV project, Cycles EMIT bake, one sample: deterministic). Body 4096 px, smaller parts scaled down.
- **Moving parts as separate meshes in the object's frame** (not at the origin): the engine usually finds a wheel's
  axle from its bounds' centre, so keep each wheel's mesh symmetric about its axle. Name them as the engine expects
  (for example `truck_body`, `wheel_fl`, `wheel_fr`, `wheel_rl`, `wheel_rr`; fl = front left = +Y).
- **Glow** (`--emission`): the bright saturated pixels of the bake as an emission map (lamps, logos). In the engine,
  light it by day too (running lights: Unreal's daylight exposure needs emission in the hundreds to show), more at
  night, and the red lamps brighter when braking (red over green and blue in the same map picks them out).
- **Material slot names** the game code looks for (for example `glass`, `tail_light` for the brake light,
  `dash_screen` for the dash screen): the import script swaps the engine's own materials in by slot name.

## Interiors and windows
A projected model's windows are opaque pictures. If players see the inside (a driver's seat view), split the window
faces into their own slot (glass) by a geometric rule (above the belt line, ahead of the B-pillar...) and add a simple
interior (dash, seats, steering wheel, a screen plane with 0..1 UVs). Expect the outside look of the windows to change
from the reference's (now real glass), and say so.

Seen from the seat, the inside matters as much as the outside view does:
- **The shell's inside**: a projected body is one surface, usually two-sided, so from the cab its inside shows the
  outside's pixels (a van's headlamps glowed under the windscreen). Make the engine material two-sided with
  the back faces a dark lining (Unreal: TwoSidedSign into a lerp).
- **Fit the interior to the shell**: cast rays from inside to find the glass's foot and the walls at each height,
  then sweep the dashboard along the glass, lay door panels a few cm inside the walls, the headliner under the roof.
  Boxes placed by eye poke through the shell or leave gaps.
- **The glass's lower edge** follows the faces the window rule picked: it steps. A dark band just inside its foot
  (a real windscreen's black frit) hides the steps.
- **Live screens**: give each screen face 0..1 UVs and its own slot; the game draws into it (a render target).
- **The steering wheel apart** (the game turns it): its hub's position in the export's frame goes to the game.

## glTF from Blender to Unreal
- Blender +X forward / +Y left / +Z up imports into Unreal with +Y flipped (Unreal's +Y is right); positions in cm.
- Import with an AssetImportTask (Interchange), then set slot materials and the actors' mesh lists in a Python
  commandlet (`UnrealEditor Project.uproject -run=pythonscript -script=abs/path.py -unattended`); the script path
  must be absolute.
- Keep the previous asset and its import script: switching back must be one command.

## Check in the engine, not only in Blender
- Before/after from the same camera; three angles; the driver's (or player's) view if there is one.
- Frame rate from the same view, before and after, read after loading settles (the first seconds spike).
- A moving part's texture turning with it: verify in Blender by rotating the part about its bounds' centre and
  rendering, if the engine view cannot show motion in a still.
