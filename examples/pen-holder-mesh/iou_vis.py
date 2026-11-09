import cv2, numpy as np, sys
out=sys.argv[1]; sil=cv2.imread('mask_photo.png',0)>0
hm=cv2.imread(f'{out}/holder_mask.png',cv2.IMREAD_UNCHANGED)[...,3]>127; hm[:888]=False
vis=cv2.imread('photo.jpg')//2
vis[sil&~hm]=(0,0,255); vis[hm&~sil]=(0,255,0); vis[sil&hm]=(0,200,200)
print('photo-only px',(sil&~hm).sum(),'render-only px',(hm&~sil).sum(),'both',(sil&hm).sum())
cv2.imwrite(f'{out}/iou_vis.jpg',vis[840:1640,540:1160])
