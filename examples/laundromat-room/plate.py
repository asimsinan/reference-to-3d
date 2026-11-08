import cv2, numpy as np
def pushpull(img,valid):
    if min(img.shape[:2])<4:
        w=valid.astype(np.float32)[...,None]; s=(img*w).sum((0,1))/max(w.sum(),1)
        out=img.copy(); out[~valid]=s; return out
    w=valid.astype(np.float32)
    sm=cv2.resize(img*w[...,None],(img.shape[1]//2,img.shape[0]//2),interpolation=cv2.INTER_AREA)
    ws=cv2.resize(w,(img.shape[1]//2,img.shape[0]//2),interpolation=cv2.INTER_AREA)
    small=sm/np.maximum(ws,1e-6)[...,None]; small=pushpull(small,ws>0.05)
    up=cv2.resize(small,(img.shape[1],img.shape[0]),interpolation=cv2.INTER_LINEAR)
    out=img.copy(); out[~valid]=up[~valid]; return out
if __name__=='__main__':
    im=cv2.imread('ref.png').astype(np.float32); m=cv2.imread('propmask.png',0)>0
    out=pushpull(im,~m)
    # light grain so filled areas are not plastic
    rng=np.random.default_rng(1); n=cv2.GaussianBlur(rng.normal(0,1,im.shape[:2]).astype(np.float32),(0,0),1.2)*4
    out[m]+=n[m][:,None]
    cv2.imwrite('plate.png',np.clip(out,0,255).astype(np.uint8))
    cv2.imwrite('plate_small.jpg',cv2.resize(np.clip(out,0,255).astype(np.uint8),(960,540)))
