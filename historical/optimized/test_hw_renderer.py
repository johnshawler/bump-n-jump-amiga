from pathlib import Path
import ctypes as C,subprocess,random,sys,json
import numpy as np
R=Path(__file__).resolve().parent
# Exercise the exact C grouping and export code; only the 68020 row primitive
# is replaced by its word-for-word portable equivalent on the host.
raw=np.frombuffer((R/'build/sprite-atlas.bin').read_bytes(),dtype='>u2')
(R/'build/host-atlas.c').write_text('#include "../src/engine.h"\nconst u16 sprite_atlas[]={'+','.join(map(str,raw.tolist()))+'};\nconst u8 sprite_nonempty[]={'+','.join(map(str,(R/'build/sprite-nonempty.bin').read_bytes()))+'};\n')
(R/'build/host-rows.c').write_text(r'''
#include "../src/engine.h"
static unsigned read_word(const u8*p){return p[0]*256+p[1];}
static void write_word(u8*p,unsigned v){p[0]=v>>8;p[1]=v;}
void sprite_rows(u8*d,const u16*s,u8*c,u32 n,long step,u32 p2,u32 p3,u32 behind,u32 clip){
 for(unsigned r=0;r<n;r++,s+=step/2,d+=40,c+=32){unsigned a=s[0],b=s[1],m=s[2]&clip,old=read_word(c);write_word(c,old|m);m&=~old;if(behind)m&=~(read_word(d)|read_word(d+28800));if(!m)continue;
 write_word(d,(read_word(d)&~m)|(a&m));write_word(d+28800,(read_word(d+28800)&~m)|(b&m));write_word(d+57600,(read_word(d+57600)&~m)|(p2&m));write_word(d+86400,(read_word(d+86400)&~m)|(p3&m));write_word(d+115200,read_word(d+115200)|m);
 }
}
''')
subprocess.run(['clang','-dynamiclib','-O2','-undefined','dynamic_lookup',str(R/'src/hw_sprites.c'),str(R/'src/render.c'),str(R/'build/host-atlas.c'),str(R/'build/host-rows.c'),'-o',str(R/'build/renderer.dylib')],check=True,capture_output=True)
e=C.CDLL(str(R/'build/engine.dylib'),mode=C.RTLD_GLOBAL);h=C.CDLL(str(R/'build/renderer.dylib'))
state={n:(C.c_ubyte*z).in_dll(e,n) for n,z in [('nt',2048),('oam',256),('pal',32)]}
reg={n:C.c_ubyte.in_dll(e,n) for n in ['ctrl','mask','bank','sy','sx','pad']}
mem=C.create_string_buffer(5*32*480+2*144000+2*8192+640);base=C.addressof(mem)
C.c_void_p.in_dll(h,'mapplanes').value=base
(C.c_void_p*2).in_dll(h,'screens')[:]=[base+76800,base+76800+144000]
(C.c_void_p*2).in_dll(h,'hw_data')[:]=[base+364800,base+364800+8192]
sel=(C.c_ubyte*64).in_dll(h,'hw_selected')
chrdata=np.frombuffer((R/"Bump 'n' Jump (USA).nes").read_bytes()[32784:],np.uint8)
ygrid,xgrid=np.indices((240,256));rng=random.Random(587)
def check(label):
 b=reg['bank'].value;ctrl=reg['ctrl'].value;mask=reg['mask'].value;sy=reg['sy'].value
 nt=np.array(state['nt'],dtype=np.int32);oam=np.array(state['oam']).reshape(64,4)
 yy=(ygrid+sy)%240;page=((((ctrl&2)>>1)+(ygrid+sy)//240)&1)*1024
 tile=nt[page+(yy//8)*32+xgrid//8];attr=nt[page+960+(yy//32)*8+xgrid//32]
 attr=(attr>>(((yy&16)>>2)|((xgrid&16)>>3)))&3
 addr=b*8192+(4096 if ctrl&16 else 0)+tile*16+(yy&7)
 p=((chrdata[addr]>>(7-(xgrid&7)))&1)|(((chrdata[addr+8]>>(7-(xgrid&7)))&1)<<1)
 exp=np.where(p,p+attr*4,0).astype(np.uint8);solid=p!=0;covered=np.zeros((240,256),bool)
 if mask&16:
  for y,t,at,x in oam.tolist():
   y+=1;ht=16 if ctrl&32 else 8
   for j in range(min(ht,240-y)):
    syy=ht-1-j if at&128 else j
    a=b*8192+((t&1)*4096+(t&254)*16+(syy//8)*16+(syy&7) if ht==16 else (4096 if ctrl&8 else 0)+t*16+syy)
    a0=int(chrdata[a]);a1=int(chrdata[a+8])
    for k in range(min(8,256-x)):
     xx=x+k
     if not(mask&4) and xx<8:continue
     bit=k if at&64 else 7-k;p=((a0>>bit)&1)|(((a1>>bit)&1)<<1)
     if p and not covered[y+j,xx]:
      covered[y+j,xx]=1
      if not(at&32 and solid[y+j,xx]):exp[y+j,xx]=16+(at&3)*4+p
 C.c_int.in_dll(e,'all_dirty').value=1;h.render_map();h.render_background(0);h.render_sprites(0);h.render_export(0)
 raw=np.frombuffer(mem,np.uint8,count=51200).reshape(5,256,40)[:,8:248,4:36]
 act=np.sum(np.unpackbits(raw,axis=2)*(1<<np.arange(5))[:,None,None],axis=0,dtype=np.uint8)
 act[act%4==0]=0;bad=np.argwhere(act!=exp)
 if len(bad):raise AssertionError((label,len(bad),[(tuple(q),int(act[tuple(q)]),int(exp[tuple(q)])) for q in bad[:12]]))
 # Every enabled DMA interval must be in bounds and separated from reuse.
 for c in range(8):
  data=(C.c_ushort*512).from_address(base+364800+c*1024);i=0;end=0
  while data[i] or data[i+1]:
   pos,ctl=data[i],data[i+1];start=(pos>>8)+((ctl&4)<<6);stop=(ctl>>8)+((ctl&2)<<7)
   assert start>=end and stop>start and stop<=292,(label,c,start,stop,end)
   end=stop+1;i+=2+2*(stop-start);assert i+1<512
 return sum(v==1 for v in sel)
# Source-generated snapshots span menus, traffic, jumps, crashes and game-over.
e.cpu_run(0);count=0;selected=0
for tick in range(15000):
 p=8 if 180<=tick<185 or (tick>1000 and (C.c_ubyte*2048).in_dll(e,'ram')[20]==2 and tick%100<3) else 0
 if tick>190:p|=16|(1 if tick%180<4 else 0)|(64 if tick%500<25 else 128 if tick%500>470 else 0)
 reg['pad'].value=p;e.cpu_run(bool(reg['ctrl'].value&128))
 C.c_ushort.in_dll(e,'dirtycount').value=0;(C.c_ubyte*2048).in_dll(e,'marked')[:]=bytes(2048)
 if tick%25==0:selected+=check('source '+str(tick));count+=1
for case in range(500):
 reg['bank'].value=rng.randrange(4);reg['ctrl'].value=rng.choice([0,2,16,18]);reg['mask'].value=rng.choice([0x1e,0x1a]);reg['sy'].value=rng.randrange(256)
 state['nt'][:]=rng.randbytes(2048);o=bytearray(rng.randbytes(256))
 # Include coalescible flipped 16x16 cars, clipping and intentional overlaps.
 for i in range(0,48,4):
  x=rng.randrange(249);y=rng.randrange(240);a=rng.choice([0,1,2,3,32,64,128,192])
  for j in range(4):o[(i+j)*4:(i+j)*4+4]=bytes([min(255,y+(j//2)*8),rng.randrange(256),a,min(255,x+(j%2)*8)])
 state['oam'][:]=o;selected+=check('random '+str(case));count+=1
print(json.dumps({'renderer_cases':count,'source_ticks':15000,'hardware_tiles_verified':selected,'pixels_per_case':61440,'mismatches':0}))
(R/'build/hardware-host-verification.json').write_text(json.dumps({'renderer_cases':count,'source_ticks':15000,'hardware_tiles_verified':selected,'pixels_per_case':61440,'mismatches':0},indent=2))
