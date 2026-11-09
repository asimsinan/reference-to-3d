# Default 737-800 parameters (metres), refined against the photo. Reads the solved shape from cam.json.
import json, os
def params(camfile='cam.json'):
    c = json.load(open(camfile)); S = dict(zc=3.0, trk=2.86); S.update(c['shape'])
    zc = S['zc']
    P = dict(X0=19.735, L=39.47, zc=zc, fus_a=1.88, fus_b=2.0, fus_n=64, fus_flat=0.25,
             nose_len=6.2, nose_pow=2.6, nose_top_pow=2.0, nose_bot_pow=3.2, nose_tip_dz=-0.55,
             tail_w_start=27.0, tail_w_pow=1.6, tail_top_start=30.0, tail_top_pow=1.7,
             tail_bot_start=24.0, tail_bot_pow=1.2, tail_end_a=0.32, tail_end_z=zc + 0.9, tail_end_h=0.32)
    P['wing'] = dict(y_root=1.6, y_glove=2.6, y_kink=6.3, y_tip=S['y_wt'] - 0.9, s_le_root=12.6, s_le_glove=13.4,
                     sweep_le=27.0, s_te_root=20.0, s_te_kink=20.3, c_tip=1.3, dihedral=6.0,
                     z_root=zc - 1.45, t_root=0.14, t_tip=0.10, wl_radius=0.9, wl_cant=10.0, wl_sweep=50.0,
                     wl_c_root=1.15, wl_c_tip=0.55, wl_len=1.7, ftf_y=[3.4, 7.1, 9.1], ftf_len=3.0)
    P['htail'] = dict(y_root=0.9, y_tip=7.17, s_le_root=33.2, sweep_le=33.0, c_root=4.3, c_tip=1.25,
                      dihedral=7.0, z_root=zc + 0.6)
    P['fin'] = dict(z_root=zc + 1.75, z_top=12.55, s_le_root=29.6, sweep_le=37.0, c_root=6.6, c_top=S['c_fin'],
                    dorsal_s0=25.5, dorsal_h=1.6, dorsal_pow=2.2)
    P['eng'] = dict(s_front=S['s_e'] - 0.1, len=4.0, r_out=1.03, r_lip_in=0.83, r_fan=0.78, y=S['y_e'],
                    z=S['z_e'], flat_bot=0.88, wscale=1.0, pylon_ztop=zc - 1.0)
    P['gear'] = dict(s_nose=S['s_ng'], r_nose=0.34, s_main=S['s_mg'], r_main=0.56, track=S['trk'])
    P['belly'] = dict(s0=11.0, s1=24.5, w=1.08, drop=0.25)
    if os.path.exists('tweaks.json'):
        T = json.load(open('tweaks.json'))
        for k, v in T.items():
            if isinstance(v, dict): P[k].update(v)
            else: P[k] = v
    return P
