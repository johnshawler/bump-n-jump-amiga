#include "menu.h"
#include <exec/execbase.h>
#include <graphics/gfxbase.h>
#include <proto/exec.h>
#include <proto/graphics.h>
#include <proto/dos.h>
#include <dos/dosextens.h>
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
volatile u32 publish_copper;
extern u32 full_redraws,total_dirty_tiles;
static u32 cpu_lines,render_lines,idle_lines;
static unsigned beam_line(void){u16 hi,lo,again;do{hi=R16(4)&1;lo=R16(6)>>8;again=R16(4)&1;}while(hi!=again);return (hi<<8)|lo;}
static u32 stamp(void){u32 a,b;unsigned line;do{a=fields;line=beam_line();b=fields;}while(a!=b);return a*312+line;}
static void wait_publish(void){
 /* Sprite DMA fetches the initial control words before the visible area. */
 for(;;){unsigned line=beam_line();if(line<20 || line>=296)return;}
}
static u8 inputlog[16384];
struct TickAudit {u32 start,end,apu_hash;u16 writes;u8 mode,scene;u32 cpu_hash;};
static struct TickAudit tick_audit[4096];
static u32 clock_last,clock_phase,pending,max_pending,clock_origin;
static void clock_update(void){
 u32 now=stamp(),elapsed=now-clock_last;clock_last=now;
 clock_phase+=elapsed*120390u;
 while(clock_phase>=31200000u){pending++;clock_phase-=31200000u;}
 if(pending>max_pending)max_pending=pending;
 if((elapsed+311)/312>max_elapsed)max_elapsed=(elapsed+311)/312;
}

volatile u32 menu_active,menu_kind,menu_choice,menu_cursor;
static u8 keys[128];
static u8 *arena;
static u32 arena_size=5*32*480+2*5*40*720+2048+2*8*1024;
static struct View *oldview;
static u32 oldirq,*irqvec;
static u16 olddma,oldint,oldadk;
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
 if(left||keys[0x4f]||(menu_kind!=3 && keys[0x20]))v|=64;
 if(right||keys[0x4e]||(menu_kind!=3 && keys[0x22]))v|=128;
 if(up||keys[0x4c]||(menu_kind!=3 && keys[0x11]))v|=16;
 if(down||keys[0x4d]||(menu_kind!=3 && keys[0x21]))v|=32;
 int fire=!(CIAA(0)&128)||keys[0x40]||keys[0x63];
 if(fire){if(ram[0x14]==2||ram[0x14]==3)v|=8;else v|=1;}
 if(keys[0x44])v|=8;
 if(keys[0x60]||keys[0x61])v|=2;
 if(keys[0x42])v|=4;
 return v;
}
static int game_clock_active;
static unsigned front,back=1,render_stage,menu_request;
static int run_active,score_slot=-1,continuing;
static u8 last_controls;
static u32 stage_starts[64],stage_start_count;
static void open_menu(unsigned request);
static int load_score_file(const char *name){u8 d[97];BPTR f=Open((CONST_STRPTR)name,MODE_OLDFILE);if(!f)return 0;LONG n=Read(f,d,97);Close(f);return n==96 && scores_unpack(d);}
static int save_scores(void){
 u8 d[96],check[97];u32 generation=scores_generation+1;if(!generation)generation=1;
 unsigned slot=score_slot==0?1:0;const char *name=slot?"DH0:HighScores.B":"DH0:HighScores.A";
 scores_pack(d,generation);BPTR f=Open((CONST_STRPTR)name,MODE_NEWFILE);if(!f)return 0;
 LONG n=Write(f,d,96);int closed=Close(f);if(n!=96 || !closed)return 0;
 f=Open((CONST_STRPTR)name,MODE_OLDFILE);if(!f)return 0;n=Read(f,check,97);Close(f);if(n!=96)return 0;
 for(unsigned i=0;i<96;i++)if(d[i]!=check[i])return 0;
 /* Finish the filesystem's delayed block writes before OS tasks pause. */
 struct MsgPort *port=DeviceProc((CONST_STRPTR)"DH0:");
 if(!port || !DoPkt(port,ACTION_FLUSH,0,0,0,0,0))return 0;
 scores_generation=generation;score_slot=slot;return 1;
}

