"""ISO Turkish-Q MacBook Pro 14 key layout fitted to the rectified deck texture -> keys.json (rects in texture px)."""
import cv2, json, numpy as np, sys
L,R,TOP,P=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4])  # left/right key edges, top gap centre, row pitch
G=float(sys.argv[5])   # gap between caps (px)
u=(R-L)/14.5
rows=[[1.5]+[1]*13,
      [1]*13+[1.5],
      [1.5]+[1]*12+['RET_TOP'],
      [1.75]+[1]*12+['RET_LOW'],
      [1.25]+[1]*11+[2.25],
      [1,1,1,1.25,5,1.25,1,'LEFT','UPDOWN','RIGHT']]
keys=[]
for r,row in enumerate(rows):
    y0=TOP+r*P+G/2; y1=TOP+(r+1)*P-G/2; x=L
    for w in row:
        if w=='RET_TOP':
            keys.append([x+G/2,y0,R-G/2,y1+G]); x=R; continue      # ISO return, upper part (bridges the gap to the lower part)
        if w=='RET_LOW':
            keys.append([x+G/2,y0-G,R-G/2,y1]); x=R; continue
        if w in('LEFT','RIGHT'):
            keys.append([x+G/2,(y0+y1)/2+G/4,x+u-G/2,y1]); x+=u; continue
        if w=='UPDOWN':
            ym=(y0+y1)/2
            keys.append([x+G/2,y0,x+u-G/2,ym-G/4]); keys.append([x+G/2,ym+G/4,x+u-G/2,y1]); x+=u; continue
        keys.append([x+G/2,y0,x+w*u-G/2,y1]); x+=w*u
json.dump(keys,open('keys.json','w'))
t=cv2.imread('tex/deck.png')
for k in keys: cv2.rectangle(t,(int(k[0]),int(k[1])),(int(k[2]),int(k[3])),(0,255,0),2)
cv2.imwrite('keys_fit.jpg',t[0:820,0:1875]); print(len(keys),'u=%.1f'%u)
