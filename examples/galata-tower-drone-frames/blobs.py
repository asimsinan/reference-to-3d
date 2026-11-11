import numpy as np,cv2,json
from invert import CC,C
g=json.load(open('solve.json'))['g']
out={}
for k in ['r1','r2','r3','r4']:
    a=np.load('out/uw_%s.npy'%k); o=a[...,:3]; w=a[...,3]
    gr=o.mean(2); bg=cv2.GaussianBlur(gr,(0,0),12); dark=((bg-gr)>38)&(w>0.35)
    dark[300:]=False  # z > -15
    n,l,st,cen=cv2.connectedComponentsWithStats(dark.astype(np.uint8))
    L=[]
    for i in range(1,n):
        x,y,ww,hh,ar=st[i]
        if ar<25: continue
        th=(cen[i][0]*0.5); th=th-360 if th>180 else th; z=-cen[i][1]*0.05
        # image coords of the blob centre
        c=CC(C[k]); r=g['r_s0']-g['taper']*z; P=np.array([[r*np.cos(np.radians(th)),r*np.sin(np.radians(th)),z]]); p=c.proj(P)[0]
        L.append((round(th,1),round(z,2),int(ar),round(p[0],1),round(p[1],1)))
    L.sort(); out[k]=L; print(k,[(t,z,a) for t,z,a,_,_ in L])
json.dump(out,open('out/blobs.json','w'))
