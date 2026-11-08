from geo import *
import cv2
S=json.load(open('scene.json')); R=S['room']; cam=np.array([0,0,R['h']])
g=cv2.cvtColor(cv2.imread('ref.png'),cv2.COLOR_BGR2GRAY).astype(np.float32)
def door(xf,top,bot):
    a=hit(*top,0,xf,cam); b=hit(*bot,0,xf,cam); return dict(x=xf,y=float((a[1]+b[1])/2),z=float((a[2]+b[2])/2),r=float(abs(a[2]-b[2])/2))
doors=[door(1.81,(1165,375),(1165,502)),door(1.81,(1218,370),(1218,513)),door(1.81,(1295,356),(1295,520)),
       door(1.81,(1158,556),(1158,679)),door(1.81,(1218,568),(1218,702)),door(1.81,(1290,584),(1290,752)),
       door(1.60,(1362,594),(1375,850)),door(1.60,(1550,634),(1562,984))]
w2=hit(1819,709,0,1.60,cam); d3=doors[-1]; doors.append(dict(x=1.60,y=float(w2[1]),z=d3['z'],r=d3['r']))
for d in doors: print({k:round(v,3) for k,v in d.items()})
# cart rails on its front face Y=3.742 and handle on left face X=0.495
for nm,p in [('top rail',(1050,657)),('mid rail',(1050,703)),('tray',(1050,762))]: print(nm,hit(*p,1,3.742,cam)[2])
for nm,p in [('handle post A top',(942,592)),('handle post B top',(967,592)),('handle A low',(942,650)),('handle B low',(967,650))]:
    print(nm,hit(*p,0,0.495,cam))
# bench profile: seat across X at many Y; backrest along its slope
def profile(fn,ts,ys):
    P=[]
    for y in ys:
        row=[]
        for t in ts:
            u,v=proj(fn(t,y),cam)
            row.append(g[int(round(v)),int(round(u))] if 0<=u<1919.5 and 0<=v<1079.5 else np.nan)
        P.append(row)
    return np.nanmedian(np.array(P),0)
ts=np.linspace(0,1,200)
seat=lambda t,y: (-0.80+t*(-0.415+0.80),y,0.445)
back=lambda t,y: (-0.80+t*(-0.852+0.80),y,0.40+t*(0.824-0.40))
ps=profile(seat,ts,np.linspace(1.6,3.3,25)); pb=profile(back,ts,np.linspace(1.6,3.3,25))
np.set_printoptions(linewidth=250,precision=3,suppress=True)
print('seat',ps[::4]); print('back',pb[::4])
np.save('prof_seat.npy',ps); np.save('prof_back.npy',pb)
json.dump(doors,open('doors.json','w'))
for x in (1447,1675): print('unit boundary px',x, hit(x,470,0,1.60,cam))
for p in [(942,592),(967,592)]: print('handle top Z.92',p,hit(*p,2,0.92,cam))
