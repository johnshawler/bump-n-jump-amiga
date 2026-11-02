import sys,collections,json
sys.path.insert(0,'work');from reference import *
b=Bus();b.oam[:]=bytes(256);m=MPU(memory=b,pc=None);d=Disassembler(m);counts=collections.Counter();calls=collections.Counter()
def run(record=False):
 while not((m.pc==0x8070 and not b.ram[14]) or (m.pc==0x9321 and b.ram[0x401])):
  if record:counts[m.pc]+=1
  m.step()
run()
for f in range(1600):
 b.pad=8 if 180<=f<185 else 0
 if f>190:b.pad|=16|(1 if f%180<4 else 0)|(64 if f%500<25 else 128 if f%500>470 else 0)
 if b.ctrl&128:m.nmi()
 run(900<=f<1500)
regions=collections.Counter()
for p,n in counts.items():regions[p>>8]+=n
print('per tick instructions',sum(counts.values())/600,'regions',[(hex(p<<8),n//600) for p,n in regions.most_common(12)])
for a in [0x8109,0xb4b6,0xb4f1,0xb4f3,0xa920,0xb476,0xb3a4,0xaa44,0x8092]:print(hex(a),counts[a],'/600')
for p,n in counts.most_common(45):print('%04x'%p,n,d.instruction_at(p)[1])
(R/'build/heavy-profile.json').write_text(json.dumps(counts))
