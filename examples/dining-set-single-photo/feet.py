from geom import *
F_={'bench':[(95,768),(225,804),(451,625),(338,609)],'S1':[(598,905),(795,955),(846,832),(683,795)],'S2':[(700,778),(856,817),(904,730)]}
for k,pts in F_.items():
    P=np.array([hit_z(u,v-2,0.0) for u,v in pts])[:,:2]   # 2 px up: the foot's centre, not its front-most point
    print(k,np.round(P,3).tolist())
    n=len(P)
    for i in range(n):
        for j in range(i+1,n): print('   %d-%d %.3f'%(i,j,np.linalg.norm(P[i]-P[j])),end='')
    print()
    if n==4:
        d1=P[1]-P[0]; d2=P[2]-P[3]; e1=P[3]-P[0]; e2=P[2]-P[1]
        ang=lambda v: np.degrees(np.arctan2(v[1],v[0]))
        print('   dirs 0->1 %.1f  3->2 %.1f  0->3 %.1f  1->2 %.1f  centre'%(ang(d1),ang(d2),ang(e1),ang(e2)),np.round(P.mean(0),3))
    else:
        print('   dirs 0->1 %.1f 1->2 %.1f'%(np.degrees(np.arctan2(*(P[1]-P[0])[::-1])),np.degrees(np.arctan2(*(P[2]-P[1])[::-1]))))
