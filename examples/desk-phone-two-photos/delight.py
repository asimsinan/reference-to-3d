"""Photo -> albedo maps for the PBR version. Dividing by a wide blur removes the photo's shading and leaves the
printed matter (logo, CALL grille, labels, dust) as relative detail, scaled to the plastic's albedo. Keys: a
white-on-black mask from luminance."""
import cv2, numpy as np
BEIGE=np.array([0.66,0.76,0.80])*255   # BGR albedo of the cream plastic (sRGB)
def delight(src,dst,sigma=35,gain=1.0,keypad=None):
    im=cv2.imread(src).astype(np.float32)
    lum=cv2.cvtColor(im.astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)/255
    w=(lum>0.3).astype(np.float32)[...,None]            # the dark keys/band/logo must not darken their surroundings' mean
    bl=cv2.GaussianBlur(im*w,(0,0),sigma)/(cv2.GaussianBlur(w,(0,0),sigma)[...,None]+1e-3)+1
    ratio=im/bl
    out=np.clip(ratio*BEIGE*gain,0,255)
    out=0.5*out+0.5*BEIGE                                   # half the photo's mottling: a plastic, not a photo
    if keypad is not None:                                  # the keys' own shadows must not reach the body's albedo
        x0,y0,x1,y1=keypad; reg=out[y0:y1,x0:x1]; lr=lum[y0:y1,x0:x1]
        reg[lr<0.5]=BEIGE; out[y0:y1,x0:x1]=reg
    cv2.imwrite(dst,out.astype(np.uint8),[cv2.IMWRITE_JPEG_QUALITY,95])
delight('ref.jpg','ref_albedo.jpg',keypad=(670,1000,1080,1360)); delight('side_match.jpg','side_albedo.jpg')
g=cv2.cvtColor(cv2.imread('ref.jpg'),cv2.COLOR_BGR2GRAY).astype(np.float32)/255
k=np.clip((g-0.25)/0.30,0,1); k=k*k*(3-2*k)
keys=(0.05+(0.85-0.05)*k)*255
cv2.imwrite('ref_keys.jpg',cv2.cvtColor(keys.astype(np.uint8),cv2.COLOR_GRAY2BGR),[cv2.IMWRITE_JPEG_QUALITY,95])
a=cv2.imread('ref_albedo.jpg'); print('albedo top sample bgr',a[1350:1430,1000:1080].reshape(-1,3).mean(0).round(0),' logo region',a[880:892,873:943].reshape(-1,3).mean(0).round(0))
