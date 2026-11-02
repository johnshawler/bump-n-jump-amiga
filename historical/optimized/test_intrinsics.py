import sys,ctypes as C,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from reference import *
lib=C.CDLL(str(R/'build/engine.dylib'))
class CPU(C.Structure):_fields_=[(s,C.c_uint) for s in ['a','x','y','s','p','pc','error','dispatches']]
c=CPU.in_dll(lib,'cpu');rr=(C.c_ubyte*2048).in_dll(lib,'ram');random.seed(1200)
for entry in [0x8092,0xaa44,0xb4f1,0xa920,0xb476,0xb3a4,0xb4b6,0x8109]:
 for k in range(3000):
  b=Bus();b.ram[:]=random.randbytes(2048) if hasattr(random,'randbytes') else bytes(random.getrandbits(8) for _ in range(2048))
  b.ram[14]=0;b.ram[0x1fe]=0x6f;b.ram[0x1ff]=0x80
  b.ram[0x27]=random.choice([0x50,0x90]);b.ram[0x28]=3
  b.ram[0x29]=0;b.ram[0x2a]=7
  if entry==0xa920:b.ram[0x27]=0xf8;b.ram[0x28]=0xa9
  if entry==0xb3a4:b.ram[0x1f]=1;b.ram[0x21]=0
  if entry==0x8109:b.pad=random.randrange(256);C.c_ubyte.in_dll(lib,'pad').value=b.pad
  rr[:]=b.ram
  m=MPU(memory=b,pc=entry);m.a=random.randrange(256);m.x=random.randrange(256);m.y=random.randrange(256);m.sp=253;m.p=random.randrange(256)&~8|48
  c.a=m.a;c.x=m.x;c.y=m.y;c.s=m.sp;c.p=m.p;c.pc=entry;c.error=0
  while m.pc!=0x8070:m.step()
  lib.cpu_run(0)
  actual=[c.a,c.x,c.y,c.s,c.p,c.pc];expected=[m.a,m.x,m.y,m.sp,m.p,m.pc]
  assert actual==expected,(hex(entry),k,actual,expected)
  assert bytes(rr)==b.ram,(hex(entry),k,'RAM')
  if entry==0x8109:
   assert C.c_ubyte.in_dll(lib,'joy').value==b.joy
   assert C.c_ubyte.in_dll(lib,'strobe').value==b.strobe
 print(hex(entry),'PASS 3000 randomized original-ROM comparisons',flush=True)
