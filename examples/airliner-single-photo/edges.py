import cv2, numpy as np, json
from scipy.signal import medfilt
m = cv2.imread('mask_gc.png',0)
xs = np.arange(330, 951); top=[]
for x in xs:
    col = np.where(m[450:900, x] > 0)[0]
    top.append(450+col[0] if len(col) else np.nan)
top = medfilt(np.array(top,float), 15)
# sub-pixel refine with luminance gradient
g = cv2.cvtColor(cv2.imread('ref.jpg'), cv2.COLOR_BGR2GRAY).astype(float)
g = cv2.GaussianBlur(g,(0,0),1.0)
ref=[]
for x,t in zip(xs,top):
    t=int(t); seg = g[t-6:t+7, x]; d = np.diff(seg)
    k = np.argmax(d); ref.append(t-6+k+0.5)
ref = medfilt(np.array(ref),9)
bot_pts = [(300,872),(350,865),(400,857),(450,849),(500,842),(550,836),(600,830)]
json.dump({'top':[[int(x),float(y)] for x,y in zip(xs,ref)], 'bottom':bot_pts}, open('edges.json','w'))
print(ref[::50])
