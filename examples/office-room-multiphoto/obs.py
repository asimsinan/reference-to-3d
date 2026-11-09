"""Hand-read pixel observations (full-res) of structural points in each photo.

Room frame: x across (0 = recessed face of the left wall, W = right wall), y along (0 = window wall, L = door wall),
z up (0 floor, H ceiling).  Left wall (as seen from the window end looking at the door): recessed main face x=0;
a chase at the window end (x 0..d, y 0..r0, full height), a beam along the top (x 0..d, z rz..H), a pilaster at the
door end (x 0..d2, y L-p..L, full height).
"""
import numpy as np

# parameter names and initial values
P0 = dict(W=3.2, L=6.0, H=2.9, d=0.16, d2=0.26, r0=1.6, rz=2.35, p=0.28,
          dx0=0.50, dx1=1.50,                       # door frame outer x
          xA0=3.1, xA1=2.3, xB0=1.8, xB1=0.95,      # window frame x (A near the right wall)
          zs=0.95, zb=2.1, zc=2.6,                  # sill, blind top, conduit
          tcd=0.42, tc0=4.4, tcw=0.8, tch=1.95,     # tall cabinet (right wall, near the door)
          bd=0.40, b0=3.4, bw=0.8, bh=1.9,          # bookcase (right wall)
          xl=1.6, yl0=3.2, yl1=4.4,
          tx0=1.2, tx1=1.7, ty0=2.0, ty1=2.8, tz=0.45,     # coffee table top
          ry0=1.5, ry1=3.1, rzt=0.95, rzb=0.80,
          xa=1.9, yf=1.6, yb=0.9, zd=0.75)                 # main desk: x-max end, front/back edge y, top            # wooden rail on the right wall                 # light fixture ends on the ceiling
DH = 2.12   # door frame outer height: the scale


def points(P):
    W, L, H, d, d2, r0, rz, p = (P[k] for k in 'W L H d d2 r0 rz p'.split())
    pt = {
        'F1': (P['dx0'], L, DH), 'F2': (P['dx1'], L, DH), 'F3': (P['dx0'], L, 0), 'F4': (P['dx1'], L, 0),
        'CR': (W, L, H), 'FR': (W, L, 0),
        'PE_tl': (d, L - p, H), 'PE_tr': (d2, L - p, H),       # pilaster end face above the beam (x d..d2)
        'PE_m': (0, L - p, rz), 'PE_md': (d, L - p, rz), 'PE_mr': (d2, L - p, rz),
        'PE_bl': (0, L - p, 0), 'PE_br': (d2, L - p, 0),
        'PI_b': (d2, L, 0), 'PI_t': (d2, L, H),
        'CH_m': (d, r0, rz), 'CH_b': (d, r0, 0), 'CH_t': (d, r0, H),
        'WC_R': (W, 0, H), 'WC_L': (d, 0, H),
        'WK_R': (W, 0, P['zc']), 'WK_L': (d, 0, P['zc']),
        'SA0': (P['xA0'], 0, P['zs']), 'SA1': (P['xA1'], 0, P['zs']), 'SB0': (P['xB0'], 0, P['zs']), 'SB1': (P['xB1'], 0, P['zs']),
        'BA0': (P['xA0'], 0, P['zb']), 'BA1': (P['xA1'], 0, P['zb']), 'BB0': (P['xB0'], 0, P['zb']), 'BB1': (P['xB1'], 0, P['zb']),
        'TC1': (W - P['tcd'], P['tc0'], P['tch']), 'TC2': (W - P['tcd'], P['tc0'] + P['tcw'], P['tch']),
        'TC3': (W - P['tcd'], P['tc0'], 0), 'TC4': (W - P['tcd'], P['tc0'] + P['tcw'], 0), 'TC5': (W, P['tc0'], P['tch']),
        'BC1': (W - P['bd'], P['b0'], P['bh']), 'BC2': (W - P['bd'], P['b0'] + P['bw'], P['bh']),
        'BC3': (W - P['bd'], P['b0'], 0), 'BC4': (W - P['bd'], P['b0'] + P['bw'], 0), 'BC5': (W, P['b0'], P['bh']),
        'LT0': (P['xl'], P['yl0'], H), 'LT1': (P['xl'], P['yl1'], H),
        'T00': (P['tx0'], P['ty0'], P['tz']), 'T10': (P['tx1'], P['ty0'], P['tz']),
        'T01': (P['tx0'], P['ty1'], P['tz']), 'T11': (P['tx1'], P['ty1'], P['tz']),
        'R1t': (W - 0.02, P['ry1'], P['rzt']), 'R0t': (W - 0.02, P['ry0'], P['rzt']),
        'R1b': (W - 0.02, P['ry1'], P['rzb']), 'R0b': (W - 0.02, P['ry0'], P['rzb']),
        'DAF': (P['xa'], P['yf'], P['zd']), 'DAB': (P['xa'], P['yb'], P['zd']),
    }
    return {k: np.array(v, float) for k, v in pt.items()}


