from pathlib import Path
import sys,json,zlib,re
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parent;T=R/sys.argv[1]
w,h,stride,pix=json.loads((T/'paused.json').read_text());im=Image.frombytes('RGBX',(w,h),zlib.decompress((T/'paused.z').read_bytes()),'raw','BGRX',stride).convert('RGB');im.save(T/'paused.png')
# verify_native.py independently checks this composed index export against the
# source ROM replay; here also check what the emulated Amiga actually displayed.
raw=np.frombuffer((T/'results/native-screen.bin').read_bytes(),np.uint8).reshape(5,256,40)[:,8:248,4:36]
a=np.sum(np.unpackbits(raw,axis=2)*(1<<np.arange(5))[:,None,None],axis=0,dtype=np.uint8)
colors=[int(v,16)for v in re.search(r'colors\[64\]=\{(.*?)\};',(R/'src/render.c').read_text(),re.S)[1].replace('\n','').split(',') if v]
pal=np.frombuffer((T/'results/native-pal.bin').read_bytes(),np.uint8)
colors=np.array([[((c>>8)&15)*17,((c>>4)&15)*17,(c&15)*17]for c in colors],np.uint8)
expected=colors[pal[np.where(a%4==0,0,a)]&63];expected=np.repeat(np.repeat(expected,2,0),2,1);actual=np.array(im)
best=(999999,None)
for y in range(46,59):
 for x in range(130,145):
  bad=int(np.count_nonzero(np.any(actual[y:y+480,x:x+512]!=expected,axis=2)))
  if bad<best[0]:best=(bad,(x,y))
Image.fromarray(expected).save(T/'expected-raster.png')
x,y=best[1];diff=np.any(actual[y:y+480,x:x+512]!=expected,axis=2);d=expected//3;d[diff]=[255,0,255];Image.fromarray(d).save(T/'raster-diff.png')
report={'actual_emulated_raster':'PASS' if not best[0] else 'FAIL','viewport_source_pixels':61440,'display_pixels':245760,'mismatches':best[0],'raster_origin':best[1],'capture':'paused'}
print(json.dumps(report));(T/'raster-verification.json').write_text(json.dumps(report,indent=2));assert not best[0],best
