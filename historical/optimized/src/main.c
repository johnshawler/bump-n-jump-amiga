#include "engine.h"
#include <exec/execbase.h>
#include <graphics/gfxbase.h>
#include <proto/exec.h>
#include <proto/graphics.h>
#include <proto/dos.h>
#ifndef AUTOTEST
#define AUTOTEST 0
#endif
#define R16(o) (*(volatile u16*)(0xdff000+(o)))
#define R32(o) (*(volatile u32*)(0xdff000+(o)))
#define CIAA(o) (*(volatile u8*)(0xbfe001+(o)*256))
struct ExecBase *SysBase;
struct GfxBase *GfxBase;
struct DosLibrary *DOSBase;
extern u8 *mapplanes,*screens[2],*waves;
extern u16 *coppers[2];
extern u32 get_vbr(void);
extern void vblank_irq(void);
extern void render_map(void),render_background(unsigned),render_sprites(unsigned),render_copper(unsigned),render_export(unsigned);
extern void audio_init(void),audio_tick(void),audio_publish(void);
volatile u32 fields;
volatile u32 source_ticks,publications,max_elapsed,max_cpu_fields,max_render_fields;
volatile u32 test_control;
extern u32 full_redraws,total_dirty_tiles;
static u32 cpu_lines,render_lines,idle_lines;
static unsigned beam_line(void){u16 hi,lo,again;do{hi=R16(4)&1;lo=R16(6)>>8;again=R16(4)&1;}while(hi!=again);return (hi<<8)|lo;}
static u32 stamp(void){u32 a,b;unsigned line;do{a=fields;line=beam_line();b=fields;}while(a!=b);return a*312+line;}
static void wait_publish(void){
 /* Sprite DMA fetches the initial control words before the visible area. */
 for(;;){unsigned line=beam_line();if(line<20 || line>=296)return;}
}
static u8 inputlog[16384];
static u8 keys[128];
static u8 *arena;
static u32 arena_size=5*32*480+2*5*40*720+2048+2*8*1024;
static struct View *oldview;
static u32 oldirq,*irqvec;
static u16 olddma,oldint,oldadk;
static void wait_field(void){u32 now=fields;while(fields==now){}}
static void keyboard_poll(void){
 if(CIAA(13)&8){unsigned raw=CIAA(12);raw=(~((raw>>1)|(raw<<7)))&255;keys[raw&127]=(raw&128)?0:1;
  unsigned control=CIAA(14);CIAA(14)=control|64;
  u32 now=fields;unsigned beam=R16(6)>>8;while(fields==now && ((unsigned)(R16(6)>>8)-beam+256)%256<3){}
  CIAA(14)=control&~64;
 }
}
static u8 read_controls(void){
 keyboard_poll();unsigned j=R16(0xc),v=0;
 unsigned left=(j&0x200)!=0,right=(j&2)!=0,up=((j^(j<<1))&0x200)!=0,down=((j^(j<<1))&2)!=0;
 if(left||keys[0x4f]||keys[0x20])v|=64;
 if(right||keys[0x4e]||keys[0x22])v|=128;
 if(up||keys[0x4c]||keys[0x11])v|=16;
 if(down||keys[0x4d]||keys[0x21])v|=32;
 int fire=!(CIAA(0)&128)||keys[0x40]||keys[0x63];
 if(fire){if(ram[0x14]==2||ram[0x14]==3)v|=8;else v|=1;}
 if(keys[0x44])v|=8;
 if(keys[0x60]||keys[0x61])v|=2;
 if(keys[0x42])v|=4;
 return v;
}
static void takeover(void){
 oldview=GfxBase->ActiView;
 olddma=R16(2);oldint=R16(0x1c);oldadk=R16(0x10);
 LoadView(0);WaitTOF();WaitTOF();OwnBlitter();WaitBlit();Forbid();Disable();
 R16(0x9a)=0x7fff;R16(0x9c)=0x7fff;R16(0x96)=0x7fff;R16(0x9e)=0x7fff;
 irqvec=(u32*)(get_vbr()+0x6c);oldirq=*irqvec;*irqvec=(u32)vblank_irq;
 render_copper(0);R32(0x80)=(u32)coppers[0];R16(0x88)=0;
 audio_init();R16(0x96)=0x83ef;R16(0x9a)=0xc020;Enable();
}
static void restore(void){
 Disable();R16(0x9a)=0x7fff;R16(0x9c)=0x7fff;R16(0x96)=0x7fff;
 for(unsigned c=0;c<4;c++)R16(0xa8+c*16)=0;
 *irqvec=oldirq;R16(0x9e)=0x7fff;R16(0x9e)=oldadk|0x8000;
 R32(0x80)=(u32)GfxBase->copinit;R16(0x88)=0;R16(0x9a)=oldint|0x8000;R16(0x96)=olddma|0x8000;
 Enable();DisownBlitter();LoadView(oldview);WaitTOF();WaitTOF();Permit();
}
static void save(const char *name,const void *data,unsigned n){BPTR f=Open((CONST_STRPTR)name,MODE_NEWFILE);if(f){Write(f,(APTR)data,n);Close(f);}}
int main(void){
 SysBase=*(struct ExecBase**)4;
 DOSBase=(struct DosLibrary*)OpenLibrary((CONST_STRPTR)"dos.library",37);
 GfxBase=(struct GfxBase*)OpenLibrary((CONST_STRPTR)"graphics.library",39);
 if(!DOSBase||!GfxBase)return 20;
 SetChipRev(0xffffffff);
 arena=AllocMem(arena_size,MEMF_CHIP|MEMF_CLEAR);
 if(!arena){Write(Output(),(APTR)"Not enough Chip RAM.\n",21);return 20;}
 mapplanes=arena;screens[0]=arena+5*32*480;screens[1]=screens[0]+5*40*720;
 coppers[0]=(u16*)(screens[1]+5*40*720);coppers[1]=coppers[0]+160;waves=(u8*)(coppers[1]+160);
 hw_data[0]=screens[1]+5*40*720+2048;hw_data[1]=hw_data[0]+8*1024;
 if(AUTOTEST)save("DH1:build-id.txt","NATIVE-68020-ASM--7\n",20);
 cpu_run(0);if(AUTOTEST){save("DH1:startup-cpu.bin",&cpu,sizeof(cpu));save("DH1:startup-ram.bin",ram,sizeof(ram));}
 render_map();takeover();
 u32 last=fields,acc=0,pending=0,max_pending=0;unsigned front=0;
 for(;;){
  u8 held=read_controls();if(keys[0x45] || test_control==0xdead || cpu.error)break;
  u32 current=fields,elapsed=current-last;
  if(!elapsed){wait_field();continue;}
  last=current;if(elapsed>max_elapsed)max_elapsed=elapsed;acc+=elapsed*120390;while(acc>=100000){pending++;acc-=100000;}if(pending>max_pending)max_pending=pending;
  // Every due source tick is retained, including fields spent rendering.
  u32 before=fields,profile_start=stamp();
  unsigned serviced=0;while(pending && serviced<6){
   if(AUTOTEST || test_control==1){held=source_ticks>=180 && source_ticks<185?8:0;if(source_ticks>190){held|=16;if(source_ticks%180<4)held|=1;if(source_ticks%500<25)held|=64;else if(source_ticks%500>470)held|=128;}}
   if(source_ticks<sizeof(inputlog))inputlog[source_ticks]=held;
   pad=held;cpu_run((ctrl&128)!=0);audio_tick();source_ticks++;pending--;serviced++;
   if(cpu.error)break;
  }
  u32 cost=stamp()-profile_start;if(cost<100000)cpu_lines+=cost;
  if(fields-before>max_cpu_fields)max_cpu_fields=fields-before;
  before=fields;profile_start=stamp();render_map();unsigned back=front^1;render_background(back);render_sprites(back);render_copper(back);audio_publish();
  cost=stamp()-profile_start;if(cost<100000)render_lines+=cost;
  if(fields-before>max_render_fields)max_render_fields=fields-before;
  profile_start=stamp();wait_publish();cost=stamp()-profile_start;if(cost<100000)idle_lines+=cost;R32(0x80)=(u32)coppers[back];R16(0x88)=0;front=back;publications++;
  if(AUTOTEST && source_ticks>=1800)break;
 }
 restore();
 if(AUTOTEST || test_control){render_export(front);
 save("DH1:native-input.bin",inputlog,source_ticks<sizeof(inputlog)?source_ticks:sizeof(inputlog));
 save("DH1:native-cpu.bin",&cpu,sizeof(cpu));save("DH1:native-ram.bin",ram,sizeof(ram));save("DH1:native-nt.bin",nt,sizeof(nt));save("DH1:native-oam.bin",oam,sizeof(oam));save("DH1:native-pal.bin",pal,sizeof(pal));save("DH1:native-screen.bin",mapplanes,5*40*256);
 u32 hs[]={hw_frames,hw_tiles,sw_tiles,hw_groups,hw_overlap,hw_capacity,hw_empty};save("DH1:hardware-stats.bin",hs,sizeof(hs));
 save("DH1:hardware-lists.bin",hw_data[front],8192);
 u32 stats[]={fields,source_ticks,publications,max_elapsed,max_cpu_fields,max_render_fields,ctrl,mask,bank,sx,sy,cpu.error,pending,max_pending,cpu_lines,render_lines,idle_lines,full_redraws,total_dirty_tiles};save("DH1:stats.bin",stats,sizeof(stats));}

 FreeMem(arena,arena_size);CloseLibrary((struct Library*)GfxBase);CloseLibrary((struct Library*)DOSBase);return cpu.error?20:0;
}
