from pathlib import Path
import sys,json
from py65.devices.mpu6502 import MPU
R=Path(__file__).resolve().parent;rom=(R/"Bump 'n' Jump (USA).nes").read_bytes();prg=rom[16:32784];chr=rom[32784:]
(R/'src/assets.c').write_text('#include "engine.h"\nconst u8 prg[32768]={'+','.join(map(str,prg))+'};\nconst u8 chr[32768]={'+','.join(map(str,chr))+'};\n')
meta=MPU.disassemble;length={'imp':1,'acc':1,'imm':2,'zpg':2,'zpx':2,'zpy':2,'inx':2,'iny':2,'rel':2,'abs':3,'abx':3,'aby':3,'ind':3}
trace=json.loads((R/'build/trace.json').read_text());pcs=set(trace['pcs'])|{0x8000,0x81f9}
# Decode all direct paths, including branches not exercised by the driving trace.
q=list(pcs)
while q:
 pc=q.pop();op,mode=meta[prg[pc-32768]]
 if op=='???':continue
 n=length[mode];v=prg[(pc+1-32768)&32767] if n>1 else 0
 if n==3:v|=prg[(pc+2-32768)&32767]<<8
 nxt=[]
 if mode=='rel':nxt+=[(pc+2+(v if v<128 else v-256))&65535,pc+n]
 elif op=='JSR':nxt +=[v,pc+n]
 elif op=='JMP' and mode=='abs':nxt +=[v]
 elif op not in ['JMP','RTI','RTS','BRK']:nxt +=[pc+n]
 for a in nxt:
  if 32768<=a<65536 and a not in pcs:pcs.add(a);q.append(a)
# Dispatch table accessed by main menu and NMI. Add all source state functions.
for lo,hi in [(0x822c,0x825a),(0x91f8,0x9208)]:
 for addr in range(lo,hi,2):pcs.add(prg[addr-32768]|prg[addr-32767]<<8)

def operation(op,mode,pc=None):
 static=pc is not None;n=length.get(mode,1)
 if static:
  v=prg[(pc+1-32768)&32767] if n>1 else 0
  if n==3:v|=prg[(pc+2-32768)&32767]<<8
  imm=str(v);nextpc=(pc+n)&65535
  start=''
 else:imm='operand';nextpc=None;start=''
 if mode in ['zpg','abs']:addr=imm
 elif mode=='zpx':addr=f'(({imm}+x)&255)'
 elif mode=='zpy':addr=f'(({imm}+y)&255)'
 elif mode=='abx':addr=f'(({imm}+x)&65535)'
 elif mode=='aby':addr=f'(({imm}+y)&65535)'
 elif mode=='inx':addr=f'(ram[({imm}+x)&255]|(ram[({imm}+x+1)&255]<<8))'
 elif mode=='iny':addr=f'(((ram[{imm}]|(ram[({imm}+1)&255]<<8))+y)&65535)'
 else:addr='0'
 val=imm if mode=='imm' else 'a' if mode=='acc' else f'rd({addr})'
 def nz(v):return f'p=(p&125)|({v}&128)|(({v}==0)<<1);'
 def put(v):return f'a={v};' if mode=='acc' else f'wr({addr},{v});'
 def jump(target):return f'goto L{target:04x};' if static and target in pcs else f'pc={target};goto dispatch;'
 cont=jump(nextpc) if static else 'goto dispatch;'
 if mode=='rel':
  cond={'BCC':'!(p&1)','BCS':'p&1','BEQ':'p&2','BNE':'!(p&2)','BMI':'p&128','BPL':'!(p&128)','BVC':'!(p&64)','BVS':'p&64'}[op]
  if static:targ=(pc+2+(v if v<128 else v-256))&65535;return f'if({cond}){{{jump(targ)}}}{cont}'
  return f'if({cond})pc=(pc+(signed char)operand)&65535;goto dispatch;'
 if op in ['LDA','LDX','LDY']:
  r=op[-1].lower();s=f'{r}={val};'+nz(r)
 elif op in ['STA','STX','STY']:s=f'wr({addr},{op[-1].lower()});'
 elif op in ['AND','ORA','EOR']:
  oper={'AND':'&','ORA':'|','EOR':'^'}[op];s=f'a {oper}= {val};'+nz('a')
 elif op in ['ADC','SBC']:
  s=f't={val};'
  if op=='SBC':s+='t^=255;'
  s+='u=a+t+(p&1);p=(p&60)|((~(a^t)&(a^u)&128)>>1)|((u>255)?1:0);a=u&255;'+nz('a')
 elif op in ['CMP','CPX','CPY']:
  r='a' if op=='CMP' else op[-1].lower();s=f't={val};u=({r}-t)&255;p=(p&124)|({r}>=t);'+nz('u')
 elif op in ['INC','DEC']:s=f't=({val}{"+" if op=="INC" else "-"}1)&255;'+put('t')+nz('t')
 elif op in ['INX','INY','DEX','DEY']:
  r=op[-1].lower();s=f'{r}=({r}{"+" if op[0]=="I" else "-"}1)&255;'+nz(r)
 elif op in ['TAX','TAY','TXA','TYA','TSX','TXS']:
  f=op[1].lower();t=op[2].lower();s=f'{t}={f};'+('' if op=='TXS' else nz(t))
 elif op in ['ASL','LSR','ROL','ROR']:
  s=f't={val};'
  if op in ['ASL','ROL']:s+=f'u=((t<<1){"|(p&1)" if op=="ROL" else ""})&255;p=(p&126)|(t>>7);'
  else:s+=f'u=(t>>1){"|((p&1)<<7)" if op=="ROR" else ""};p=(p&126)|(t&1);'
  s+=put('u')+nz('u')
 elif op=='BIT':s=f't={val};p=(p&61)|(t&192)|(((a&t)==0)<<1);'
 elif op in ['CLC','SEC','CLI','SEI','CLD','SED','CLV']:
  bit={'CLC':1,'SEC':1,'CLI':4,'SEI':4,'CLD':8,'SED':8,'CLV':64}[op];s=f'p{ "|=" if op.startswith("SE") else "&="}{bit if op.startswith("SE") else 255-bit};'
 elif op in ['PHA','PHP']:s=f'PUSH({"a" if op=="PHA" else "p|48"});'
 elif op in ['PLA','PLP']:s=f'{"a" if op=="PLA" else "p"}=POP();'+(nz('a') if op=='PLA' else 'p=p|48;')
 elif op=='JSR':
  ret=(nextpc-1)&65535 if static else '((pc-1)&65535)'
  s=f'PUSH(({ret})>>8);PUSH(({ret})&255);'
  return s+(jump(v) if static else 'pc=operand;goto dispatch;')
 elif op=='RTS':return 't=POP();u=POP();pc=((t|(u<<8))+1)&65535;goto dispatch;'
 elif op=='RTI':return 'p=POP()|48;t=POP();u=POP();pc=t|(u<<8);goto dispatch;'
 elif op=='JMP':
  if mode=='abs':return jump(v) if static else 'pc=operand;goto dispatch;'
  return f't=rd({imm});u=rd((({imm})&65280)|((({imm})+1)&255));pc=t|(u<<8);goto dispatch;'
 elif op=='BRK':return 'cpu.error=pc;goto done;'
 elif op=='NOP':s=''
 else:return 'cpu.error=pc;goto done;'
 return s+cont

