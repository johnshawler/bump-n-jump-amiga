import sys,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from reference import *
b=Bus();m=MPU(memory=b,pc=None);d=Disassembler(m);counts=collections.Counter();ops=collections.Counter()
for frame in range(1550):
 b.pad=8 if 180<=frame<185 else 16 if frame>190 else 0
 if frame>190 and frame%180<4:b.pad|=1
 if frame and b.ctrl&128:m.nmi()
 for step in range(100000):
  if (m.pc==0x8070 and not b.ram[14]) or (m.pc==0x9321 and b.ram[0x401]):break
  if 1450<=frame<1550:counts[m.pc]+=1;ops[d.instruction_at(m.pc)[1].split()[0]]+=1
  m.step()
print('TOTAL per frame',sum(counts.values())/100,ops)
for pc,n in counts.most_common(100):print('%04x'%pc,n,d.instruction_at(pc)[1])
