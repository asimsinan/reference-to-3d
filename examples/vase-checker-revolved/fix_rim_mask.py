"""rim ears: GrabCut lost the gold rim's outer edges against the red background (15 px a side). Hand-read outline
(g_rimL.png / g_rimR.png) filled into the mask."""
import cv2,numpy as np
s=cv2.imread('mask_grabcut.png',0)
L=[(225,200),(205,205),(193,210),(189,215),(186,220),(186,225),(187,230),(188,235),(191,240),(196,244)]
R=[(396,244),(398,240),(400,235),(401,230),(402,225),(402,220),(399,215),(393,210),(381,205),(362,200)]
poly=np.array(L+R+[(300,199)],np.int32)
cv2.fillPoly(s,[poly],255); cv2.imwrite('mask_raw.png',s)
