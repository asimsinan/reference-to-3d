"""mean sRGB of the same boxes in the photo and a render (both 1000x1000 from the photo's camera)"""
import cv2, numpy as np, sys
ref=cv2.imread('ref.jpg').astype(float); r=cv2.imread(sys.argv[1]).astype(float)
if r.shape[0]!=1000: r=cv2.resize(r,(1000,1000),interpolation=cv2.INTER_AREA)
B={'top near':(300,412,420,428),'top far':(600,330,700,350),'short apron':(300,470,460,495),'long apron':(600,420,700,440),
   'leg B':(495,600,520,800),'leg A':(252,600,276,800),'S1 cushion':(660,600,800,650),'S1 tray':(640,672,780,695),'S1 leg':(775,760,790,900),
   'bench cushion':(110,545,230,565),'S2 cushion':(760,510,880,550),'cup2':(548,370,560,390),'candle':(625,310,655,325),
   'sphere':(580,290,610,315),'plate':(510,348,580,354),'floor':(300,880,450,960)}
tot=[]
for k,(x0,y0,x1,y1) in B.items():
    a=ref[y0:y1,x0:x1].reshape(-1,3).mean(0)[::-1]; b=r[y0:y1,x0:x1].reshape(-1,3).mean(0)[::-1]; tot.append(np.abs(a-b).mean())
    print('%-14s photo %s  render %s  ratio %s'%(k,np.round(a).astype(int),np.round(b).astype(int),np.round(b/np.maximum(a,1),2)))
print('mean abs diff over boxes %.1f'%np.mean(tot))