# image sizes
SIZE = {'door': (1536, 2048), 'long': (1536, 2048), 'win': (1536, 2048), 'win2': (1536, 2048),
        'left': (2048, 1536), 'right': (2048, 1536)}

OBS = {
    'door': {
        'R1t': (1458, 1491),
        'F1': (318, 832), 'F2': (690, 832), 'F3': (318, 1620), 'F4': (690, 1618), 'CR': (1198, 590),
        'PE_tl': (237, 537), 'PE_tr': (267, 537), 'PE_m': (190, 722), 'PE_md': (237, 722),
        'PE_bl': (190, 1654), 'PE_br': (272, 1654),
        'BC1': (1200, 898), 'BC5': (1420, 902), 'BC2': (1097, 912),
                'LT0': (765, 345), 'LT1': (765, 535),
    },
    'long': {
        'T01': (612, 1583), 'T11': (847, 1583), 'R1t': (1164, 1228),
        'F1': (584, 915), 'F2': (766, 913), 'F3': (584, 1277), 'F4': (766, 1277),
        'PE_bl': (526, 1300), 'PE_br': (562, 1297), 'PE_m': (526, 865), 'PE_md': (543, 865), 'PE_mr': (560, 865),
        'PE_tl': (543, 780), 'PE_tr': (557, 780), 'CH_m': (248, 716),
        'BC1': (1025, 920), 'BC5': (1140, 918), 'BC2': (955, 942),
        'LT0': (775, 632), 'LT1': (790, 752),
    },
    'win': {
        'DAF': (419, 1861), 'DAB': (481, 1648),
        'WC_R': (118, 468), 'WC_L': (1195, 497),
        'SA0': (100, 1262), 'SA1': (478, 1262), 'SB0': (690, 1262), 'SB1': (1110, 1262),
        'BA0': (100, 715), 'BA1': (478, 715), 'BB0': (690, 715), 'BB1': (1110, 715),
    },
    'win2': {
        'DAF': (522, 1117), 'DAB': (537, 1066),
        'T10': (503, 1359), 'T00': (800, 1359), 'T11': (432, 1612), 'T01': (840, 1604),
        'WC_R': (72, 88), 'WC_L': (1175, 90),
        'SA0': (110, 880), 'SA1': (480, 880), 'SB0': (695, 880), 'SB1': (1100, 880),
        'BA0': (110, 322), 'BA1': (480, 322), 'BB0': (695, 322), 'BB1': (1100, 322),
    },
    'left': {
        'T01': (723, 1281),
        'CH_m': (960, 300), 'CH_b': (958, 1150),
        'PE_bl': (1770, 1140), 'PE_br': (1835, 1190), 'PI_b': (1995, 1192),
        'PE_m': (1915, 262), 'PE_mr': (1955, 258),
    },
    'right': {
        'T11': (1712, 1357), 'R1t': (1125, 901), 'R0t': (1740, 903), 'R1b': (1125, 957), 'R0b': (1740, 951),
        'FR': (398, 1195),
        'TC2': (485, 520), 'TC1': (690, 522), 'TC4': (482, 1250), 'TC3': (690, 1250), 'TC5': (742, 538),
        'BC2': (740, 500), 'BC1': (1085, 500), 'BC4': (740, 1262), 'BC3': (1085, 1262),
    },
}

# initial camera guesses: position, (yaw deg: direction of view in the xy plane, 0 = +x, 90 = +y), pitch down deg, f
CAM0 = {
    'door': ((1.8, 1.5, 1.45), 90, 1, 1500),
    'long': ((1.4, 0.5, 1.5), 90, 2, 880),
    'win': ((1.8, 3.8, 1.45), -90, 2, 1500),
    'win2': ((1.6, 5.3, 1.45), -90, 2, 1500),
    'left': ((2.6, 3.0, 1.6), 180, 10, 840),
    'right': ((0.6, 1.8, 1.5), 25, 8, 840),
}
