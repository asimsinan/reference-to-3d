# fit per frame: photo(linear) ~ sum_i w_i * pass_i (NNLS per channel, on blurred tower pixels) -> out/fit_<frame>.png, lp/fit.json
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2,numpy as np,json,sys
from scipy.optimize import nnls
def lin(c): return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def srgb(c): return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.maximum(c,1e-9),1/2.4)-0.055)
names=open('id/names.txt').read().split(); SUNS=json.load(open('lp/suns.json')); res={}
FR=sys.argv[1:] or ['r2','r3','r4']
for k in FR:
    a=lin(cv2.imread('ref/%s.png'%k).astype(np.float32)/255.)
    passes=[cv2.imread('lp/%s_%02d.exr'%(k,i),cv2.IMREAD_UNCHANGED) for i in range(len(SUNS)+1)]
    alpha=passes[0][...,3]; Ps=[p[...,:3] for p in passes]
    idm=cv2.imread('id/%s.png'%k,cv2.IMREAD_UNCHANGED); idx=np.round(idm[...,2]/8.0).astype(int); idx[idm[...,3]<128]=0
    use=np.isin(idx,[names.index(n)+1 for n in ('shaft','cornice','arcade','roof')])
    use=cv2.erode(use.astype(np.uint8),np.ones((7,7),np.uint8))>0
    ys=np.nonzero(use)[0]; use[ys.max()-40:]=False     # the foot: people and the plaza
    B=lambda im: cv2.GaussianBlur(im,(0,0),4)
    ab=B(a); pb=[B(p) for p in Ps]; W=[]
    sub=np.nonzero(use.ravel())[0][::3]
    for c in range(3):
        A=np.stack([p[...,c].ravel()[sub] for p in pb],1); y=ab[...,c].ravel()[sub]
        w,_=nnls(A,y); W.append(w)
    W=np.array(W)   # 3 x P
    comp=sum(Ps[i]*W[:,i][None,None,::1] for i in range(len(Ps)))
    out=cv2.imread('ref/%s.png'%k).astype(np.float32)/255.; m=alpha>0.5
    out[m]=srgb(np.clip(comp[m],0,1))
    cv2.imwrite('out/fit_%s.png'%k,(np.clip(out,0,1)*255+0.5).astype(np.uint8))
    top=np.argsort(-W.mean(0))[:4]
    res[k]={'w':W.tolist()}
    print(k,'sky w',np.round(W[:,0],3),'main suns',[(SUNS[i-1] if i>0 else 'sky',round(float(W[:,i].mean()),3)) for i in top])
json.dump(res,open('lp/fit.json','w'))
