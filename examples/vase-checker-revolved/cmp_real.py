import numpy as np, cv2, sys
ph=cv2.imread('../photo.jpg').astype(float); r=cv2.imread(sys.argv[1]).astype(float)
BOX=dict(neck_white=(275,270,300,320),neck_grey=(232,280,252,330),belly_white=(270,500,310,540),belly_grey=(330,470,370,520),
         left_belly=(150,470,180,520),right_belly=(410,470,440,520),foot=(260,780,300,800),band=(270,752,300,760),rim_front=(270,240,310,247))
for k,(x0,y0,x1,y1) in BOX.items():
    a=ph[y0:y1,x0:x1].reshape(-1,3).mean(0)[::-1]; b=r[y0:y1,x0:x1].reshape(-1,3).mean(0)[::-1]
    print('%-12s photo %s model %s  dL %+.0f'%(k,np.round(a),np.round(b),b.mean()-a.mean()))
cv2.imwrite(sys.argv[2],np.hstack([ph[170:850,100:490],r[170:850,100:490]]).astype(np.uint8))
