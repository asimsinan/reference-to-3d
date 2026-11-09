"""Prop positions from pixel readings: each entry (photo, (px,py), axis, value) -> the 3D point where the ray meets
world[axis] == value.  uv run --with numpy python measure_props.py"""
import json

import numpy as np

from camlib import load

cams = load()
room = json.load(open('room.json')); W = room['W']

R = {
    # chairs along the left wall (seat centres, plane x = 0.30), from left.jpg and long.jpg
    'chairL1_left': ('left', (590, 1040), 0, 0.30), 'chairL2_left': ('left', (810, 1040), 0, 0.30), 'chairL3_left': ('left', (1030, 1050), 0, 0.30),
    'chairL3_long': ('long', (330, 1370), 0, 0.30), 'chairL2_long': ('long', (200, 1440), 0, 0.30), 'chairL1_long': ('long', (80, 1560), 0, 0.30),
    'chairL_win2': ('win2', (60, 1380), 0, 0.30),
    # chairs along the right wall (plane x = W-0.30)
    'chairR1_right': ('right', (1265, 1080), 0, W - 0.30), 'chairR2_right': ('right', (1470, 1085), 0, W - 0.30), 'chairR3_right': ('right', (1690, 1090), 0, W - 0.30),
    'chairR_long1': ('long', (1080, 1380), 0, W - 0.30), 'chairR_long2': ('long', (1290, 1430), 0, W - 0.30), 'chairR_long3': ('long', (1480, 1530), 0, W - 0.30),
    # coffee table top corners (z = 0.45)
    'ct_far_l_long': ('long', (600, 1580), 2, 0.45), 'ct_far_r_long': ('long', (840, 1580), 2, 0.45),
    'ct_near_l_long': ('long', (530, 2000), 2, 0.45), 'ct_near_r_long': ('long', (880, 2000), 2, 0.45),
    'ct_far_l_win2': ('win2', (435, 1265), 2, 0.45), 'ct_far_r_win2': ('win2', (800, 1262), 2, 0.45),
    'ct_near_l_win2': ('win2', (420, 1600), 2, 0.45), 'ct_near_r_win2': ('win2', (840, 1600), 2, 0.45),
    # return unit (low cabinet) base corners z=0 and top (win2); and from right.jpg its top near corner
    'ru_bl_win2': ('win2', (235, 1600), 2, 0.0), 'ru_br_win2': ('win2', (440, 1590), 2, 0.0),
    'ru_top_l_win2': ('win2', (185, 1150), 2, 0.75), 'ru_top_r_win2': ('win2', (470, 1150), 2, 0.75),
    'ru_top_right_jpg': ('right', (1700, 1345), 2, 0.75),
    # main desk top near corners (z = 0.75) from win2 and win
    'md_near_l_win2': ('win2', (450, 1125), 2, 0.75), 'md_near_r_win2': ('win2', (1100, 1078), 2, 0.75),
    'md_near_l_win': ('win', (500, 1420), 2, 0.75), 'md_near_r_win': ('win', (1536, 1560), 2, 0.75),
    # printer cabinet base (z=0) and top (z=0.75?) from win2; printer top
    'pc_bl_win2': ('win2', (90, 1280), 2, 0.0), 'pc_br_win2': ('win2', (330, 1270), 2, 0.0),
    'pc_top_win2': ('win2', (330, 1140), 2, 0.72),
    # radiator bottom at the wall plane y = 0.12
    'rad_bl_win': ('win', (350, 1620), 1, 0.12), 'rad_br_win': ('win', (590, 1620), 1, 0.12), 'rad_top_win': ('win', (470, 1330), 1, 0.12),
    # office chair floor centre
    'oc_floor_win2': ('win2', (735, 1310), 2, 0.0), 'oc_top_win2': ('win2', (730, 870), 1, 1.7),
    # chair rail on the right wall (plane x = W): top edge ends
    'rail_l_right': ('right', (1120, 905), 0, W), 'rail_r_right': ('right', (1720, 935), 0, W), 'rail_bot_right': ('right', (1400, 950), 0, W),
    # socket on the door wall, switch
    'socket_door': ('door', (830, 1150), 1, room['L']),
    # second light fixture (window side) end seen in win.jpg, ceiling
    'light2_end_win': ('win', (605, 378), 2, room['H']),
    # printer top corners (win): the printer box top
    'printer_top_l_win': ('win', (60, 1300), 2, 1.05), 'printer_top_r_win': ('win', (350, 1300), 2, 1.05),
    # laptop on the desk (win2): base centre at z=0.75
    'laptop_win2': ('win2', (620, 985), 2, 0.75), 'phone_win2': ('win2', (1070, 1050), 2, 0.75), 'cup_win2': ('win2', (880, 1000), 2, 0.75),
    'flower_win2': ('win2', (520, 1300), 2, 0.45), 'clock_win2': ('win2', (560, 1420), 2, 0.45),
}

out = {}
for k, (cam, (px, py), ax, val) in R.items():
    p = cams[cam].hit(px, py, ax, val); out[k] = p.tolist()
    print(f'{k:20s} ({p[0]:6.2f}, {p[1]:6.2f}, {p[2]:5.2f})')
json.dump(out, open('props_measured.json', 'w'), indent=1)
