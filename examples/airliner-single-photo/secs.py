# Pure-python section definitions (no bpy) shared by geom.py and the numpy fitters.
import math
from mathutils_lite import Vector
def lerp(a, b, t): return a + (b - a) * t
def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)


# ---------------- fuselage ----------------
def fus_section(s, P):
    """returns (half_width, z_top, z_bot) at station s."""
    L, zc, R, Hh = P['L'], P['zc'], P['fus_a'], P['fus_b']
    Ln = P['nose_len']
    if s < Ln:
        t = s / Ln
        k = (1 - (1 - t) ** P['nose_pow']) ** 0.5
        a = R * k
        # nose: lower centre line, cockpit top
        ztop = zc + lerp(P['nose_tip_dz'], Hh, (1 - (1 - t) ** P['nose_top_pow']) ** 0.5)
        zbot = zc + lerp(P['nose_tip_dz'], -Hh, (1 - (1 - t) ** P['nose_bot_pow']) ** 0.5)
        return a, ztop, zbot
    ts0, tb0 = P['tail_top_start'], P['tail_bot_start']
    a = R; ztop = zc + Hh; zbot = zc - Hh
    if s > P['tail_w_start']:
        t = (s - P['tail_w_start']) / (L - P['tail_w_start'])
        a = lerp(R, P['tail_end_a'], t ** P['tail_w_pow'])
    if s > ts0:
        t = (s - ts0) / (L - ts0)
        ztop = lerp(zc + Hh, P['tail_end_z'] + P['tail_end_h'], t ** P['tail_top_pow'])
    if s > tb0:
        t = (s - tb0) / (L - tb0)
        zbot = lerp(zc - Hh, P['tail_end_z'] - P['tail_end_h'], t ** P['tail_bot_pow'])
    return a, ztop, zbot

def ring_xyz(X, a, ztop, zbot, n=64, flat=0.0):
    pts = []
    zm, h = (ztop + zbot) / 2, (ztop - zbot) / 2
    for i in range(n):
        th = 2 * math.pi * i / n
        c, s_ = math.cos(th), math.sin(th)
        # superellipse-ish: slightly squarer sides
        e = 2.0 / (2.0 + flat)
        cy = math.copysign(abs(c) ** e, c); sz = math.copysign(abs(s_) ** e, s_)
        pts.append((X, a * cy, zm + h * sz))
    return pts

def fuselage_rings(P):
    X0 = P['X0']; L = P['L']
    st = [0.0, 0.03, 0.08, 0.15, 0.25, 0.4, 0.6, 0.85, 1.1, 1.4, 1.8, 2.2, 2.7, 3.2, 3.8, 4.4, 5.0, 5.6, 6.2]
    s = 7.0
    while s < L - 0.01:
        st.append(s); s += 1.0 if s < P['tail_w_start'] - 1 else 0.5
    st.append(L)
    rings = []
    for s in st:
        a, zt, zb = fus_section(s, P)
        a = max(a, 0.004); h = max((zt - zb) / 2, 0.004)
        rings.append(ring_xyz(X0 - s, a, (zt + zb) / 2 + h, (zt + zb) / 2 - h, P['fus_n'], P['fus_flat']))
    return rings

def fin_secs(P):
    F = P['fin']; X0 = P['X0']; secs = []
    zr, zt = F['z_root'], F['z_top']; tn = math.tan(math.radians(F['sweep_le']))
    s_lin0 = F['s_le_root']
    zs = [zr + d for d in (0, 0.05, 0.12, 0.22, 0.35, 0.5, 0.7, 0.95)] + [lerp(zr, zt, f) for f in (0.15, 0.25, 0.4, 0.55, 0.7, 0.85, 0.95, 1.0)]
    zs = sorted(set(round(z, 4) for z in zs))
    for z in zs:
        s_lin = s_lin0 + (z - zr) * tn
        s_te = s_lin0 + F['c_root'] + (z - zr) * (tn - (F['c_root'] - F['c_top']) / (zt - zr))
        u = max(0.0, 1 - (z - zr) / F['dorsal_h'])
        s_le = s_lin - (s_lin0 - F['dorsal_s0']) * u ** F['dorsal_pow']
        c = s_te - s_le
        f = (z - zr) / (zt - zr)
        t = lerp(0.12, 0.09, f) * (F['c_root'] / c) * (1 + 0.6 * u)
        secs.append(dict(le=(X0 - s_le, 0, z), chord=c, t=min(t, 0.2), up=(0, 1, 0)))
    return secs

