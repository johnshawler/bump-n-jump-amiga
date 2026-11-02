from pathlib import Path
from py65.devices.mpu6502 import MPU
from py65.disassembler import Disassembler
import json, collections, sys
R=Path(__file__).resolve().parent
rom=(R/"Bump 'n' Jump (USA).nes").read_bytes()
class Bus:
 def __init__(self):
  self.ram=bytearray(2048);self.nt=bytearray(2048);self.pal=bytearray(32);self.oam=bytearray([240]*256);self.apu=bytearray(32)
  self.ctrl=self.mask=self.addr=self.tmp=self.toggle=self.buf=self.oa=self.bank=self.sx=self.sy=self.pad=self.strobe=self.joy=0
 def __getitem__(self,a):
  a &=65535
  if a<0x2000:return self.ram[a&2047]
  if a>=0x8000:return rom[16+a-0x8000]
  if a<0x4000:
   r=a&7
   if r==2:self.toggle=0;return 0xc0
   if r==4:return self.oam[self.oa]
   if r==7:
    old=self.addr;v=self.ppuread(self.addr);b=self.buf;self.buf=v;self.addr=(self.addr+(32 if self.ctrl&4 else 1))&0x3fff
    return v if old>=0x3f00 else b
  if a==0x4016:
   v=(self.joy&1)|0x40
   if not self.strobe:self.joy=(self.joy>>1)|0x80
   return v
  return 0
 def ppuread(self,a):
  a &=0x3fff
  if a<0x2000:return rom[32784+self.bank*8192+a]
  if a<0x3f00:return self.nt[((a&0x800)>>1)|(a&1023)]
  q=a&31
  if q&19==16:q &=15
  return self.pal[q]
 def __setitem__(self,a,v):
  a &=65535;v &=255
  if a<0x2000:self.ram[a&2047]=v;return
  if a>=0x8000:self.bank=v&3;return
  if a<0x4000:
   r=a&7
   if r==0:self.ctrl=v;self.tmp=(self.tmp&0x73ff)|((v&3)<<10)
   elif r==1:self.mask=v
   elif r==3:self.oa=v
   elif r==4:self.oam[self.oa]=v;self.oa=(self.oa+1)&255
   elif r==5:
    if not self.toggle:self.sx=v;self.tmp=(self.tmp&0x7fe0)|(v>>3)
    else:self.sy=v;self.tmp=(self.tmp&0x0c1f)|((v&7)<<12)|((v&0xf8)<<2)
    self.toggle^=1
   elif r==6:
    if not self.toggle:self.tmp=(self.tmp&255)|((v&63)<<8)
    else:self.tmp=(self.tmp&0x7f00)|v;self.addr=self.tmp
    self.toggle^=1
   elif r==7:
    q=self.addr&0x3fff
    if 0x2000<=q<0x3f00:self.nt[((q&0x800)>>1)|(q&1023)]=v
    elif q>=0x3f00:
     q &=31
     if q&19==16:q &=15
     self.pal[q]=v&63
    self.addr=(self.addr+(32 if self.ctrl&4 else 1))&0x3fff
   return
  if a==0x4014:self.oam[:]=self.ram[(v*256)&2047:((v*256)&2047)+256]
  elif a==0x4016:
   self.strobe=v&1
   if self.strobe:self.joy=self.pad
  elif 0x4000<=a<0x4020:self.apu[a-0x4000]=v

