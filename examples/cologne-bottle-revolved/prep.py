"""Textures from the photo. Crop (X0,Y0)-(X1,Y1) round the bottle, upsampled UP x; margin outside the model's own
silhouette (model_mask.png) filled by normalized Gaussian convolution. tex_front.png: the photo; tex_back.png: the
label's print and the dip tube inpainted (the back is the front's mirror; a mirrored logo would be wrong).
writes tex_front.png, tex_back.png, tex_info.json, prep_vis.jpg"""
import cv2,numpy as np,json
from scipy import ndimage as ndi
im=cv2.imread('photo.jpg'); m=cv2.imread('model_mask.png',0)>0
X0,Y0,X1,Y1=540,420,1020,1720; UP=2
def smooth_fill(img,valid):
    out=img.astype(np.float32).copy(); done=valid.copy(); mk=valid.astype(np.float32)
    for sg in (2,4,8,16,32,64,128):
        num=cv2.GaussianBlur(img.astype(np.float32)*mk[...,None],(0,0),sg); den=cv2.GaussianBlur(mk,(0,0),sg)
        ok=(den>0.02)&~done; out[ok]=num[ok]/den[ok][:,None]; done|=ok
    out[~done]=out[done].mean(0)
    return np.clip(out,0,255).astype(np.uint8)
valid=ndi.binary_erosion(m,iterations=2)      # edge pixels are mixed with the background
front=smooth_fill(im,valid)
# back plate: inpaint the print on the label (dark / saturated-brown pixels inside the body between the shoulder and the base)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); g=im.mean(2)
H,W=g.shape; yy,xx=np.mgrid[0:H,0:W]
label=(yy>960)&(yy<1590)&valid
# local darkness relative to the label's background (median filtered)
med=cv2.medianBlur(im,41).mean(2)
print_=label&((med-g>22)|((hsv[...,1]>110)&(hsv[...,2]<215)))
print_=ndi.binary_dilation(print_,iterations=3)
tube=(yy>868)&(yy<990)&(xx>748)&(xx<815)&valid          # the dip tube seen through the clear body
inp=(print_|tube).astype(np.uint8)*255
back=cv2.inpaint(front,inp,9,cv2.INPAINT_TELEA)
# smooth the inpainted label area a little (Telea leaves streaks)
blur=cv2.GaussianBlur(back,(0,0),3); w=cv2.GaussianBlur(inp.astype(np.float32)/255,(0,0),2)[...,None]
back=(back*(1-w)+blur*w).astype(np.uint8)
def crop_up(a): return cv2.resize(a[Y0:Y1,X0:X1],None,fx=UP,fy=UP,interpolation=cv2.INTER_LANCZOS4)
cv2.imwrite('tex_front.png',crop_up(front)); cv2.imwrite('tex_back.png',crop_up(back))
# plain colours: the underside (the grey bottom ring), the cap top
ring=(yy>1620)&(yy<1660)&(xx>700)&(xx<860)
info=dict(crop=[X0,Y0,X1,Y1],up=UP,under_rgb=[int(c) for c in np.median(im[ring],0)[::-1]],print_px=int(print_.sum()))
json.dump(info,open('tex_info.json','w')); print(info)
vis=np.hstack([front[Y0:Y1,X0:X1],back[Y0:Y1,X0:X1]]); cv2.imwrite('prep_vis.jpg',cv2.resize(vis,None,fx=0.5,fy=0.5))