def wing_secs(P, side):
    W = P['wing']; X0 = P['X0']; sg = 1 if side == 'L' else -1
    dih = math.radians(W['dihedral'])
    def le_at(y):
        # LE station: inner glove then swept
        if y <= W['y_glove']:
            s = lerp(W['s_le_root'], W['s_le_glove'], (y - W['y_root']) / (W['y_glove'] - W['y_root']))
        else:
            s = W['s_le_glove'] + (y - W['y_glove']) * math.tan(math.radians(W['sweep_le']))
        return s
    def te_at(y):
        if y <= W['y_kink']:
            return lerp(W['s_te_root'], W['s_te_kink'], (y - W['y_root']) / (W['y_kink'] - W['y_root']))
        return lerp(W['s_te_kink'], le_at(W['y_tip']) + W['c_tip'], (y - W['y_kink']) / (W['y_tip'] - W['y_kink']))
    ys = [W['y_root'], W['y_root'] + 0.6, W['y_glove'], (W['y_glove'] + W['y_kink']) / 2, W['y_kink']]
    k = W['y_kink']
    while k < W['y_tip'] - 0.5:
        k += 1.2; ys.append(min(k, W['y_tip']))
    if ys[-1] != W['y_tip']: ys.append(W['y_tip'])
    secs = []
    up = Vector((0, -sg * math.sin(dih), math.cos(dih)))
    for y in ys:
        s_le = le_at(y); c = te_at(y) - s_le
        z = W['z_root'] + (y - W['y_root']) * math.tan(dih)
        f = (y - W['y_root']) / (W['y_tip'] - W['y_root'])
        secs.append(dict(le=(X0 - s_le, sg * y, z), chord=c, t=lerp(W['t_root'], W['t_tip'], f),
                         camber=0.02, up=tuple(up)))
    # blended winglet: arc up then straight blade
    tip = secs[-1]; yt, zt0 = W['y_tip'], secs[-1]['le'][2]
    s_tip = le_at(yt); r = W['wl_radius']; cant = math.radians(W['wl_cant'])
    for i in range(1, 7):
        a = (math.pi / 2 - cant) * i / 6
        y = yt + r * math.sin(a); z = zt0 + r * (1 - math.cos(a))
        c = lerp(W['c_tip'], W['wl_c_root'], i / 6)
        s_le = s_tip + (r * a) * math.tan(math.radians(W['wl_sweep'] * 0.7))
        upv = Vector((0, -sg * math.sin(a + dih * (1 - i / 6)), math.cos(a + dih * (1 - i / 6))))
        secs.append(dict(le=(X0 - s_le, sg * y, z), chord=c, t=0.09, camber=0.0, up=tuple(upv)))
    # straight blade
    a = math.pi / 2 - cant
    y0, z0, s0 = secs[-1]['le'][1] * sg, secs[-1]['le'][2], X0 - secs[-1]['le'][0]
    for i in range(1, 5):
        l = W['wl_len'] * i / 4
        y = y0 + l * math.cos(a); z = z0 + l * math.sin(a)
        s_le = s0 + l * math.tan(math.radians(W['wl_sweep']))
        c = lerp(W['wl_c_root'], W['wl_c_tip'], i / 4)
        upv = Vector((0, -sg * math.sin(a), math.cos(a)))
        secs.append(dict(le=(X0 - s_le, sg * y, z), chord=c, t=0.08, camber=0.0, up=tuple(upv)))
    return secs

def htail_secs(P, side):
    T = P['htail']; X0 = P['X0']; sg = 1 if side == 'L' else -1
    dih = math.radians(T['dihedral']); up = Vector((0, -sg * math.sin(dih), math.cos(dih)))
    secs = []
    for f in (0, 0.25, 0.5, 0.75, 0.93, 1.0):
        y = lerp(T['y_root'], T['y_tip'], f)
        s_le = T['s_le_root'] + (y - T['y_root']) * math.tan(math.radians(T['sweep_le']))
        c = lerp(T['c_root'], T['c_tip'], f)
        if f == 1.0: c *= 0.75; s_le += 0.12
        z = T['z_root'] + (y - T['y_root']) * math.tan(dih)
        secs.append(dict(le=(X0 - s_le, sg * y, z), chord=c, t=lerp(T.get('t_root', 0.11), T.get('t_tip', 0.09), f), up=tuple(up)))
    return secs

