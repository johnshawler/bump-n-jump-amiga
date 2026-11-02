from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from reference import Bus,MPU,render
rows=[];meta=[]
for choice in range(16):
 b=Bus();b.oam[:]=bytes(256);m=MPU(memory=b,pc=None);injected=False;active=0
 for tick in range(1100):
  b.pad=8 if 180<=tick<185 else 0
  if tick and b.ctrl&128:m.nmi()
  for i in range(100000):
   if (m.pc==0x8070 and not b.ram[14])or(m.pc==0x9321 and b.ram[0x401]):break
   m.step()
  else:raise RuntimeError('stuck')
  if b.ram[20]==4 and not injected:b.ram[0x3c]=choice;injected=True
  if b.ram[20]==12:
   active+=1
   if active==10:break
 assert injected and b.ram[0x56]==choice and active==10
 # Preview is a source snapshot, not another copy of the gameplay engine.
 raw=bytes(b.nt+b.oam+b.pal+bytes([b.ctrl,b.mask,b.bank,b.sx,b.sy]));rows.append(raw)
 render(b,R/'stage-select'/('stage-%02d.png'%(choice+1)))
 meta.append(dict(stage=choice+1,source_tick=tick,bank=b.bank,ctrl=b.ctrl,scroll=[b.sx,b.sy],sha256=hashlib.sha256(raw).hexdigest()))
(R/'src/stage_previews.c').write_text('#include "engine.h"\n/* Original-ROM snapshots: NT, OAM, palette, control/mask/bank/scroll. */\nconst u8 stage_previews[16][2341]={\n'+',\n'.join('{'+','.join(map(str,r))+'}' for r in rows)+'};\n')
(R/'stage-select/previews.json').write_text(json.dumps(meta,indent=2));print('16 original stage previews generated')
