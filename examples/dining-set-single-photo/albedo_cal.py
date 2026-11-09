"""Per-material albedo gains from photo/render ratios (linear light) over each material's regions; textured materials
get calibrated copies tex/<name>_cal.png, flat ones a colour gain. Cumulative over runs (gains.json)."""
import cv2, numpy as np, json, os, sys
ref=cv2.imread('ref.jpg').astype(np.float32)[...,::-1]; r=cv2.imread(sys.argv[1]).astype(np.float32)[...,::-1]
if r.shape[0]!=1000: r=cv2.resize(r,(1000,1000),interpolation=cv2.INTER_AREA)
lin=lambda c: np.where(c/255<=0.04045,c/255/12.92,((c/255+0.055)/1.055)**2.4)
REG={'oak':[(600,330,700,350),(300,470,460,495),(600,420,700,440),(640,672,780,695)],
     'leg':[(495,600,520,800),(252,600,276,800),(775,760,790,900)],
     'linen':[(660,600,800,650),(760,510,880,550),(110,545,230,565)],
     'porcelain':[(548,370,560,390)],'white_wax':[(625,310,655,325)],'pink_wax':[(580,290,610,315)],'plate_wood':[(505,347,585,356),(494,336,512,348)],
     'floor':[(300,880,450,960),(0,700,90,800),(560,600,680,700)],'wall':[(895,240,1000,470)],'curtain':[(520,60,600,240)],'coaster':[(354,382,400,388)]}
TEX={'oak':'oak_photo','leg':'leg_photo','linen':'linen_photo','pink_wax':'pink_wax','plate_wood':'oak_plate','floor':'floor','coaster':'oak_coaster'}
G=json.load(open('gains.json')) if os.path.exists('gains.json') else {}
for m,boxes in (REG.items() if len(sys.argv)<3 else []):
    pa=np.mean([lin(ref[y0:y1,x0:x1].reshape(-1,3).mean(0)) for x0,y0,x1,y1 in boxes],0)
    ra=np.mean([lin(r[y0:y1,x0:x1].reshape(-1,3).mean(0)) for x0,y0,x1,y1 in boxes],0)
    g=np.clip(pa/np.maximum(ra,1e-4),0.5,2.0)**0.7
    G[m]=np.clip(np.array(G.get(m,[1,1,1]))*g, 0.7 if m in ('porcelain','white_wax') else 0.3, 2.5).tolist()
    print('%-11s ratio %s  cumulative %s'%(m,np.round(g,2),np.round(G[m],2)))
json.dump(G,open('gains.json','w'),indent=1)
for m,t in TEX.items():
    im=cv2.imread(f'tex/{t}.png').astype(np.float32)[...,::-1]
    l=lin(im)*np.array(G[m]); s=np.where(l<=0.0031308,l*12.92,1.055*np.power(np.maximum(l,0),1/2.4)-0.055)
    cv2.imwrite(f'tex/{t}_cal.png',np.clip(s*255,0,255)[...,::-1].astype(np.uint8))
