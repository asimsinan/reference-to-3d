"""Lights and tone curve fitted to the photo's region means AND contrast (std per region, the furniture's 5th/95th
lightness percentiles and spread)."""
import subprocess, numpy as np, cv2, json, sys
from scipy.optimize import minimize
ref=cv2.imread('ref.jpg').astype(np.float32)
B={'top near':(300,412,420,428),'top far':(600,330,700,350),'short apron':(300,470,460,495),'long apron':(600,420,700,440),
   'leg B':(495,600,520,800),'leg A':(252,600,276,800),'S1 cushion':(660,600,800,650),'S1 tray':(640,672,780,695),'S1 leg':(775,760,790,900),
   'bench cushion':(110,545,230,565),'S2 cushion':(760,510,880,550),'cup2':(548,370,560,390),'candle':(625,310,655,325),
   'sphere':(580,290,610,315),'plate':(510,348,580,354),'floor near':(300,880,450,960),'floor left':(0,700,90,800),'wall':(895,240,1000,470),'curtain':(520,60,600,240),
   'S1 front':(600,640,880,720),'table end':(230,400,500,520),'under table':(420,500,560,640)}
al=cv2.imread('../renders_foto/photo.png',cv2.IMREAD_UNCHANGED)[...,3]>250; M=cv2.erode(al.astype(np.uint8),np.ones((5,5),np.uint8))>0
Lr=cv2.cvtColor(ref.astype(np.uint8),cv2.COLOR_BGR2LAB)[...,0].astype(float)
def gstats(L): v=L[M]; return np.array([np.percentile(v,5),np.percentile(v,50),np.percentile(v,95),v.std()])
GR=gstats(Lr)
LOOK=sys.argv[2] if len(sys.argv)>2 else 'None'
log=[]
def f(x):
    e,win,sheer,world,fill=x; top=np.log(1e-3)
    cmd=['/Applications/Blender.app/Contents/MacOS/Blender','-b','-P','build.py','--','--mode','final','--out','r_tune2','--shots','photo','--res','400','--samples','24',
         '--vt','Standard','--look',LOOK,'--exposure',f'{e:.3f}','--win',f'{np.exp(win):.1f}','--sheer',f'{np.exp(sheer):.2f}','--fillz','2.6','--fillfwd','0.9','--fillsize','1.8','--world',f'{np.exp(world):.3f}','--fill',f'{np.exp(fill):.1f}']
    subprocess.run(cmd,capture_output=True)
    r=cv2.resize(cv2.imread('r_tune2/photo.png'),(1000,1000)).astype(np.float32)
    Lx=cv2.cvtColor(r.astype(np.uint8),cv2.COLOR_BGR2LAB)[...,0].astype(float)
    dm=[]; ds=[]
    for (x0,y0,x1,y1) in B.values():
        a=ref[y0:y1,x0:x1].reshape(-1,3); b=r[y0:y1,x0:x1].reshape(-1,3)
        dm.append(np.abs(a.mean(0)-b.mean(0)).mean()); ds.append(abs(Lr[y0:y1,x0:x1].std()-Lx[y0:y1,x0:x1].std()))
    g=np.abs(gstats(Lx)-GR)
    v=float(np.mean(dm)+1.0*np.mean(ds)+1.0*g.mean()); log.append((v,[float(t) for t in x],float(np.mean(dm)),float(np.mean(ds)),[float(t) for t in g]))
    print('%.1f (mean %.1f std %.1f global %s) e %.2f win %.0f sheer %.2f world %.2f key %.0f'%(v,np.mean(dm),np.mean(ds),np.round(g,0),e,np.exp(win),np.exp(sheer),np.exp(world),np.exp(fill)),flush=True); return v
x0=[0.4,np.log(1000),np.log(2.0),np.log(0.4),np.log(150)]
sim=[x0]+[list(np.array(x0)+np.eye(5)[i]*[0.5,0.7,0.6,0.8,1.0][i]) for i in range(5)]
minimize(f,x0,method='Nelder-Mead',options=dict(maxfev=int(sys.argv[1]),initial_simplex=np.array(sim)))
best=min(log,key=lambda t:t[0]); print('BEST',LOOK,best)
json.dump({'look':LOOK,'score':best[0],'e':best[1][0],'win':float(np.exp(best[1][1])),'sheer':float(np.exp(best[1][2])),'key':True,'world':float(np.exp(best[1][3])),'fill':float(np.exp(best[1][4])),
           'mean':best[2],'std':best[3],'global':best[4]},open(f'light3_{LOOK.replace(" ","_")}.json','w'),indent=1)
