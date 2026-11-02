import sys,collections,runpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from reference import *
g=runpy.run_path(str(R/'generate.py'));pcs=g['pcs'];missing=collections.Counter();b=Bus();b.oam[:]=bytes(256);m=MPU(memory=b,pc=None)
def step():
 if m.pc not in pcs:missing[m.pc]+=1
 m.step()
while not(m.pc==0x8070 and not b.ram[14]):step()
for f in range(1802):
 b.pad=8 if 180<=f<185 else 0
 if f>190:
  b.pad|=16
  if f%180<4:b.pad|=1
  if f%500<25:b.pad|=64
  elif f%500>470:b.pad|=128
 if b.ctrl&128:m.nmi()
 while not((m.pc==0x8070 and not b.ram[14]) or (m.pc==0x9321 and b.ram[0x401])):step()
print('Fallback instructions',sum(missing.values()),'unique',len(missing),'top',missing.most_common(30))
(R/'build/missing-pcs.json').write_text(__import__('json').dumps(dict(missing)))
