from pathlib import Path
import runpy,re
R=Path(__file__).resolve().parent
G=runpy.run_path(str(R/'generate.py'));pcs=G['pcs'];prg=G['prg'];meta=G['meta'];length=G['length'];operation=G['operation'];hdr=G['hdr']
# Keep the tested C semantics for uncommon, previously unseen code and for six
# complete, independently checked routines. The primary execution path is 68020.
cpu=(R/'src/cpu.c').read_text();fast={}
for pc in [0x8092,0xaa44,0xb4f1,0xa920,0xb476,0xb3a4]:
 body=cpu.split(f'L{pc:04x}:\n',1)[1].split('\n',1)[0]
 target=int(re.search(r'goto L([0-9a-f]{4});',body).group(1),16)
 fast[pc]=(body,target)
head='''#include "engine.h"
#define PACK ((p&60)|(n&128)|(vflag&64)|c|((z==0)<<1)|32)
#define UNPACK c=p&1;z=(p&2)?0:1;n=vflag=p
#define PUSH(val) do{ram[256+s]=(val);s=(s-1)&255;}while(0)
#define POP() (ram[256+(s=(s+1)&255)])
'''
init='u8 a=cpu.a,x=cpu.x,y=cpu.y,s=cpu.s,p=cpu.p,c=p&1,z=(p&2)?0:1,n=p,vflag=p;u16 pc=cpu.pc,t,u,operand;'
end='done:cpu.a=a;cpu.x=x;cpu.y=y;cpu.s=s;cpu.p=PACK;cpu.pc=pc;'
c=head+'void cpu_fast(unsigned entry){'+init+'switch(entry){\n'
for pc,(body,target) in fast.items():c+=f'case {pc}: '+re.sub(r'goto L[0-9a-f]{4};',f'pc={target};goto done;',body)+'\n'
c+='}'+end+'}\nvoid cpu_fallback(void){'+init+'t=rd(pc);pc=(pc+1)&65535;switch(t){\n'
for code,(op,mode) in enumerate(meta):
 if op=='???':continue
 nn=length[mode];c+=f'case {code}:'
 if nn>1:c+='operand=rd(pc);pc=(pc+1)&65535;'
 if nn>2:c+='operand|=rd(pc)<<8;pc=(pc+1)&65535;'
 c+=operation(op,mode).replace('goto dispatch;','goto done;')+'\n'
c+='default:cpu.error=pc;}'+end+'}\n';(R/'src/cpu_helpers.c').write_text(c)
ALL=set('NZCV')
uses={};defs={};edges={}
for pc in pcs:
 op,mode=meta[prg[pc-32768]];nn=length.get(mode,1);nxt=(pc+nn)&65535
 vv=prg[(pc+1-32768)&32767] if nn>1 else 0
 if nn==3:vv|=prg[(pc+2-32768)&32767]<<8
 use=set();define=set();succ=[nxt]
 if op in ['LDA','LDX','LDY','AND','ORA','EOR','INC','DEC','INX','INY','DEX','DEY','TAX','TAY','TXA','TYA','TSX','PLA']:define=set('NZ')
 if op in ['ADC','SBC']:use=set('C');define=ALL.copy()
 if op in ['CMP','CPX','CPY','ASL','LSR','ROL','ROR']:define=set('NZC')
 if op in ['ROL','ROR']:use=set('C')
 if op=='BIT':define=set('NZV')
 if op in ['CLC','SEC']:define=set('C')
 if op=='CLV':define=set('V')
 if op=='PHP':use=ALL.copy()
 if op in ['PLP','RTI']:define=ALL.copy()
 if mode=='rel':
  use=set('Z' if op in ['BEQ','BNE'] else 'N' if op in ['BMI','BPL'] else 'C' if op in ['BCS','BCC'] else 'V')
  succ=[nxt,(pc+2+(vv if vv<128 else vv-256))&65535]
 if op=='JSR':use=ALL.copy();define=ALL.copy()
 if op=='JMP':
  if mode=='abs':succ=[vv]
  else:succ=[];use=ALL.copy()
 if op in ['RTS','BRK','???']:succ=[];use=ALL.copy()
 if op=='RTI':succ=[]
 if pc in fast:use=ALL.copy();define=ALL.copy();succ=[fast[pc][1]]
 if pc in [0x8070,0x9321]:use|=ALL
 if any(p not in pcs for p in succ):use|=ALL
 uses[pc]=use;defs[pc]=define;edges[pc]=[p for p in succ if p in pcs]