def render(b,path):
 from PIL import Image
 palette=bytes.fromhex('666666002a881412a73b00a45c007e6e00406c0600561d003335000b4800005200004f0800404d000000000000000000adadad155fd94240ff7527fea01accb71e7bb531208447004e60001e7b000c85001d8048006e89000000000000000000fffeff64b0ff9290ffc676fff36afffe6eccfe8170ea9e22bcbe0088d8005ce43045e08248cdde4f4f4f000000000000fffeffc0dfffd3d2ffe8c8fffbc2ff fec4eaf eccc5f7d8a5e4e594cfef96bdf4abb3f3ccb5ebf2b8b8b8000000000000'.replace(' ',''))
 # Use a fixed established NES RGB palette.
 colors=[tuple(palette[i:i+3]) for i in range(0,len(palette),3)]
 out=Image.new('RGB',(256,240));pix=out.load();solid=[[False]*256 for _ in range(240)]
 for y in range(240):
  yy=(y+b.sy)%480;n=(b.ctrl&2)*512+(y+b.sy)//240*1024
  yy%=240
  for x in range(256):
   xx=(x+b.sx)&255;ntbase=(((b.ctrl&2)*512+(y+b.sy)//240*1024)&1024)
   tile=b.nt[ntbase+(yy//8)*32+xx//8];at=b.nt[ntbase+960+(yy//32)*8+xx//32]
   col=(at>>(((yy&16)>>2)|((xx&16)>>3)))&3
   a=(0x1000 if b.ctrl&16 else 0)+tile*16+(yy&7)
   p=((b.ppuread(a)>>(7-(xx&7)))&1)|(((b.ppuread(a+8)>>(7-(xx&7)))&1)<<1)
   solid[y][x]=bool(p);c=b.pal[col*4+p] if p else b.pal[0]
   pix[x,y]=colors[c%64]
 for i in range(63,-1,-1):
  yy,t,at,xx=b.oam[i*4:i*4+4];h=16 if b.ctrl&32 else 8
  for j in range(h):
   y=yy+1+j
   if y>=240:continue
   sy=h-1-j if at&128 else j
   a=((t&1)*4096+(t&254)*16+(sy//8)*16+(sy&7)) if h==16 else ((4096 if b.ctrl&8 else 0)+t*16+sy)
   p0=b.ppuread(a);p1=b.ppuread(a+8)
   for k in range(8):
    x=xx+k
    if x>=256:continue
    bit=k if at&64 else 7-k;p=((p0>>bit)&1)|(((p1>>bit)&1)<<1)
    if p and not(at&32 and solid[y][x]):pix[x,y]=colors[b.pal[16+(at&3)*4+p]%64]
 out.save(path)

def main():
 b=Bus();m=MPU(memory=b,pc=None);seen=set();counts=collections.Counter();frames=int(sys.argv[1]) if len(sys.argv)>1 else 4000
 checks=[]
 for frame in range(frames):
  # Start the original title menu, then steer, jump and run through deaths.
  b.pad=8 if frame in range(180,185) or (frame>1000 and b.ram[0x14]==2 and frame%100<3) else 0
  if frame>190:
   if frame%180<4:b.pad|=1
   if frame%500<25:b.pad|=64
   elif frame%500>470:b.pad|=128
   b.pad |=16
  if frame and b.ctrl&128:m.nmi()
  steps=0
  while steps<100000:
   if (m.pc==0x8070 and b.ram[14]==0) or (m.pc==0x9321 and b.ram[0x401]):break
   seen.add(m.pc);counts[m.pc]+=1;m.step();steps+=1
  if steps==100000:print('stuck',frame,hex(m.pc));break
  if frame in [0,179,189,300,600,1000,2000,frames-1]:
   render(b,R/f'build/ref-{frame}.png');checks.append([frame,steps,hex(m.pc),list(b.ram[0x14:0x16]),b.ctrl,b.bank,b.sx,b.sy]);print(checks[-1])
 (R/'build/trace.json').write_text(json.dumps({'pcs':sorted(seen),'counts':counts,'checkpoints':checks}))
 (R/'build/reference-state.bin').write_bytes(bytes([m.a,m.x,m.y,m.sp,m.p])+m.pc.to_bytes(2,'little')+b.ram+b.nt+b.pal+b.oam)
 print('unique',len(seen),'total',sum(counts.values()),'top',counts.most_common(20))
if __name__=='__main__':main()
