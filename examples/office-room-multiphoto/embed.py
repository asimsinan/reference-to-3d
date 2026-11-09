import base64, json
R = json.load(open('room_final.json'))
keep = {k: round(R[k], 4) for k in ('W', 'L', 'H', 'xA0', 'xA1', 'xB0', 'xB1', 'xl', 'yl0', 'yl1')}
keep.update({'xA0': 2.50, 'xA1': 1.46, 'xB0': 1.24, 'xB1': 0.20})      # window openings of the detailed model
t = open('viewer/template.html').read()
t = t.replace('"__GLB__"', '"' + base64.b64encode(open('oda.glb', 'rb').read()).decode() + '"').replace('__ROOM__', json.dumps(keep))
open('/Users/asimsinanyuksel/Desktop/oda/oda_gezinti.html', 'w').write(t); print(round(len(t) / 1e6, 2), 'MB')
