#include "engine.h"
u8 ram[2048],nt[2048],pal[32],oam[256],apu[32];
u8 ctrl,mask,bank,sx,sy,pad,strobe,joy,toggle,readbuf,oamaddr;
u16 ppuaddr,pputmp;
u16 dirty[2048],dirtycount;
u8 marked[2048];int all_dirty=1;
struct CPU cpu={0,0,0,255,0x30,0x8000,0,0};
void mark_tile(unsigned i){if(!marked[i]){marked[i]=1;dirty[dirtycount++]=i;}}
static u8 ppuread(unsigned a){
 a&=0x3fff;
 if(a<0x2000)return chr[(bank<<13)+a];
 if(a<0x3f00)return nt[((a&0x800)>>1)|(a&1023)];
 a&=31;if((a&19)==16)a&=15;return pal[a];
}
u8 io_read(unsigned a){
 if(a<0x4000){
  switch(a&7){
   case 2:toggle=0;return 0xc0;
   case 4:return oam[oamaddr];
   case 7:{unsigned old=ppuaddr;u8 v=ppuread(old),b=readbuf;readbuf=v;ppuaddr=(old+((ctrl&4)?32:1))&0x3fff;return old>=0x3f00?v:b;}
  }
 }
 if(a==0x4016){u8 v=(joy&1)|0x40;if(!strobe)joy=(joy>>1)|128;return v;}
 return 0;
}
void io_write(unsigned a,unsigned v){
 if(a>=0x8000){bank=v&3;return;}
 if(a<0x4000){
  switch(a&7){
   case 0:ctrl=v;pputmp=(pputmp&0x73ff)|((v&3)<<10);break;
   case 1:mask=v;break;
   case 3:oamaddr=v;break;
   case 4:oam[oamaddr++]=v;break;
   case 5:if(!toggle){sx=v;pputmp=(pputmp&0x7fe0)|(v>>3);}else{sy=v;pputmp=(pputmp&0xc1f)|((v&7)<<12)|((v&248)<<2);}toggle^=1;break;
   case 6:if(!toggle)pputmp=(pputmp&255)|((v&63)<<8);else{pputmp=(pputmp&0x7f00)|v;ppuaddr=pputmp;}toggle^=1;break;
   case 7:{unsigned q=ppuaddr&0x3fff;
    if(q>=0x2000 && q<0x3f00){q=((q&0x800)>>1)|(q&1023);if(nt[q]!=v){nt[q]=v;if((q&1023)<960)mark_tile(q);else{unsigned x=(q&7)*4,y=((q&63)>>3)*4,b=q&1024;for(unsigned j=0;j<4 && y+j<30;j++)for(unsigned k=0;k<4;k++)mark_tile(b+(y+j)*32+x+k);}}}
    else if(q>=0x3f00){q&=31;if((q&19)==16)q&=15;pal[q]=v&63;}
    ppuaddr=(ppuaddr+((ctrl&4)?32:1))&0x3fff;break;}
  }return;
 }
 if(a==0x4014){memcpy(oam,ram+((v<<8)&2047),256);return;}
 if(a==0x4016){strobe=v&1;if(strobe)joy=pad;return;}
 if(a>=0x4000 && a<0x4020){apu[a-0x4000]=v;apu_write(a,v);}
}