static void service_tick(void){
   u8 held=read_controls();if(keys[0x45])return;
   if(AUTOTEST || test_control==1 || test_control==3){held=source_ticks>=180 && source_ticks<185?8:0;if(source_ticks>190){held|=16;if(source_ticks%180<4)held|=1;if(source_ticks%500<25)held|=64;else if(source_ticks%500>470)held|=128;}}
   if(test_control==3 && source_ticks>1000 && ram[0x14]==2 && source_ticks%100<3)held|=8;
   if(source_ticks<sizeof(inputlog))inputlog[source_ticks]=held;
   u32 before=stamp(),writes=audio_writes;
   unsigned previous_scene=ram[0x14];pad=held;cpu_run((ctrl&128)!=0);audio_tick();audio_publish();
   u32 after=stamp(),cost=after-before;cpu_lines+=cost;
   if((cost+311)/312>max_cpu_fields)max_cpu_fields=(cost+311)/312;
   if(source_ticks<4096){struct TickAudit *a=tick_audit+source_ticks;a->start=before-clock_origin;a->end=after-clock_origin;a->apu_hash=audio_write_hash;a->writes=audio_writes-writes;a->mode=ram[0x85]&15;a->scene=ram[0x14];a->cpu_hash=(((((cpu.a*33+cpu.x)*33+cpu.y)*33+cpu.s)*33+cpu.p)*33+cpu.pc);}
   source_ticks++;pending--;
   if(ram[0x14]==4 && previous_scene!=4 && !(ram[0x3d]&128)){if(continuing){continuing=0;run_active=1;}else menu_request=1;}
   if(run_active && ((ram[0x14]==20 && ram[0x15]>=90) || (previous_scene==20 && ram[0x14]!=20) || (ram[0x14]==21 && previous_scene!=21))){run_active=0;if(!(AUTOTEST || test_control==1 || test_control==3))menu_request=scores_rank(game_score())>=0?2:(ram[0x14]==21?0:4);}
   if(ram[0x14]==2 && (held&4) && !(last_controls&4))menu_request=3;
   last_controls=held;
}
void render_yield(void){
 if(!game_clock_active)return;
 clock_update();
 while(pending && !menu_request && !keys[0x45] && test_control!=0xdead && !cpu.error){service_tick();clock_update();}
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
/* Source logic pauses while a native menu is open. No game ticks or sound
 * events are discarded; the wall clock resumes at the point it stopped. */
static void menu_mute(void){for(unsigned c=0;c<4;c++)R16(0xa8+c*16)=0;}
static void menu_beep(unsigned confirm){R16(0xa6)=confirm?280:420;R16(0xa8)=24;}
static void menu_show(unsigned kind,unsigned choice,unsigned cursor,const char *initials,u32 score,int status){
 back=front^1;menu_draw(back,kind,choice,cursor,initials,score,status);
 publish_copper=(u32)coppers[back];while(publish_copper && !keys[0x45])keyboard_poll();front=back;
}
static int menu_save_scores(void){restore();int ok=save_scores();takeover();
 /* The OS may have consumed key releases while the disk was saving. */
 memset(keys,0,sizeof(keys));menu_mute();return ok;}
static void open_menu(unsigned request){
 menu_request=0;
 unsigned choice=ram[0x3c]&15;
 if(request==1 && (AUTOTEST || test_control==1 || test_control==3)){ram[0x3c]=0;run_active=1;if(stage_start_count<32){stage_starts[stage_start_count*2]=source_ticks;stage_starts[stage_start_count*2+1]=0;stage_start_count++;}return;}
 u32 paused=stamp();game_clock_active=0;
 Disable();if(render_stage==5 && !publish_copper)front=back;publish_copper=0;Enable();
 menu_mute();unsigned kind=request==1?1:request==2?3:request==4?4:2,cursor=0;char initials[3]={'A','A','A'};
 unsigned offer_continue=ram[0x14]!=21;
 u32 score=game_score();unsigned reached=ram[0x56]<16?ram[0x56]+1:16;
 int status=0;unsigned continue_choice=0;u8 previous=255,oldkeys[128];memcpy(oldkeys,keys,128);
 unsigned repeat=0,beep_end=0;u32 last_field=fields;
 menu_kind=kind;menu_choice=choice;menu_cursor=cursor;
 menu_show(kind,kind==4?continue_choice:choice,cursor,initials,score,status);menu_active=1;
 for(;;){
  keyboard_poll();if(keys[0x45] || test_control==0xdead)break;
  if(fields==last_field)continue;
  last_field=fields;
  if(beep_end && (int)(fields-beep_end)>=0){menu_mute();beep_end=0;}
  u8 held=read_controls(),edge=held&~previous;
  if(previous==255){if(held&9)continue;previous=held;edge=0;}
  if(held&240){if((held&240)==(previous&240)){if(++repeat>=20 && (repeat-20)%5==0)edge|=held&240;}else repeat=0;}else repeat=0;
  int redraw=0,confirm=0;
  if(kind==1){
   if(edge&240){choice=(choice+((edge&(64|16))?15:1))&15;redraw=1;}
   if(edge&4){kind=2;redraw=1;}
   if(edge&9){ram[0x3c]=choice;run_active=1;if(stage_start_count<32){stage_starts[stage_start_count*2]=source_ticks;stage_starts[stage_start_count*2+1]=choice;stage_start_count++;}break;}
  }else if(kind==2){
   if(edge&(9|4)){
    if(status<0){status=menu_save_scores()?1:-1;redraw=1;}
    else if(request==1){kind=1;redraw=1;}else if(request==2 && offer_continue){kind=4;redraw=1;}else break;
   }
  }else if(kind==4){
   if(edge&240){continue_choice^=1;redraw=1;}
   if(edge&9){
    if(!continue_choice){
     /* The cartridge's title/continue path enters scene 3, which resets
      * score and lives before its ordinary stage setup. */
     ram[0x3c]=reached-1;ram[0x3d]=0;ram[0x14]=3;ram[0x15]=ram[0x16]=0;
     ram[4]=0xe1;ram[5]=0x84;continuing=1;
    }
    break;
   }
  }else{
   if(edge&(16|32)){initials[cursor]='A'+(initials[cursor]-'A'+((edge&16)?1:25))%26;redraw=1;}
   if(edge&64){cursor=(cursor+2)%3;redraw=1;}if(edge&128){cursor=(cursor+1)%3;redraw=1;}
   const char *letters="QWERTYUIOPASDFGHJKLZXCVBNM";
   static const u8 codes[]={0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x31,0x32,0x33,0x34,0x35,0x36,0x37};
   for(unsigned i=0;i<26;i++)if(keys[codes[i]]&&!oldkeys[codes[i]]){initials[cursor]=letters[i];if(cursor<2)cursor++;redraw=1;}
   if(keys[0x41]&&!oldkeys[0x41]){if(cursor)cursor--;redraw=1;}
   if(edge&9){if(keys[0x44] || cursor==2)confirm=1;else{cursor++;redraw=1;}}
   if(confirm){scores_insert(score,reached,initials);status=menu_save_scores()?1:-1;kind=2;redraw=1;}
  }
  previous=held;memcpy(oldkeys,keys,128);
  menu_kind=kind;menu_choice=kind==4?continue_choice:choice;menu_cursor=cursor;
  if(redraw){menu_beep(confirm);beep_end=fields+4;menu_show(kind,kind==4?continue_choice:choice,cursor,initials,score,status);}
 }
 /* Do not let the accepting button become pause/jump in the resumed game. */
 while(!keys[0x45] && test_control!=0xdead && (read_controls()&9)){}
 menu_active=0;menu_kind=0;menu_mute();
 render_invalidate();all_dirty=1;render_stage=0;
 /* The menu may have replaced display palettes and sprite lists. Build one
  * complete game snapshot before restarting its clock. */
 render_map();back=front^1;render_background(back);render_sprites(back);render_copper(back);
 publish_copper=(u32)coppers[back];while(publish_copper && !keys[0x45])keyboard_poll();front=back;
 for(unsigned c=0;c<4;c++){R16(0xa6+c*16)=audio_period[c];R16(0xa8+c*16)=audio_volume[c];}
 u32 now=stamp();clock_origin+=now-paused;clock_last=now;game_clock_active=1;
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
 scores_reset();if(load_score_file("DH0:HighScores.A"))score_slot=0;if(load_score_file("DH0:HighScores.B"))score_slot=1;
 render_map();takeover();
 clock_origin=clock_last=stamp();game_clock_active=1;
 u32 frame_cost=0;
 for(;;){
  clock_update();
  if(keys[0x45] || test_control==0xdead || cpu.error)break;
  if(menu_request){open_menu(menu_request);continue;}
  if(pending){
   service_tick();
   if(AUTOTEST && source_ticks>=1800)break;
   continue;
  }
  u32 before=stamp(),cpu_before=cpu_lines;
  if(render_stage==0){render_map();back=front^1;frame_cost=0;render_stage=1;}
  else if(render_stage==1){if(render_background_step(back,8))render_stage=2;}
  else if(render_stage==2){render_sprites(back);render_stage=3;}
  else if(render_stage==3){render_copper(back);render_stage=4;}
  else if(render_stage==4){publish_copper=(u32)coppers[back];render_stage=5;}
  else if(!publish_copper){
   front=back;render_stage=0;
   if((frame_cost+311)/312>max_render_fields)max_render_fields=(frame_cost+311)/312;
  }else{keyboard_poll();idle_lines+=stamp()-before;continue;}
  u32 cost=stamp()-before-(cpu_lines-cpu_before);frame_cost+=cost;render_lines+=cost;
 }
 game_clock_active=0;
 u32 run_lines=stamp()-clock_origin,run_fields=(run_lines+156)/312;
 /* Debug receipts render the final source state after the clock has stopped.
  * Normal release exit restores the OS immediately. */
 if(AUTOTEST || test_control){Disable();if(render_stage==5 && !publish_copper)front=back;publish_copper=0;Enable();render_map();back=front^1;render_background(back);render_sprites(back);render_copper(back);wait_publish();R32(0x80)=(u32)coppers[back];R16(0x88)=0;front=back;}

 restore();
 if(AUTOTEST || test_control){render_export(front);
 save("DH1:stage-starts.bin",stage_starts,stage_start_count*8);
 save("DH1:native-input.bin",inputlog,source_ticks<sizeof(inputlog)?source_ticks:sizeof(inputlog));
 save("DH1:native-cpu.bin",&cpu,sizeof(cpu));save("DH1:native-ram.bin",ram,sizeof(ram));save("DH1:native-nt.bin",nt,sizeof(nt));save("DH1:native-oam.bin",oam,sizeof(oam));save("DH1:native-pal.bin",pal,sizeof(pal));save("DH1:native-screen.bin",mapplanes,5*40*256);
 u32 hs[]={hw_frames,hw_tiles,sw_tiles,hw_groups,hw_overlap,hw_capacity,hw_empty};save("DH1:hardware-stats.bin",hs,sizeof(hs));
 save("DH1:hardware-lists.bin",hw_data[front],8192);
 save("DH1:tick-audit.bin",tick_audit,(source_ticks<4096?source_ticks:4096)*sizeof(struct TickAudit));
 save("DH1:native-apu.bin",apu,sizeof(apu));
 u32 aud[]={audio_publications,audio_writes,audio_write_hash};save("DH1:audio-stats.bin",aud,sizeof(aud));
 save("DH1:audio-period.bin",audio_period,sizeof(audio_period));save("DH1:audio-volume.bin",audio_volume,sizeof(audio_volume));
 u32 timeline[]={run_lines,clock_phase,pending,max_pending};save("DH1:clock-stats.bin",timeline,sizeof(timeline));
 u32 stats[]={run_fields,source_ticks,publications,max_elapsed,max_cpu_fields,max_render_fields,ctrl,mask,bank,sx,sy,cpu.error,pending,max_pending,cpu_lines,render_lines,idle_lines,full_redraws,total_dirty_tiles};save("DH1:stats.bin",stats,sizeof(stats));}

 FreeMem(arena,arena_size);CloseLibrary((struct Library*)GfxBase);CloseLibrary((struct Library*)DOSBase);return cpu.error?20:0;
}
