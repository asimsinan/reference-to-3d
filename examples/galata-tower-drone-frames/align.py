import numpy as np,cv2,itertools
D={k:np.load('out/uw_%s.npy'%k) for k in ['r1','r2','r3','r4']}
def hp(a):
    g=a[...,:3].mean(2); g=g-cv2.GaussianBlur(g,(0,0),6); return g
rows=slice(0,400)  # z 0..-20
res={}
for a,b in itertools.combinations(D,2):
    A=hp(D[a])[rows]; B=hp(D[b])[rows]; wa=D[a][rows,:,3]>0.45; wb=D[b][rows,:,3]>0.45
    best=[]
    for s in range(-360,360):
        Bs=np.roll(B,s,1); ws=np.roll(wb,s,1); m=wa&ws
        if m.sum()<4000: continue
        x=A[m]; y=Bs[m]; x=x-x.mean(); y=y-y.mean(); ncc=(x*y).sum()/np.sqrt((x*x).sum()*(y*y).sum())
        best.append((ncc,s*0.5,m.sum()))
    best.sort(reverse=True); res[(a,b)]=best[0]
    print(a,b,'best',[(round(n,3),d,c) for n,d,c in best[:4]])
