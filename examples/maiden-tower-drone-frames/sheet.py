import cv2,numpy as np,sys
pre=sys.argv[1]; rows=[]
for i in range(1,7):
    a=cv2.imread('ref/r%d.png'%i); b=cv2.imread('out/%s_r%d.png'%(pre,i))
    rows.append(np.hstack([cv2.resize(a,(620,480)),cv2.resize(b,(620,480))]))
cv2.imwrite('g/sheetA.jpg',np.vstack(rows[:3])); cv2.imwrite('g/sheetB.jpg',np.vstack(rows[3:]))
