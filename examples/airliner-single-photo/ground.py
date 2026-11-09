# Rectify the photo's ground plane (z=0) to a top view; build a seamless concrete tile from a sunlit patch.
import cv2, numpy as np, json
cam = json.load(open('cam.json')); Rm = np.array(cam['R']); C = np.array(cam['C']); f = cam['f']; W, H = cam['W'], cam['H']
ref = cv2.imread('ref.jpg').astype(np.float32)
res = 0.05; xs = np.arange(60, -120, -res); ys = np.arange(80, -80, -res)   # rows: x (front at top), cols: y (left at left)
X, Y = np.meshgrid(xs, ys, indexing='ij'); P = np.stack([X, Y, np.zeros_like(X)], -1).reshape(-1, 3)
pc = (P - C) @ Rm.T; u = f * pc[:, 0] / pc[:, 2] + W / 2; v = f * pc[:, 1] / pc[:, 2] + H / 2
ok = (pc[:, 2] > 0) & (u >= 0) & (u < W) & (v >= 640) & (v < H)
top = cv2.remap(ref, u.reshape(X.shape).astype(np.float32), v.reshape(X.shape).astype(np.float32), cv2.INTER_LINEAR)
top[~ok.reshape(X.shape)] = 0
cv2.imwrite('ground_top.jpg', cv2.resize(top, None, fx=0.25, fy=0.25))
np.save('ground_uv.npy', np.stack([u.reshape(X.shape), v.reshape(X.shape)], -1).astype(np.float32))
json.dump({'res': res, 'x0': 60, 'y0': 80}, open('ground_top.json', 'w'))
