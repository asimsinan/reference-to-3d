from cushfit import *
out=json.load(open('cush.json')); cx,cy,th,a,b,rc,zr,zt=out['S1']
out['bench']=fit('bench',[0.03,0.56,0.0,0.455,b,rc,zr,zt],keep=lambda x,y: (y> 530+0.15*(x-80)) | (x<100),
              fixed=dict(a=0.455,b=b,rc=rc,zr=zr,zt=zt)).tolist()
json.dump(out,open('cush.json','w'),indent=1)
