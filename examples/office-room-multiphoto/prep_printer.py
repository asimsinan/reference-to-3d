"""Printer faces by 4-point homography from the close-up photos (ek6 front, ek5 side)."""
import cv2, numpy as np
def rect(img, pts, wm, hm, ppm, out):
    W, H = int(wm * ppm), int(hm * ppm)
    Hm = cv2.getPerspectiveTransform(np.float32(pts), np.float32([(0, 0), (W, 0), (W, H), (0, H)]))
    cv2.imwrite(out, cv2.warpPerspective(img, Hm, (W, H), flags=cv2.INTER_CUBIC), [cv2.IMWRITE_JPEG_QUALITY, 93])
f, s = cv2.imread('ek6.jpg'), cv2.imread('ek5.jpg')
# front (TL, TR, BR, BL): base z 0..0.235, bay band 0.235..0.36, scanner strip, ADF front, control panel
rect(f, [(228, 1250), (1236, 1250), (1213, 1843), (225, 1845)], 0.43, 0.235, 1200, 'tex/pr_front_base.jpg')
rect(f, [(245, 935), (1250, 940), (1236, 1250), (228, 1250)], 0.43, 0.125, 1200, 'tex/pr_front_bay.jpg')
rect(f, [(565, 935), (1125, 937), (1125, 1080), (560, 1080)], 0.235, 0.075, 1600, 'tex/pr_panel.jpg')
rect(f, [(245, 900), (1150, 905), (1150, 937), (245, 935)], 0.43, 0.035, 1200, 'tex/pr_front_scan.jpg')
rect(f, [(240, 620), (1150, 620), (1150, 900), (240, 900)], 0.43, 0.10, 1200, 'tex/pr_front_adf.jpg')
# side facing the door (+y): body z 0..0.36 and the scanner/ADF unit 0.36..0.49
rect(s, [(245, 1075), (1255, 1075), (1255, 1800), (250, 1800)], 0.484, 0.36, 1000, 'tex/pr_side_body.jpg')
rect(s, [(215, 700), (1060, 700), (1060, 1060), (215, 1060)], 0.47, 0.13, 1000, 'tex/pr_side_top.jpg')
print('ok')
# white plastic of every face to the same albedo (the photos were lit very differently face to face)
import glob
for fn in glob.glob('tex/pr_*.jpg'):
    im = cv2.imread(fn).astype(np.float32); lum = im.mean(2)
    ref = np.percentile(lum, 88)
    im *= 226.0 / max(ref, 1)
    im = np.clip(im, 0, 255)
    cv2.imwrite(fn, im.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 93]); print(fn, round(226 / ref, 2))
