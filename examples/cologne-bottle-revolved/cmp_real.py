"""Photo vs the real-material render from the photo's camera (full frame: the backdrop is the photo). Prints the
means of label/cap/collar boxes in both, writes OUTDIR/compare.jpg"""
import sys,numpy as np,cv2
out=sys.argv[1]; ph=cv2.imread('photo.jpg').astype(float); r=cv2.imread(f'{out}/photo_view.png').astype(float)
REG=dict(label_L=(640,1050,700,1150),label_C=(740,1250,820,1350),label_R=(860,1050,920,1150),yellow=(700,1430,860,1510),cap=(740,500,870,650),collar=(700,740,880,840),clear=(650,900,760,970),table=(1100,1500,1400,1700))
for nm,(x0,y0,x1,y1) in REG.items():
    a=ph[y0:y1,x0:x1].reshape(-1,3).mean(0)[::-1]; b=r[y0:y1,x0:x1].reshape(-1,3).mean(0)[::-1]
    print('%-8s photo %s  render %s  diff %+.0f'%(nm,np.round(a).astype(int),np.round(b).astype(int),(b-a).mean()))
d=np.abs(r-ph).mean(2); m=cv2.imread('model_mask.png',0)>0
print('mean |diff| over model %.1f'%d[m].mean())
crop=lambda x: x[430:1710,560:1020]
cv2.imwrite(f'{out}/compare.jpg',cv2.resize(np.hstack([crop(ph),crop(r),np.repeat(np.clip(crop(d)*3,0,255)[...,None],3,2)]).astype(np.uint8),None,fx=0.6,fy=0.6))
