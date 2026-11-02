#include "engine.h"
#define R16(o) (*(volatile u16*)(0xdff000+(o)))
#define R32(o) (*(volatile u32*)(0xdff000+(o)))
#define MAP_PLANE (32*480)
#define SCREEN_PLANE (40*720)
u8 *mapplanes,*screens[2];
u16 *coppers[2];
static const u16 colors[64]={
0x666,0x028,0x11a,0x30a,0x507,0x604,0x600,0x510,0x330,0x040,0x050,0x040,0x044,0,0,0,
0xaaa,0x15d,0x44f,0x72f,0xa1c,0xb17,0xb32,0x840,0x460,0x170,0x080,0x174,0x068,0,0,0,
0xfff,0x6bf,0x99f,0xc7f,0xf6f,0xf6c,0xf87,0xea2,0xbc0,0x8d0,0x5e3,0x4d8,0x4cd,0x444,0,0,
0xfff,0xcdf,0xddf,0xecf,0xfcf,0xfce,0xfcc,0xfda,0xee9,0xcf9,0xbfa,0xbfc,0xbee,0xbbb,0,0};
u32 full_redraws,total_dirty_tiles;
static u16 pending[2][2048],pending_count[2];
static u8 queued[2][2048],full[2]={1,1},last_bank[2]={255,255},last_table[2]={255,255};
static unsigned view_y(void){unsigned y=((ctrl&2)?240:0)+sy;return y>=480?y-480:y;}
static void enqueue(unsigned b,unsigned q){if(!queued[b][q]){queued[b][q]=1;pending[b][pending_count[b]++]=q;}}
extern const u8 bg_atlas[];
extern void draw_bg_tile(u8*,const u8*,u32,u32);
static void tile_at(unsigned buffer,unsigned q,unsigned physical_y){
 unsigned x=q&31,y=(q&1023)>>5,base=q&1024;
 unsigned at=nt[base+960+(y>>2)*8+(x>>2)];at=(at>>(((y&2)<<1)|(x&2)))&3;
 const u8 *src=chr+((unsigned)bank<<13)+((ctrl&16)?4096:0)+(nt[q]<<4);
 unsigned off=physical_y*40+x+4;
 u8 *p0=screens[buffer]+off,*p1=p0+SCREEN_PLANE,*p2=p1+SCREEN_PLANE,*p3=p2+SCREEN_PLANE,*p4=p3+SCREEN_PLANE;

 for(unsigned row=0;row<8;row++){
  u8 a=src[row],b=src[row+8],m=a|b;
  *p0=a;*p1=b;*p2=(at&1)?m:0;*p3=(at&2)?m:0;*p4=0;
  p0+=40;p1+=40;p2+=40;p3+=40;p4+=40;
 }
}
static void tile_draw(unsigned buffer,unsigned q){
 unsigned y=((q&1023)>>5)*8;
 if(q&1024)tile_at(buffer,q,y+240);
 else{tile_at(buffer,q,y);tile_at(buffer,q,y+480);}
}
void render_map(void){
 if(all_dirty){full[0]=full[1]=1;all_dirty=0;}
 for(unsigned i=0;i<dirtycount;i++){
  unsigned q=dirty[i];enqueue(0,q);enqueue(1,q);marked[q]=0;
 }
 dirtycount=0;
}
void render_background(unsigned b){
 if(last_bank[b]!=bank || last_table[b]!=(ctrl&16)){full[b]=1;last_bank[b]=bank;last_table[b]=ctrl&16;}
 if(full[b]){full_redraws++;for(unsigned q=0;q<960;q++){tile_draw(b,q);tile_draw(b,q+1024);}full[b]=0;}
 else {total_dirty_tiles+=pending_count[b];for(unsigned i=0;i<pending_count[b];i++)tile_draw(b,pending[b][i]);}
 for(unsigned i=0;i<pending_count[b];i++)queued[b][pending[b][i]]=0;
 pending_count[b]=0;
}
static void restore_under_sprite(unsigned b,unsigned x,unsigned y,unsigned h){
 unsigned right=(x+7)>>3;if(right>31)right=31;
 unsigned bottom=(y+h-1)>>3;
 for(unsigned ty=y>>3;ty<=bottom;ty++){
  unsigned yy=ty*8;if(yy>=480)yy-=480;unsigned base=0;if(yy>=240){base=1024;yy-=240;}unsigned row=yy>>3;
  for(unsigned tx=x>>3;tx<=right;tx++)enqueue(b,base+row*32+tx);
 }
}
void render_export(unsigned b){
 memset(mapplanes,0,5*40*256);unsigned yy=view_y();
 for(unsigned p=0;p<5;p++)for(unsigned y=0;y<240;y++)memcpy(mapplanes+p*40*256+(y+8)*40+4,screens[b]+p*SCREEN_PLANE+(yy+y)*40+4,32);
}
extern const u16 sprite_atlas[];
extern void sprite_rows(u8*,const u16*,u8*,u32,long,u32,u32,u32,u32);
static u8 coverage[32*240+2] __attribute__((aligned(4)));
void render_sprites(unsigned buffer){
 if(!(mask&16))return;
 memset(coverage,0,sizeof(coverage));
 unsigned origin=view_y();u8 *dst=screens[buffer]+origin*40+4;
 const u8 *cb=chr+((unsigned)bank<<13);
 for(int i=0;i<64;i++){
  const u8 *s=oam+i*4;unsigned yy=s[0]+1,t=s[1],at=s[2],x=s[3],h=(ctrl&32)?16:8;
  if(yy>=240)continue;
  restore_under_sprite(buffer,x,origin+yy,h);
  unsigned sh=x&7,off=yy*40+(x>>3);
  u16 *d0=(u16*)(dst+off),*d1=(u16*)((u8*)d0+SCREEN_PLANE),*d2=(u16*)((u8*)d1+SCREEN_PLANE),*d3=(u16*)((u8*)d2+SCREEN_PLANE),*d4=(u16*)((u8*)d3+SCREEN_PLANE);
  u16 *cover=(u16*)(coverage+yy*32+(x>>3));
  unsigned clip=x>248?0xff00:0xffff;
  if(!(mask&4) && x<8)clip&=0x00ff;
  if(h==8 && !(ctrl&8)){
   const u16 *atp=sprite_atlas+((bank*256+t)*384)+((at&64)?192:0)+sh*24+((at&128)?21:0);
   unsigned rows=240-yy;if(rows>8)rows=8;
   sprite_rows((u8*)d0,atp,(u8*)cover,rows,(at&128)?-6:6,(at&1)?65535:0,(at&2)?65535:0,at&32,clip);
   continue;
  }
  for(unsigned j=0;j<h && yy+j<240;j++){
   unsigned syy=(at&128)?h-1-j:j;
   unsigned a=(h==16)?((t&1)*4096+(t&254)*16+(syy&8)*2+(syy&7)):(((ctrl&8)?4096:0)+t*16+syy);
   unsigned b0=cb[a],b1=cb[a+8];
   if(at&64){b0=((b0&0x55)<<1)|((b0>>1)&0x55);b0=((b0&0x33)<<2)|((b0>>2)&0x33);b0=(b0<<4)|(b0>>4);b0&=255;
    b1=((b1&0x55)<<1)|((b1>>1)&0x55);b1=((b1&0x33)<<2)|((b1>>2)&0x33);b1=(b1<<4)|(b1>>4);b1&=255;}
   u16 p0=(b0<<8)>>sh,p1=(b1<<8)>>sh,m=(p0|p1)&clip;
   u16 opaque=m;m&=~*cover;*cover|=opaque;
   if(at&32)m&=~(*d0|*d1);
   if(m){u16 keep=~m;*d0=(*d0&keep)|(p0&m);*d1=(*d1&keep)|(p1&m);*d2=(*d2&keep)|((at&1)?m:0);*d3=(*d3&keep)|((at&2)?m:0);*d4|=m;}
   d0+=20;d1+=20;d2+=20;d3+=20;d4+=20;cover+=16;
  }
 }
}
static void cmove(u16 **c,u16 reg,u16 value){*(*c)++=reg;*(*c)++=value;}
void render_copper(unsigned b){
 u16 *c=coppers[b];
 cmove(&c,0x100,(mask&24)?0x5200:0x0200);cmove(&c,0x102,0);cmove(&c,0x104,0);cmove(&c,0x106,0);cmove(&c,0x108,8);cmove(&c,0x10a,8);cmove(&c,0x1fc,0);
 cmove(&c,0x08e,0x34a1);cmove(&c,0x090,0x24a1);cmove(&c,0x092,0x0048);cmove(&c,0x094,0x00c0);
 for(unsigned p=0;p<5;p++){u32 a=(u32)(screens[b]+p*SCREEN_PLANE+view_y()*40+4);cmove(&c,0xe0+p*4,a>>16);cmove(&c,0xe2+p*4,a);}
 for(unsigned p=0;p<32;p++){unsigned n=(p&3)?p:0;cmove(&c,0x180+p*2,colors[pal[n]&63]);}
 *c++=0xffff;*c++=0xfffe;
}