hdr='''#include "engine.h"
#define PUSH(val) do{ram[256+s]=(val);s=(s-1)&255;}while(0)
#define POP() (ram[256+(s=(s+1)&255)])
void cpu_run(int interrupt){
 unsigned a=cpu.a,x=cpu.x,y=cpu.y,s=cpu.s,p=cpu.p,pc=cpu.pc,t,u,operand;
 unsigned guard=0;
 if(interrupt){PUSH(pc>>8);PUSH(pc&255);PUSH(p&239);p|=4;pc=0x81f9;}
 goto dispatch;
'''
# One large native function, direct branch labels; only indirect returns dispatch.
s=hdr+'static void *const targets[32768]={\n'
for pc in sorted(pcs):s+=f'[{pc-32768}]=&&L{pc:04x},\n'
s+='};\ndispatch:\n if(++guard>40000){cpu.error=pc;goto done;}\n if((pc==0x8070 && !ram[14]) || (pc==0x9321 && ram[0x401]))goto done;\n if(pc>=32768 && targets[pc-32768])goto *targets[pc-32768];goto fallback;\n'
for pc in sorted(pcs):
 if not(0x8000<=pc<=0xffff):continue
 op,mode=meta[prg[pc-32768]]
 s+=f'L{pc:04x}:\n'
 if pc==0x8070:s+='if(!ram[14]){pc=0x8070;goto done;}\n'
 if pc==0x9321:s+='if(ram[0x401]){pc=0x9321;goto done;}\n'
 s+=operation(op,mode,pc)+'\n'
s+='fallback: t=rd(pc);pc=(pc+1)&65535;switch(t){\n'
for code,(op,mode) in enumerate(meta):
 if op=='???':continue
 n=length[mode];s+=f'case {code}: '
 if n>1:s+='operand=rd(pc);pc=(pc+1)&65535;'
 if n>2:s+='operand|=rd(pc)<<8;pc=(pc+1)&65535;'
 s+=operation(op,mode)+'\n'
s+='default:cpu.error=pc;goto done;}\ndone:cpu.a=a;cpu.x=x;cpu.y=y;cpu.s=s;cpu.p=p;cpu.pc=pc;cpu.dispatches=guard;\n}\n'
(R/'src/cpu.c').write_text(s)
print('Static addresses',len(pcs),'C bytes',len(s))
