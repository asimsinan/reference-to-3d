import cv2, numpy as np, json
lab=cv2.GaussianBlur(cv2.cvtColor(cv2.imread('ref.jpg'),cv2.COLOR_BGR2LAB).astype(np.float32),(3,3),0)
gx=sum(np.abs(cv2.Sobel(lab[...,i],cv2.CV_32F,1,0)) for i in range(3))
def pk(row,a,b):
    l=gx[row,a:b]; k=int(np.argmax(l))
    if 0<k<len(l)-1:
        L,C,R=l[k-1],l[k],l[k+1]; dk=0.5*(L-R)/(L-2*C+R)
    else: dk=0
    return a+k+dk
# leg: (left edge guess at y0, at y1), (right edge guess at y0, at y1), rows
legs={'A':dict(y=(480,845),l=(247,246),r=(282,279)),
      'B':dict(y=(520,925),l=(487,491),r=(527,526)),
      'D':dict(y=(510,625),l=(536,534),r=(557,557)),
      'C':dict(y=(400,480),l=(723,724),r=(750,749))}
out={}
for k,v in legs.items():
    rows=np.arange(v['y'][0],v['y'][1]+1,8); res=[]
    for y in rows:
        t=(y-v['y'][0])/(v['y'][1]-v['y'][0])
        lg=v['l'][0]+t*(v['l'][1]-v['l'][0]); rg=v['r'][0]+t*(v['r'][1]-v['r'][0])
        xl=pk(y,int(lg-4),int(lg+5)); xr=pk(y,int(rg-4),int(rg+5)); res.append((y,xl,xr))
    R=np.array(res)
    ml,cl=np.polyfit(R[:,0],R[:,1],1); mr,cr=np.polyfit(R[:,0],R[:,2],1)
    rl=R[:,1]-(ml*R[:,0]+cl); rr=R[:,2]-(mr*R[:,0]+cr)
    print(k,'left dx/dy %.4f rms %.2f | right dx/dy %.4f rms %.2f | width top %.1f bottom %.1f'%(ml,np.sqrt((rl**2).mean()),mr,np.sqrt((rr**2).mean()),R[0,2]-R[0,1],R[-1,2]-R[-1,1]))
    print('  ',' '.join('%d:%.1f/%.1f'%tuple(r) for r in R))
    out[k]=R.tolist()
json.dump(out,open('legs.json','w'))
