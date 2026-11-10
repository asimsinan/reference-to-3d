"""photo | render (composited over the photo) per view + numbers. usage: cmp.py RENDER_DIR out.jpg"""
import cv2,numpy as np,sys
D=sys.argv[1];rows=[]
CROP={'front':(180,620,1380,1720),'side':(180,600,1320,1400),'rear':(250,900,1500,1720)}
for v in ['front','side','rear']:
    ph=cv2.imread(v+'.jpg');r=cv2.imread('%s/%s.png'%(D,v),cv2.IMREAD_UNCHANGED);r=cv2.resize(r,(1500,2000),interpolation=cv2.INTER_LINEAR)
    a=r[...,3:4].astype(float)/255;comp=(r[...,:3]*a+ph*(1-a)).astype(np.uint8)
    m=cv2.imread('m_%s.png'%v,0)>0;ra=r[...,3]>250
    both=m&ra
    def st(img):
        px=img[both].astype(float);L=px.mean(1);hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)[both]
        return px.mean(0)[::-1].round(0),round(L.std(),1),np.percentile(L,[5,95]).round(0),round(hsv[:,1].mean(),0)
    print(v,'IoU(all, cord incl.)',round((m&ra).sum()/(m|ra).sum(),3));print('  photo  mean rgb %s  L-std %s  p5/p95 %s sat %s'%st(ph));print('  render mean rgb %s  L-std %s  p5/p95 %s sat %s'%st(comp))
    x0,y0,x1,y1=CROP[v];pair=np.hstack([ph[y0:y1,x0:x1],comp[y0:y1,x0:x1]]);rows.append(cv2.resize(pair,(1400,int(pair.shape[0]*1400/pair.shape[1]))))
    cv2.imwrite('%s/cmp_%s.jpg'%(D,v),rows[-1])
cv2.imwrite(sys.argv[2],np.vstack(rows))
