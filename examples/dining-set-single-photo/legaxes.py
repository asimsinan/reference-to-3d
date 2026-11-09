import cv2, numpy as np, json
lab=cv2.GaussianBlur(cv2.cvtColor(cv2.imread('ref.jpg'),cv2.COLOR_BGR2LAB).astype(np.float32),(3,3),0)
gx=sum(np.abs(cv2.Sobel(lab[...,i],cv2.CV_32F,1,0)) for i in range(3))
L={'S1_FL':((645,712),(600,890),26,12),'S1_FR':((779,730),(795,940),28,12),'S2_BR':((893,610),(904,722),18,10),
   'S2_FR':((849,690),(856,808),16,10),'S1_BR':((835,712),(846,822),18,10),
   'B_L1':((117,595),(96,760),22,11),'B_L2':((211,612),(225,795),24,12),'B_L3':((432,540),(451,615),16,10),'B_L4':((337,545),(338,600),14,10)}
out={}
for k,((xa,ya),(xb,yb),wa,wb) in L.items():
    rows=[];
    for y in range(ya,yb+1,4):
        t=(y-ya)/(yb-ya); xc=xa+t*(xb-xa); w=wa+t*(wb-wa)
        def pk(x0):
            a=int(x0-4); l=gx[y,a:a+9]; return a+np.argmax(l)
        xl=pk(xc-w/2); xr=pk(xc+w/2); rows.append((y,xl,xr))
    R=np.array(rows,float); ctr=(R[:,1]+R[:,2])/2; wid=R[:,2]-R[:,1]
    m,c=np.polyfit(R[:,0],ctr,1); res=ctr-(m*R[:,0]+c)
    ok=np.abs(res)<2.5*np.std(res)+0.5; m,c=np.polyfit(R[ok,0],ctr[ok],1)
    print('%-6s x = %.4f*y + %.1f   rms %.2f  width %.1f -> %.1f'%(k,m,c,np.std(ctr[ok]-(m*R[ok,0]+c)),np.median(wid[:3]),np.median(wid[-3:])))
    out[k]=dict(m=m,c=c,y0=ya,y1=yb,w0=float(np.median(wid[:3])),w1=float(np.median(wid[-3:])))
json.dump(out,open('legaxes.json','w'),indent=1)
