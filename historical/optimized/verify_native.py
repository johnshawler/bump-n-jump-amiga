from pathlib import Path
import sys,struct,json
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent));from reference import *
T=R/(sys.argv[1] if len(sys.argv)>1 else 'test/results');data=(T/'stats.bin').read_bytes();st=struct.unpack('>'+str(len(data)//4)+'I',data);N=st[1]
b=Bus();b.oam[:]=bytes(256);m=MPU(memory=b,pc=None)
def run():
 for i in range(100000):
  if (m.pc==0x8070 and not b.ram[14]) or (m.pc==0x9321 and b.ram[0x401]):return
  m.step()
 raise RuntimeError('reference stuck')
run()
inputs=(T/"native-input.bin").read_bytes() if (T/"native-input.bin").exists() else None
for frame in range(N):
 b.pad=8 if 180<=frame<185 else 0
 if frame>190:
  b.pad|=16
  if frame%180<4:b.pad|=1
  if frame%500<25:b.pad|=64
  elif frame%500>470:b.pad|=128
 if inputs is not None:b.pad=inputs[frame]
 if b.ctrl&128:m.nmi()
 run()
gotcpu=list(struct.unpack('>8I',(T/'native-cpu.bin').read_bytes()))[:6]
assert gotcpu==[m.a,m.x,m.y,m.sp,m.p,m.pc],('CPU',gotcpu,[m.a,m.x,m.y,m.sp,m.p,m.pc])
for k in ['ram','nt','oam','pal']:
 got=(T/('native-'+k+'.bin')).read_bytes();ref=bytes(getattr(b,k));assert got==ref,(k,[(i,x,y) for i,(x,y) in enumerate(zip(got,ref)) if x!=y][:8])
print('Source logic and all native RAM/VRAM/sprites/palette match at',N,'ticks')
# Independently build the 5-bit palette-index reference.
expected=bytearray(256*240);solid=bytearray(len(expected));covered=bytearray(len(expected))
for y in range(240):
 yy=(y+b.sy)%240;nb=(((b.ctrl&2)>>1)+(y+b.sy)//240)&1;nb*=1024
 for x in range(256):
  t=b.nt[nb+(yy//8)*32+x//8];at=b.nt[nb+960+(yy//32)*8+x//32];co=(at>>(((yy&16)>>2)|((x&16)>>3)))&3
  a=(4096 if b.ctrl&16 else 0)+t*16+(yy&7)
  p=((b.ppuread(a)>>(7-(x&7)))&1)|(((b.ppuread(a+8)>>(7-(x&7)))&1)<<1)
  expected[y*256+x]=p+co*4 if p else 0;solid[y*256+x]=bool(p)
for i in range(64):
 yy,t,at,xx=b.oam[i*4:i*4+4];yy+=1;h=16 if b.ctrl&32 else 8
 for j in range(h):
  y=yy+j
  if y>=240:continue
  syy=h-1-j if at&128 else j
  a=((t&1)*4096+(t&254)*16+(syy//8)*16+(syy&7)) if h==16 else ((4096 if b.ctrl&8 else 0)+t*16+syy)
  p0=b.ppuread(a);p1=b.ppuread(a+8)
  for k in range(8):
   x=xx+k
   if x>=256:continue
   bit=k if at&64 else 7-k;p=((p0>>bit)&1)|(((p1>>bit)&1)<<1);q=y*256+x
   if p and not covered[q]:
    covered[q]=1
    if not(at&32 and solid[q]):expected[q]=16+(at&3)*4+p
raw=(T/'native-screen.bin').read_bytes();actual=bytearray(len(expected))
for y in range(240):
 for x in range(256):
  a=(y+8)*40+4+x//8;actual[y*256+x]=sum(((raw[a+p*10240]>>(7-(x&7)))&1)<<p for p in range(5))
# Values 4/8/12 are transparent universal background colour and can be canonicalized.
for a in [actual,expected]:
 for i,v in enumerate(a):
  if not(v&3):a[i]=0
bad=[(i%256,i//256,x,y) for i,(x,y) in enumerate(zip(actual,expected)) if x!=y]
print('Pixel mismatches',len(bad),bad[:25])
render(b,R/'build/native-reference.png')
colors=[tuple(Image.open(R/'build/native-reference.png').getpixel((0,0))) for _ in range(32)]
# Save index images for lossless comparison.
for label,a in [('native',actual),('expected',expected)]:
 im=Image.frombytes('P',(256,240),bytes(a));im.putpalette([v for i in range(256) for v in ((i*71)%256,(i*131)%256,(i*47)%256)]);im.save(R/f'build/{label}-indices.png')
assert not bad
report=json.dumps({'ticks':N,'logic':'PASS','native_viewport_pixels':61440,'pixel_mismatches':0,'fields':st[0],'publications':st[2],'max_cpu_fields':st[4],'max_render_fields':st[5]},indent=2)
(R/'build/native-verification.json').write_text(report)
(T/'native-verification.json').write_text(report)
