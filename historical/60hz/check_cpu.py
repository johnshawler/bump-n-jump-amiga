import ctypes as C,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from reference import *
lib=C.CDLL(str(R/'build/engine.dylib'))
class CPU(C.Structure):_fields_=[(s,C.c_uint) for s in ['a','x','y','s','p','pc','error','dispatches']]
c=CPU.in_dll(lib,'cpu');arrays={k:(C.c_ubyte*n).in_dll(lib,k) for k,n in [('ram',2048),('nt',2048),('pal',32),('oam',256)]}
regs={k:C.c_ubyte.in_dll(lib,k) for k in ['ctrl','mask','bank','sx','sy','pad']}
b=Bus();b.oam[:]=bytes(256);m=MPU(memory=b,pc=None)
for frame in range(15000):
 b.pad=8 if frame in range(180,185) or (frame>1000 and b.ram[0x14]==2 and frame%100<3) else 0
 if frame>190:
  if frame%180<4:b.pad|=1
  if frame%500<25:b.pad|=64
  elif frame%500>470:b.pad|=128
  b.pad|=16
 regs['pad'].value=b.pad
 intr=bool(frame and b.ctrl&128)
 if intr:m.nmi()
 steps=0
 while steps<100000:
  if (m.pc==0x8070 and not b.ram[14]) or (m.pc==0x9321 and b.ram[0x401]):break
  m.step();steps+=1
 lib.cpu_run(intr)
 vals=[m.a,m.x,m.y,m.sp,m.p,m.pc];native=[c.a,c.x,c.y,c.s,c.p,c.pc]
 if vals!=native:
  print('CPU FAIL',frame,vals,native,c.error);sys.exit(1)
 for k in arrays:
  if bytes(arrays[k])!=bytes(getattr(b,k)):
   for i,(x,y) in enumerate(zip(arrays[k],getattr(b,k))):
    if x!=y:print('MEM FAIL',frame,k,hex(i),x,y);sys.exit(1)
 for k in ['ctrl','mask','bank','sx','sy']:
  if regs[k].value!=getattr(b,k):print('REG FAIL',frame,k);sys.exit(1)
 # Consume the renderer queue, as the Amiga does.
 C.c_ushort.in_dll(lib,'dirtycount').value=0
 (C.c_ubyte*2048).in_dll(lib,'marked')[:]=bytes(2048)
 if frame%1000==0:print('PASS',frame,steps,'mode',b.ram[0x14],flush=True)
print('PASS: 15000 complete frames: registers, all RAM, VRAM, palettes and sprites')
