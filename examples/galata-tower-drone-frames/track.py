"""track.py IMG side x0 y0 y1 [win] -> silhouette x per row, following max |gx| from seed (x0,y0)."""
import sys, cv2, numpy as np, json
im=cv2.imread(sys.argv[1]).astype(np.float32); g=cv2.GaussianBlur(im,(0,0),1.0)
gx=np.abs(cv2.Sobel(g,cv2.CV_32F,1,0,ksize=3)).sum(2)
side=sys.argv[2]; x=float(sys.argv[3]); y0,y1=int(sys.argv[4]),int(sys.argv[5]); w=int(sys.argv[6]) if len(sys.argv)>6 else 2
out=[]; step=1 if y1>y0 else -1
for y in range(y0,y1,step):
    xi=int(round(x)); seg=gx[y,xi-w:xi+w+1]; j=int(np.argmax(seg)); xn=xi-w+j
    if 0<j<2*w:
        a,b,c=seg[j-1],seg[j],seg[j+1]; den=a-2*b+c; xn+= 0.5*(a-c)/den if den!=0 else 0
    out.append((round(float(xn),1),y,round(float(seg.max()),0))); x=xn
print(json.dumps(out))
