import numpy as np
def corners(o):
    if o['kind']=='box':
        x0,x1,y0,y1,z0,z1=o['b']; y0=max(y0,0.35)
        return [(x,y,z) for x in(x0,x1) for y in(y0,y1) for z in(z0,z1)],None
    if o['kind']=='cyl':
        a=np.linspace(0,2*np.pi,24,endpoint=False); P=[]
        for z,r in zip(o['z'],o['r']): P+= [(o['c'][0]+r*np.cos(t),o['c'][1]+r*np.sin(t),z) for t in a]
        return P,None
    if o['kind']=='tilt':
        y0=max(o['y'][0],0.35); P=[]
        for y in (y0,o['y'][1]):
            for (x,z) in (o['bottom'],o['top']): P+=[(x,y,z),(x-o['t'],y,z)]
        return P,None
