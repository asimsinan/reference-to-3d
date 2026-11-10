# flag texture (official construction, red from the photos) and a sea tile from photo r5
import cv2,numpy as np,json
def lin(c): return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def srgb(c): return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.maximum(c,1e-9),1/2.4)-0.055)
L=json.load(open('light.json')); Elit=np.array(L['sun'])*0.707/np.pi+np.array(L['sky'])
# flag red: saturated red pixels of the flag in r5 and r4
reds=[]
for n,(x0,y0,x1,y1) in {'r5':(690,132,740,172),'r4':(775,205,822,245),'r1':(860,150,912,208)}.items():
    p=cv2.imread('ref/%s.png'%n)[y0:y1,x0:x1].reshape(-1,3).astype(float); m=(p[:,2]>150)&(p[:,1]<90); reds.append(p[m])
red=np.median(np.concatenate(reds),0)[::-1]/255.; alb=np.clip(lin(red)/Elit*1.3,0,0.9); print('flag red sRGB',np.round(red*255),'albedo',np.round(alb,3))
G=800; W=int(1.5*G); im=np.zeros((G,W,3),np.float32); im[:]=srgb(alb)[::-1]
cv2.circle(im,(int(0.5*G),G//2),int(0.25*G),(0.9,0.9,0.9),-1,cv2.LINE_AA); cv2.circle(im,(int(0.5625*G),G//2),int(0.2*G),tuple(float(v) for v in srgb(alb)[::-1]),-1,cv2.LINE_AA)
cx=(0.5625-0.2+1/3+0.125)*G; r=0.125*G; pts=[]
for k in range(10):
    a=np.pi+k*np.pi/5; rr=r if k%2==0 else r*0.381966
    pts.append((cx+rr*np.cos(a),G/2+rr*np.sin(a)))
cv2.fillPoly(im,[np.array(pts,np.int32)],(0.9,0.9,0.9),cv2.LINE_AA)
cv2.imwrite('tex/flag.png',(im*255).astype(np.uint8))
# sea tile
p=cv2.imread('ref/r5.png')[250:550,60:360].astype(np.float32)/255.
a=np.clip(lin(p)/Elit[::-1]-0.03,0.01,0.9); a=cv2.resize(a,(512,512),interpolation=cv2.INTER_CUBIC)
t=np.vstack([np.hstack([a,a[:,::-1]]),np.hstack([a[::-1],a[::-1,::-1]])])
cv2.imwrite('tex/sea.png',(srgb(t)*255).astype(np.uint8)); print('sea albedo',np.round(np.median(a.reshape(-1,3),0)[::-1],3))
gs=[]
for n,(x0,y0,x1,y1) in {'r1':(849,30,862,116),'r3':(627,112,638,172),'r2':(710,112,722,176)}.items():
    p=cv2.imread('ref/%s.png'%n)[y0:y1,x0:x1].reshape(-1,3).astype(float); d=p[:,2]-p[:,0]; gs.append(p[d>=np.percentile(d,75)])
g=np.median(np.concatenate(gs),0)[::-1]/255.; print('gold sRGB',np.round(g*255))
rl=[]
for n,(x0,y0,x1,y1) in {'r5':(690,470,800,490),'r4':(745,520,850,540)}.items():
    p=cv2.imread('ref/%s.png'%n)[y0:y1,x0:x1].reshape(-1,3).astype(float); rl.append(p[p.sum(1)<np.percentile(p.sum(1),25)])
rail=np.median(np.concatenate(rl),0)[::-1]/255.; print('rail sRGB',np.round(rail*255))
json.dump({'spec':{'dome':0.25,'terrace':0.15,'parapet':0.15},'gold':[float(v) for v in lin(g)],'flag':[float(v) for v in alb],'rail':[float(v) for v in np.clip(lin(rail)/0.5,0,0.6)]},open('extra.json','w'))
