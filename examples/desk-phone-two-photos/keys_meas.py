"""Front photo: each key's top edge, top-face/front-face boundary and bottom edge along its centre column -> keys_meas.json.
The key centres (cx, cy) are this photo's, read on a grid (grid.py)."""
import cv2, numpy as np, json
g=cv2.cvtColor(cv2.imread('ref.jpg'),cv2.COLOR_BGR2GRAY).astype(np.float32); g=cv2.GaussianBlur(g,(0,0),1.0)
keys=[[741,1042],[843,1047],[944,1050],[742,1086],[848,1090],[954,1093],[745,1131],[855,1133],[963,1137],[748,1178],[860,1180],[973,1182]]
out=[]
for (cx,cy) in keys:
    y0=cy-35; col=g[y0:cy+45, cx-8:cx+9].mean(1); d=np.diff(col)
    top=np.argmin(d[:40])+y0+.5; bot=np.argmax(d[20:])+20+y0+.5
    k=int(top-y0)+5; seg=col[k:int(bot-y0)]
    ff=np.argmax(seg<14)+k+y0 if (seg<14).any() else np.nan
    out.append([cx,cy,float(top),float(ff),float(bot)])
json.dump(out,open('keys_meas.json','w'))
