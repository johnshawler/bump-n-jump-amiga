#ifndef ENGINE_H
#define ENGINE_H
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
extern const u8 prg[32768],chr[32768];
extern u8 ram[2048],nt[2048],pal[32],oam[256],apu[32];
extern u8 ctrl,mask,bank,sx,sy,pad,strobe,joy,toggle,readbuf,oamaddr;
extern u16 ppuaddr,pputmp;
extern u16 dirty[2048],dirtycount;
extern u8 marked[2048];
extern int all_dirty;
extern u8 frame_nt[2048],frame_oam[256],frame_pal[32];
extern u8 frame_ctrl,frame_mask,frame_bank,frame_sx,frame_sy;
void render_snapshot(void);
void render_yield(void);
int render_background_step(unsigned buffer,unsigned budget);
extern u8 *hw_data[2],hw_selected[64];
extern u32 hw_frames,hw_tiles,sw_tiles,hw_groups,hw_overlap,hw_capacity,hw_empty;
void hw_prepare(unsigned buffer);
void hw_export(unsigned buffer,u8 *planes);
struct CPU {unsigned a,x,y,s,p,pc,error,dispatches;};
extern struct CPU cpu;
u8 io_read(unsigned addr);
void io_write(unsigned addr,unsigned value);
static inline __attribute__((always_inline)) u8 rd(unsigned addr){
 if(addr<0x2000)return ram[addr&2047];
 if(addr>=0x8000)return prg[addr-0x8000];
 return io_read(addr);
}
static inline __attribute__((always_inline)) void wr(unsigned addr,unsigned value){
 if(addr<0x2000){ram[addr&2047]=value;return;}
 io_write(addr,value);
}
void cpu_run(int interrupt);
void mark_tile(unsigned index);
void apu_write(unsigned addr,u8 value);
extern u32 audio_write_hash,audio_writes,audio_publications;
extern u16 audio_period[4],audio_volume[4];
void *memcpy(void *,const void *,unsigned long);
void *memset(void *,int,unsigned long);
#ifdef RENDER_SNAPSHOT
#define nt frame_nt
#define oam frame_oam
#define pal frame_pal
#define ctrl frame_ctrl
#define mask frame_mask
#define bank frame_bank
#define sx frame_sx
#define sy frame_sy
#endif
#endif
