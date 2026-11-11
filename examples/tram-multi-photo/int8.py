import cv2,numpy as np,sys
ph=cv2.imread('ref2/p8.png').astype(np.float32); r=cv2.imread('out/real34_8.png',cv2.IMREAD_UNCHANGED).astype(np.float32); a=r[...,3:]/255.
c=r[...,:3]*a+ph*(1-a)
B={'ceiling':(820,40,940,90),'floor':(560,650,760,840),'wainscot_R':(1150,620,1270,700),'seat2L':(270,560,380,690),'post_L':(255,260,275,460),'sash_R':(1150,400,1270,420),'windowL':(20,200,200,350)}
for n,(x0,y0,x1,y1) in B.items(): print('  %-10s photo %s render %s'%(n,ph[y0:y1,x0:x1].reshape(-1,3).mean(0)[::-1].round(),c[y0:y1,x0:x1].reshape(-1,3).mean(0)[::-1].round()))
print('|diff| %.1f'%np.abs(c-ph).mean()); cv2.imwrite('g/int8.jpg',np.concatenate([ph,c],1)[::2,::2])
