from geo import *
h=1.0; cam=np.array([0,0,h])
Yb=hit(650,700,2,0,cam)[1]
Hc=hit(700,262,1,Yb,cam)[2]
door_top=hit(1000,337,1,Yb,cam)[2]
s=2.0/door_top   # door 2.0 m
h=s; cam=np.array([0,0,h])
Yb=hit(650,700,2,0,cam)[1]; Hc=hit(700,262,1,Yb,cam)[2]
Xl=hit(588,480,1,Yb,cam)[0]
Xr=hit(1610,110,2,Hc,cam)[0]
print(f'cam h {h:.3f}  back Y {Yb:.3f}  ceiling {Hc:.3f}  left X {Xl:.3f} right X {Xr:.3f} width {Xr-Xl:.3f}')
# dryer block
pd=hit(1150,705,2,0,cam); Xd=pd[0]; print('dryer front X',Xd,'Y at base',pd[1])
Zdt=hit(1200,275,0,Xd,cam)[2]; print('dryer top Z',Zdt)
Yde=hit(1362,300,0,Xd,cam)[1]; print('dryer block near end Y',Yde)
Xr2=hit(1540,300,1,Yde,cam)[0]; print('right wall X from corner',Xr2)
# washers
pw=hit(1315,875,2,0,cam); print('washer4 left-bottom',pw)
Zwt=hit(1315,455,0,pw[0],cam)[2]; print('washer top',Zwt)
# table
fl=hit(900,844,2,0,cam); fr=hit(1080,836,2,0,cam); print('table front legs',fl,fr)
Zt=hit(900,617,1,fl[1],cam)[2]; print('table top',Zt)
bl=hit(870,578,2,Zt,cam); print('table back-left top',bl)
# cart wheels
for p in [(978,897),(1150,886),(955,855),(1114,842)]: print('cart wheel',p,hit(*p,2,0,cam))
w=hit(978,897,2,0,cam); print('cart top', hit(950,647,1,w[1],cam)[2], 'tray',hit(978,765,1,w[1],cam)[2])
# bench
bf=hit(656,945,2,0,cam); print('bench far front leg',bf)
print('bench seat Z',hit(655,788,1,bf[1],cam)[2])
# bucket
bk=hit(1250,1005,2,0,cam); print('bucket base front',bk, 'top', hit(1250,870,1,bk[1],cam)[2])
json.dump(dict(h=h,Yb=Yb,Hc=Hc,Xl=Xl,Xr=Xr),open('room.json','w'))
