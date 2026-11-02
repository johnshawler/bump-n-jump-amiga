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
void *memcpy(void *,const void *,unsigned long);
void *memset(void *,int,unsigned long);
#endif
