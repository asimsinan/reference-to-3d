# Ground albedo colour: photo's sunlit+shadowed concrete divided by the irradiance a 0.5-grey ground receives.
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import cv2, numpy as np, json
S = cv2.imread('pass_sunpass.exr', cv2.IMREAD_UNCHANGED); KL = cv2.imread('pass_skylow.exr', cv2.IMREAD_UNCHANGED); KH = cv2.imread('pass_skyhigh.exr', cv2.IMREAD_UNCHANGED)
h, w = S.shape[:2]; cal = json.load(open('calib.json'))
sun = cal['sun'] * np.array(cal['sun_color'])[::-1]; lo = np.array(cal['sky_low'])[::-1]; hi = np.array(cal['sky_high'])[::-1]
ref = cv2.resize(cv2.imread('ref.jpg'), (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
ref = np.where(ref <= 0.04045, ref / 12.92, ((ref + 0.055) / 1.055) ** 2.4)
alpha = cv2.resize(cv2.imread('out_match.png', cv2.IMREAD_UNCHANGED)[..., 3], (w, h)) > 10
grd = np.zeros((h, w), bool); grd[int(h * 0.62):, :] = True; grd &= ~(cv2.dilate(alpha.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0)
F = cv2.imread('fills/fill_25_240_.exr', cv2.IMREAD_UNCHANGED); fl = np.array(cal.get('fill', [0, 0, 0]))[::-1]
irr = (S[..., :3] * sun + KL[..., :3] * lo + KH[..., :3] * hi + F[..., :3] * fl) / 0.5
tile = cv2.imread('tex/ground_tile.png').astype(np.float32) / 255
tile = np.where(tile <= 0.04045, tile / 12.92, ((tile + 0.055) / 1.055) ** 2.4).reshape(-1, 3).mean(0)
alb = np.array([np.sum(ref[grd][:, c] * irr[grd][:, c]) / np.sum(irr[grd][:, c] ** 2) for c in range(3)])
gain = alb / tile
print('ground albedo (RGB)', alb[::-1].round(3), 'tile', tile[::-1].round(3), 'gain', gain[::-1].round(3))
cal['ground_gain'] = gain[::-1].tolist(); json.dump(cal, open('calib.json', 'w'), indent=1)
