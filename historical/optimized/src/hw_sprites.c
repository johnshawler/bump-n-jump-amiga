#include "engine.h"

/* The four NES sprite palettes match the four Amiga sprite channel pairs.
 * Coalesce adjacent source tiles, then reuse each channel down the display.
 * Overlapping objects stay in the original renderer: that preserves NES OAM
 * priority even when hardware and software sprites share a picture. */
#define CHANNEL_BYTES 1024
/* Bitplane pixel zero with this display's DDF timing, checked against the
 * completed AGA raster. DIWSTRT's horizontal value is one pixel farther right. */
#define SPRITE_X_ORIGIN 0xa0
u8 *hw_data[2];
u8 hw_selected[64];
u32 hw_frames,hw_tiles,sw_tiles,hw_groups,hw_overlap,hw_capacity,hw_empty;
extern const u16 sprite_atlas[];
extern const u8 sprite_nonempty[];
struct Group {u16 x,y,h;u8 width,palette,head,tail,blocked;};
static struct Group groups[64];
static u8 next_tile[64],order[64];

static void append(struct Group *g,unsigned i){
 next_tile[g->tail]=i;g->tail=i;next_tile[i]=255;
}
void hw_prepare(unsigned buffer){
 unsigned count=0;
 u16 used[8]={0},end[8]={0};
 memset(hw_selected,0,sizeof(hw_selected));
 for(unsigned c=0;c<8;c++)*(u32*)(hw_data[buffer]+c*CHANNEL_BYTES)=0;
 if(!(mask&16))return;
 if(ctrl&40){for(unsigned i=0;i<64;i++)if(oam[i*4]<239)sw_tiles++;return;}
 for(unsigned i=0;i<64;i++){
  if(hw_selected[i])continue;
  const u8 *s=oam+i*4;unsigned y=s[0]+1,x=s[3],at=s[2];
  if(y>=240)continue;
  if(!sprite_nonempty[bank*256+s[1]]){hw_selected[i]=2;hw_empty++;continue;}
  unsigned j=i+1,left=i,right=255,width=8;
  if(j<64 && !hw_selected[j]){
   const u8 *t=oam+j*4;
   if(t[0]==s[0] && ((t[2]^at)&35)==0 && sprite_nonempty[bank*256+t[1]]){
    if(t[3]==x+8){right=j;width=16;}
    else if(x==t[3]+8){left=j;right=i;x=t[3];width=16;}
   }
  }
  unsigned g;
  for(g=0;g<count;g++)if(groups[g].x==x && groups[g].y+groups[g].h==y && groups[g].width==width && groups[g].palette==(at&3) && groups[g].blocked==((at&32)?1:0))break;
  if(g==count){
   struct Group *p=groups+count++;p->x=x;p->y=y;p->h=0;p->width=width;p->palette=at&3;p->head=left;p->tail=left;p->blocked=(at&32)?1:0;next_tile[left]=255;
  }else append(groups+g,left);
  if(right!=255)append(groups+g,right);
  groups[g].h+=8;hw_selected[left]=3;if(right!=255)hw_selected[right]=3;
 }
 /* Conservative rectangle exclusion also covers behind-background objects.
  * No selected hardware object can obscure a source sprite drawn in software. */
 for(unsigned i=0;i<count;i++)for(unsigned j=i+1;j<count;j++){
  struct Group *a=groups+i,*b=groups+j;
  if(a->x<b->x+b->width && b->x<a->x+a->width && a->y<b->y+b->h && b->y<a->y+a->h){a->blocked=2;b->blocked=2;}
 }
 for(unsigned i=0;i<count;i++){
  unsigned j=i;while(j && groups[order[j-1]].y>groups[i].y){order[j]=order[j-1];j--;}order[j]=i;
 }
 unsigned frame_groups=0;
 for(unsigned k=0;k<count;k++){
  struct Group *g=groups+order[k];unsigned c=g->palette*2,h=g->h;
  if(g->y+h>240)h=240-g->y;
  if(g->blocked){hw_overlap++;continue;}
  if(end[c]>g->y)c++;
  if(end[c]>g->y || used[c]+4+h*4+4>CHANNEL_BYTES){hw_capacity++;continue;}
  u16 *out=(u16*)(hw_data[buffer]+c*CHANNEL_BYTES+used[c]);
  unsigned x=g->x+SPRITE_X_ORIGIN,y=g->y+0x34,stop=y+h;
  out[0]=(y<<8)|(x>>1);out[1]=(stop<<8)|((y&256)>>6)|((stop&256)>>7)|(x&1);
  u16 clip=0xffff;if(g->x>240)clip<<=g->x-240;
  if(!(mask&4) && g->x<8)clip&=0xffff>>(8-g->x);
  for(unsigned i=g->head;i!=255;i=next_tile[i]){
   const u8 *s=oam+i*4;unsigned yy=s[0]+1,at=s[2],rows=240-yy;if(rows>8)rows=8;
   const u16 *src=sprite_atlas+(bank*256+s[1])*384+((at&64)?192:0)+((at&128)?21:0);
   u16 *dst=out+2+(yy-g->y)*2;long step=(at&128)?-3:3;
   if(s[3]==g->x){for(unsigned r=0;r<rows;r++){dst[0]=src[0]&clip;dst[1]=src[1]&clip;dst+=2;src+=step;}}
   else{for(unsigned r=0;r<rows;r++){dst[0]|=(src[0]>>8)&clip;dst[1]|=(src[1]>>8)&clip;dst+=2;src+=step;}}
   hw_selected[i]=1;hw_tiles++;
  }
  used[c]+=4+h*4;end[c]=g->y+h+1;frame_groups++;hw_groups++;
 }
 for(unsigned c=0;c<8;c++)*(u32*)(hw_data[buffer]+c*CHANNEL_BYTES+used[c])=0;
 for(unsigned i=0;i<64;i++)if(hw_selected[i]==3){hw_selected[i]=0;sw_tiles++;}
 if(frame_groups)hw_frames++;
}

/* Debug export decodes the actual DMA lists, including their channel palettes.
 * Release rendering never copies these objects into the playfield bitmap. */
void hw_export(unsigned buffer,u8 *planes){
 for(unsigned c=0;c<8;c++){
  const u16 *src=(const u16*)(hw_data[buffer]+c*CHANNEL_BYTES),*limit=src+CHANNEL_BYTES/2;
  while(src+2<limit && (src[0]||src[1])){
   unsigned pos=*src++,ctl=*src++;
   int x=(pos&255)*2+(ctl&1)-SPRITE_X_ORIGIN,y=(pos>>8)+((ctl&4)?256:0)-0x34;
   int stop=(ctl>>8)+((ctl&2)?256:0)-0x34;
   for(;y<stop && src+2<=limit;y++){
    unsigned a=*src++,b=*src++;
    if(y<0 || y>=240)continue;
    for(int j=0;j<16;j++){
     int xx=x+j;if(xx<0 || xx>=256)continue;
     unsigned v=((a>>(15-j))&1)|(((b>>(15-j))&1)<<1);if(!v)continue;
     v+=16+(c>>1)*4;unsigned off=(y+8)*40+4+(xx>>3),bit=128>>(xx&7);
     for(unsigned p=0;p<5;p++){u8 *d=planes+off+p*10240;*d=(*d&~bit)|((v&(1<<p))?bit:0);}
    }
   }
  }
 }
}
