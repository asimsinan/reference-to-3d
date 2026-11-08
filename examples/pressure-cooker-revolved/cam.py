"""The photo's camera, solved by hand from the ellipses of two horizontal circles (see README / the reference).

Object frame: +X front (towards the camera), +Y the object's left (= the image's right), +Z up, metres.
A level camera at (D, 0, HC) looking along -X, focal length F px, principal point (CX, CY) in image pixels
(v down). A level camera keeps the photo's verticals vertical; an off-centre crop is the principal point.

How the numbers were found (this photo: 554 x 554, a pot ~27 cm wide):
  scale at the axis plane k = F/D = 1000 px/m (pot radius 0.133 m = 133 px)
  base circle (r 0.112, z 0):    front point 23 px below the side points -> HC/(D-0.112) = 0.205
  lid flange (r 0.146, z 0.217): front point  8 px below the side points -> (HC-0.217)/(D-0.145) = 0.055
  -> D = 1.55, HC = 0.295, F = 1550; CX = the axis' column, CY from v(z=0, x=0) = CY + k*HC = 402.
"""
D=1.55; HC=0.295; F=1550.0; CX=233.0; CY=107.0; W=H=554

def proj(x,y,z):
    """object point -> image (u, v)"""
    d=D-x; return CX+F*y/d, CY-F*(z-HC)/d

def unproj0(u,v):
    """image (u, v) -> (y, z) on the plane x = 0 (the plane of the axis, where side handles sit)"""
    return (u-CX)*D/F, HC-(v-CY)*D/F

def blender_shift():
    """Blender camera shift for the principal point (sensor_fit HORIZONTAL, units of the image width).
    The sign is easy to get wrong: a principal point left of / above the centre needs shift_x > 0 / shift_y < 0."""
    return -(CX-W/2)/W, (CY-H/2)/W