lin={p:set() for p in pcs};lout={p:set() for p in pcs}
changed=True
while changed:
 changed=False
 for pc in sorted(pcs,reverse=True):
  oo=set().union(*(lin[p] for p in edges[pc])) if edges[pc] else set()
  ii=uses[pc]|(oo-defs[pc])
  if ii!=lin[pc] or oo!=lout[pc]:lin[pc]=ii;lout[pc]=oo;changed=True
curr_live=ALL
print('NZ flag writes omitted',sum(2-len(lout[p]&set('NZ')) for p in pcs if defs[p]&set('NZ')))

A=[]
def out(s):A.extend(s.splitlines())
def nz(reg):
 if 'N' in curr_live:out(f'move.b %{reg},%d4')
 if 'Z' in curr_live:out(f'move.b %{reg},%d5')
def imm(v):return f'#{v}'
def save_nz():out('move.l %d4,%a4\nmove.l %d5,%a5')
def restore_nz():out('move.l %a4,%d4\nmove.l %a5,%d5')
def jump(pc):
 if pc in pcs:out(f'bra L{pc:04x}')
 else:out(f'move.l #{pc},cpu+20\nbra dispatch')
def indexed_addr(mode,v,preserve=False):
 # Return an address in a0, preserving the logical flags for stores.
 if preserve:save_nz()
 if mode in ['zpg','abs']:out(f'move.l #{v},%a0')
 elif mode in ['zpx','zpy']:
  rr='d1' if mode=='zpx' else 'd2';out(f'moveq #0,%d4\nmove.b %{rr},%d4\nadd.b #{v},%d4\nmove.l %d4,%a0')
 elif mode in ['abx','aby']:
  rr='d1' if mode=='abx' else 'd2';out(f'move.l %{rr},%a0\nadda.l #{v},%a0')
  if v>0xff00:out('move.l %a0,%d4\nand.l #65535,%d4\nmove.l %d4,%a0')
 elif mode=='inx':
  out(f'moveq #0,%d4\nmove.b %d1,%d4\nadd.b #{v},%d4\nmoveq #0,%d5\nmove.b (%a2,%d4.l),%d5\naddq.b #1,%d4\nmove.b (%a2,%d4.l),%d4\nlsl.w #8,%d4\nmove.b %d5,%d4\nmoveq #0,%d5\nmove.w %d4,%d5\nmove.l %d5,%a0')
 elif mode=='iny':
  out(f'moveq #0,%d4\nmove.b {(v+1)&255}(%a2),%d4\nlsl.w #8,%d4\nmove.b {v}(%a2),%d4\nmove.l %d4,%a0\nadda.l %d2,%a0\nmove.l %a0,%d4\nand.l #65535,%d4\nmove.l %d4,%a0')
 if preserve:restore_nz()
def mem(mode,v,reg='d4'):
 if mode=='imm':out(f'move.b #{v},%{reg}');return
 if mode=='acc':out(f'move.b %d0,%{reg}');return
 if mode in ['abs','zpg'] and v<0x2000:out(f'move.b {v&2047}(%a2),%{reg}');return
 if mode in ['abx','aby'] and v<0x700:
  rr='d1' if mode=='abx' else 'd2';out(f'move.b {v}(%a2,%{rr}.l),%{reg}');return
 if mode in ['abx','aby'] and 0x8000<=v<=0xff00:
  rr='d1' if mode=='abx' else 'd2';out(f'move.b {v-0x8000}(%a3,%{rr}.l),%{reg}');return
 if mode=='abs' and v>=0x8000:out(f'move.b {v-0x8000}(%a3),%{reg}');return
 indexed_addr(mode,v);out('bsr bus_read')
 if reg!='d4':out(f'move.b %d4,%{reg}')
def write(mode,v,reg):
 if mode=='acc':out(f'move.b %{reg},%d0');return
 if mode in ['abs','zpg'] and v<0x2000:out(f'move.b %{reg},{v&2047}(%a2)');return
 if mode in ['abx','aby'] and v<0x700:
  rr='d1' if mode=='abx' else 'd2';out(f'move.b %{reg},{v}(%a2,%{rr}.l)');return
 # The address builder may use d4/d5; preserve the operand in a1 first.
 out(f'move.l %{reg},%a1');indexed_addr(mode,v,True);out('bsr bus_write')

