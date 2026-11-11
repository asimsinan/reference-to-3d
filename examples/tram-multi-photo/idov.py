"""idov.py -- ID-render outlines (yellow) over each photo -> g/idov{k}.jpg"""
import cv2, numpy as np, sys, json
ks=sys.argv[1:] or ['1','2','3','4','5','6']
for k in ks:
    import os
    im=cv2.imread(f'ref2/p{k}.png' if os.environ.get('V34') else f'ref/p{k}.png'); idr=cv2.imread(f'out/id{k}.png',cv2.IMREAD_UNCHANGED)
    a=idr[...,3]>128; c=idr[...,:3].astype(int); key=c[...,0]*65536+c[...,1]*256+c[...,2]; key[~a]=-1
    e=np.zeros(key.shape,bool); e[:,1:]|=key[:,1:]!=key[:,:-1]; e[1:,:]|=key[1:,:]!=key[:-1,:]
    out=im.copy(); out[e]=(0,255,255)
    sil=a.astype(np.uint8); cnt,_=cv2.findContours(sil,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(out,cnt,-1,(255,0,255),1)
    cv2.imwrite(f'g/idov{k}.jpg',out)
