"""peaks.py IMG row|col IDX A B [n]  -- strongest gradient peaks along a row (x in [A,B]) or column (y in [A,B]); subpixel, signed."""
import sys, cv2, numpy as np
im=cv2.imread(sys.argv[1]).astype(np.float32); g=cv2.GaussianBlur(im,(0,0),1.0).mean(2)
mode,i,a,b=sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]); n=int(sys.argv[6]) if len(sys.argv)>6 else 5
if mode=='row': s=g[i-1:i+2,:].mean(0)
else: s=g[:,i-1:i+2].mean(1)
d=np.gradient(s); out=[]
for k in range(max(a,1),min(b,len(s)-2)):
    if abs(d[k])>=abs(d[k-1]) and abs(d[k])>abs(d[k+1]):
        den=abs(d[k-1])-2*abs(d[k])+abs(d[k+1]); off=0.5*(abs(d[k-1])-abs(d[k+1]))/den if den!=0 else 0
        out.append((abs(d[k]),k+off,d[k]))
out.sort(reverse=True)
print(mode,i,' '.join('%.1f(%+.0f)'%(p,v) for _,p,v in sorted(out[:n],key=lambda t:t[1])))