out('''.section .text.cpu_run,"ax"
.globl cpu_run
cpu_run:
movem.l %d2-%d7/%a2-%a6,-(%sp)
lea ram,%a2
lea prg,%a3
bsr load_state
tst.l 48(%sp)
beq dispatch
move.l %d4,%a4
move.l %d5,%a5
moveq #0,%d4
move.w cpu+22,%d4
lsr.w #8,%d4
move.b %d4,256(%a2,%d3.l)
subq.b #1,%d3
move.b cpu+23,256(%a2,%d3.l)
subq.b #1,%d3
move.l %a4,%d4
move.l %a5,%d5
bsr pack_status
and.b #239,%d4
move.b %d4,256(%a2,%d3.l)
subq.b #1,%d3
move.l %a4,%d4
move.l %a5,%d5
or.b #4,cpu+19
bra L81f9

dispatch:
move.l %d4,%a4
moveq #0,%d4
move.w cpu+22,%d4
cmp.w #0x8000,%d4
bcs fallback_entry
eor.w #0x8000,%d4
lea jump_table,%a0
move.l (%a0,%d4.l*4),%a0
cmpa.l #0,%a0
beq fallback_entry
move.l %a4,%d4
jmp (%a0)
fallback_entry:
move.l %a4,%d4
bsr save_state
jsr cpu_fallback
bsr load_state
tst.l cpu+24
bne finish
bra dispatch
finish:
bsr save_state
movem.l (%sp)+,%d2-%d7/%a2-%a6
rts

load_state:
move.l cpu,%d0
move.l cpu+4,%d1
move.l cpu+8,%d2
move.l cpu+12,%d3
move.l cpu+16,%d4
move.l %d4,%d6
and.l #1,%d6
move.l %d4,%d7
and.l #64,%d7
moveq #1,%d5
btst #1,%d4
beq 1f
moveq #0,%d5
1:rts

pack_status:
move.l %d4,%a4
move.l %d5,%a5
and.b #128,%d4
or.b %d6,%d4
or.b %d7,%d4
tst.b %d5
bne 1f
or.b #2,%d4
1:move.b cpu+19,%d5
and.b #60,%d5
or.b %d5,%d4
or.b #32,%d4
rts
save_state:
move.l %d0,cpu
move.l %d1,cpu+4
move.l %d2,cpu+8
move.l %d3,cpu+12
bsr pack_status
moveq #0,%d5
move.b %d4,%d5
move.l %d5,cpu+16
move.l %a4,%d4
move.l %a5,%d5
rts

bus_read:
cmpa.l #0x800,%a0
bcs 1f
cmpa.l #0x2000,%a0
bcs 2f
cmpa.l #0x8000,%a0
bcc 3f
movem.l %d0-%d1/%a0-%a1,-(%sp)
move.l %a0,-(%sp)
jsr io_read
addq.l #4,%sp
move.b %d0,%d4
movem.l (%sp)+,%d0-%d1/%a0-%a1
rts
1:move.b (%a2,%a0.l),%d4
rts
2:move.l %a0,%d4
and.l #2047,%d4
move.b (%a2,%d4.l),%d4
rts
3:move.l %a0,%d4
sub.l #0x8000,%d4
move.b (%a3,%d4.l),%d4
rts
bus_write:
move.l %d4,%a4
cmpa.l #0x800,%a0
bcs 1f
cmpa.l #0x2000,%a0
bcs 2f
movem.l %d0-%d1,-(%sp)
move.l %a1,-(%sp)
move.l %a0,-(%sp)
jsr io_write
addq.l #8,%sp
movem.l (%sp)+,%d0-%d1
move.l %a4,%d4
rts
1:move.l %a1,%d4
move.b %d4,(%a2,%a0.l)
move.l %a4,%d4
rts
2:move.l %a0,%d4
and.l #2047,%d4
lea (%a2,%d4.l),%a0
move.l %a1,%d4
move.b %d4,(%a0)
move.l %a4,%d4
rts
''')
ordered=sorted(pcs)
for ix,pc in enumerate(ordered):
 curr_live=lout[pc]
 op,mode=meta[prg[pc-32768]];nn=length.get(mode,1);v=prg[(pc+1-32768)&32767] if nn>1 else 0
 if nn==3:v|=prg[(pc+2-32768)&32767]<<8
 nxt=(pc+nn)&65535;following=ordered[ix+1] if ix+1<len(ordered) else None
 out(f'L{pc:04x}:')
 if pc==0x8070:out('tst.b 14(%a2)\nbne 1f\nmove.l #0x8070,cpu+20\nbra finish\n1:')
 if pc==0x9321:out('tst.b 0x401(%a2)\nbeq 1f\nmove.l #0x9321,cpu+20\nbra finish\n1:')
 if pc in fast:
  target=fast[pc][1];out(f'move.l #{pc},cpu+20\nbsr save_state\npea {pc}\njsr cpu_fast\naddq.l #4,%sp\nbsr load_state\nbra L{target:04x}');continue
 if mode=='rel':
  target=(pc+2+(v if v<128 else v-256))&65535
  if op in ['BEQ','BNE']:out('tst.b %d5');cond='beq' if op=='BEQ' else 'bne'
  elif op in ['BMI','BPL']:out('btst #7,%d4');cond='bne' if op=='BMI' else 'beq'
  elif op in ['BCS','BCC']:out('tst.b %d6');cond='bne' if op=='BCS' else 'beq'
  else:out('btst #6,%d7');cond='bne' if op=='BVS' else 'beq'
  if target in pcs:out(f'{cond} L{target:04x}')
  else:out(f'{cond} 1f\nbra 2f\n1:move.l #{target},cpu+20\nbra dispatch\n2:')
 elif op in ['LDA','LDX','LDY']:
  reg={'LDA':'d0','LDX':'d1','LDY':'d2'}[op];mem(mode,v,reg);nz(reg)
 elif op in ['STA','STX','STY']:write(mode,v,{'STA':'d0','STX':'d1','STY':'d2'}[op])
 elif op in ['AND','ORA','EOR']:
  mem(mode,v);out(f'{ {"AND":"and","ORA":"or","EOR":"eor"}[op]}.b %d4,%d0');nz('d0')
 elif op in ['ADC','SBC']:
  mem(mode,v)
  if op=='SBC':out('not.b %d4')
  out('lsr.b #1,%d6\naddx.b %d4,%d0')
  if 'V' in curr_live:
   out('move.w %ccr,%d7')
   if 'C' in curr_live:out('move.b %d7,%d6\nand.b #1,%d6')
   out('lsl.b #5,%d7\nand.b #64,%d7')
  elif 'C' in curr_live:out('scs %d6\nneg.b %d6')
  nz('d0')
 elif op in ['CMP','CPX','CPY']:
  mem(mode,v);reg={'CMP':'d0','CPX':'d1','CPY':'d2'}[op]
  if curr_live&set('NZ'):
   out(f'move.b %{reg},%d5\nsub.b %d4,%d5')
   if 'C' in curr_live:out('scc %d6\nneg.b %d6')
   if 'N' in curr_live:out('move.b %d5,%d4')
  elif 'C' in curr_live:out(f'cmp.b %d4,%{reg}\nscc %d6\nneg.b %d6')
 elif op in ['INC','DEC']:
  mem(mode,v);out(f'{"addq" if op=="INC" else "subq"}.b #1,%d4')
  if 'Z' in curr_live:out('move.b %d4,%d5')
  write(mode,v,'d4')
 elif op in ['INX','INY','DEX','DEY']:
  reg='d1' if op[-1]=='X' else 'd2';out(f'{"addq" if op[0]=="I" else "subq"}.b #1,%{reg}');nz(reg)
 elif op in ['TAX','TAY','TXA','TYA','TSX','TXS']:
  regs={'A':'d0','X':'d1','Y':'d2','S':'d3'};src=regs[op[1]];dst=regs[op[2]];out(f'move.b %{src},%{dst}')
  if op!='TXS':nz(dst)
 elif op in ['ASL','LSR','ROL','ROR']:
  mem(mode,v)
  if op in ['ROL','ROR']:out('lsr.b #1,%d6')
  out(f'{ {"ASL":"lsl","LSR":"lsr","ROL":"roxl","ROR":"roxr"}[op]}.b #1,%d4')
  if 'C' in curr_live:out('scs %d6\nneg.b %d6')
  if 'Z' in curr_live:out('move.b %d4,%d5')
  write(mode,v,'d4')
 elif op=='BIT':
  mem(mode,v)
  if 'V' in curr_live:out('move.b %d4,%d7\nand.b #64,%d7')
  if 'Z' in curr_live:out('move.b %d0,%d5\nand.b %d4,%d5')
 elif op in ['CLC','SEC']:out('moveq #'+('0' if op=='CLC' else '1')+',%d6')
 elif op=='CLV':out('moveq #0,%d7')
 elif op in ['CLI','SEI','CLD','SED']:
  bit=4 if op[-1]=='I' else 8
  out(f'{"or" if op[0]=="S" else "and"}.b #{bit if op[0]=="S" else 255-bit},cpu+19')
 elif op=='PHA':out('move.b %d0,256(%a2,%d3.l)\nsubq.b #1,%d3')
 elif op=='PLA':out('addq.b #1,%d3\nmove.b 256(%a2,%d3.l),%d0');nz('d0')
 elif op=='PHP':out('bsr pack_status\nor.b #48,%d4\nmove.b %d4,256(%a2,%d3.l)\nsubq.b #1,%d3');restore_nz()
 elif op in ['PLP','RTI']:
  out('addq.b #1,%d3\nmoveq #0,%d4\nmove.b 256(%a2,%d3.l),%d4\nor.b #48,%d4\nmove.l %d4,cpu+16\nmove.b %d4,%d6\nand.b #1,%d6\nmove.b %d4,%d7\nand.b #64,%d7\nmoveq #1,%d5\nbtst #1,%d4\nbeq 1f\nmoveq #0,%d5\n1:')
  if op=='RTI':
   save_nz();out('addq.b #1,%d3\nmoveq #0,%d4\nmove.b 256(%a2,%d3.l),%d4\naddq.b #1,%d3\nmoveq #0,%d5\nmove.b 256(%a2,%d3.l),%d5\nlsl.w #8,%d5\nor.w %d5,%d4\nmove.w %d4,cpu+22');restore_nz();out('bra dispatch');continue
 elif op=='JSR':
  ret=(pc+2)&65535;out(f'move.b #{ret>>8},256(%a2,%d3.l)\nsubq.b #1,%d3\nmove.b #{ret&255},256(%a2,%d3.l)\nsubq.b #1,%d3');jump(v);continue
 elif op=='RTS':
  save_nz();out('addq.b #1,%d3\nmoveq #0,%d4\nmove.b 256(%a2,%d3.l),%d4\naddq.b #1,%d3\nmoveq #0,%d5\nmove.b 256(%a2,%d3.l),%d5\nlsl.w #8,%d5\nor.w %d5,%d4\naddq.w #1,%d4\nmove.w %d4,cpu+22');restore_nz();out('bra dispatch');continue
 elif op=='JMP':
  if mode=='abs':jump(v)
  elif v<0x800:
   save_nz();out(f'moveq #0,%d4\nmove.b {((v&0xff00)|((v+1)&255))}(%a2),%d4\nlsl.w #8,%d4\nmove.b {v}(%a2),%d4\nmove.w %d4,cpu+22');restore_nz();out('bra dispatch')
  else:out(f'move.l #{pc},cpu+20\nbra fallback_entry_direct')
  continue
 elif op=='NOP':pass
 else:out(f'move.l #{pc},cpu+24\nmove.l #{pc},cpu+20\nbra finish');continue
 if following!=nxt:jump(nxt)

out('fallback_entry_direct:\nbsr save_state\njsr cpu_fallback\nbsr load_state\nbra dispatch')
out('.section .rodata.jump_table,"a"\n.balign 4\njump_table:')
for n in range(0x8000,0x10000):out(f'.long L{n:04x}' if n in pcs else '.long 0')
branchmap={'bra':'jra','bsr':'jbsr','beq':'jeq','bne':'jne','bcs':'jcs','bcc':'jcc','bmi':'jmi','bpl':'jpl','bhi':'jhi','bls':'jls'}
A=[branchmap.get(line.split(' ')[0],line.split(' ')[0])+line[len(line.split(' ')[0]):] for line in A]
(R/'src/cpu_native.s').write_text('\n'.join(A)+'\n');print('Native assembly lines',len(A),'helper C bytes',len(c))
