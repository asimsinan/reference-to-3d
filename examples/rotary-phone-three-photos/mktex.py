"""final texture files from masks + mat.json (run after prep_tex.py and whenever mat.json changes)"""
import cv2,numpy as np,json,os
M=json.load(open('mat.json')) if os.path.exists('mat.json') else {}
RED=np.array(M.get('red',[0.16,0.008,0.014]));WH=np.array(M.get('white',[0.62,0.62,0.56]))
lin2s=lambda c:np.where(c<0.0031308,c*12.92,1.055*np.clip(c,0,1)**(1/2.4)-0.055)
m=cv2.imread('t_ring_mask.png',0).astype(float)/255
alb=lin2s(RED*(1-m[...,None])+WH*m[...,None]);os.makedirs('gen',exist_ok=True)
cv2.imwrite('gen/kadran_albedo.png',(alb[...,::-1]*255).round().astype(np.uint8))
c=cv2.imread('t_card.png').astype(float)*M.get('card_gain',1.0);cv2.imwrite('gen/kart_albedo.png',np.clip(c,0,255).astype(np.uint8))
