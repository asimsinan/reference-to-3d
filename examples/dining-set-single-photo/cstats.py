import cv2, numpy as np, sys
ref=cv2.imread('ref.jpg'); ren=cv2.imread(sys.argv[1])
if ren.shape[0]!=1000: ren=cv2.resize(ren,(1000,1000),interpolation=cv2.INTER_AREA)
al=cv2.imread('../renders_foto/photo.png',cv2.IMREAD_UNCHANGED)[...,3]>250; m=cv2.erode(al.astype(np.uint8),np.ones((5,5),np.uint8))>0
def st(img,mk):
    hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV).astype(float); L=cv2.cvtColor(img,cv2.COLOR_BGR2LAB)[...,0].astype(float)[mk]
    return hsv[...,1][mk].mean(), L.mean(), L.std(), np.percentile(L,5), np.percentile(L,95)
R={'all furniture':m}
for nm,(x0,y0,x1,y1) in {'table top+apron':(230,300,770,460),'stools':(590,480,930,960),'legs':(240,520,530,950)}.items():
    k=np.zeros_like(m); k[y0:y1,x0:x1]=True; R[nm]=m&k
print('%-16s %18s %18s %18s %18s'%('','sat','light','contrast','p5-p95'))
for k,mk in R.items():
    a=st(ref,mk); b=st(ren,mk); print('%-16s %8.0f / %-8.0f %8.0f / %-8.0f %8.1f / %-8.1f %5.0f-%-4.0f / %3.0f-%-3.0f'%(k,a[0],b[0],a[1],b[1],a[2],b[2],a[3],a[4],b[3],b[4]))
