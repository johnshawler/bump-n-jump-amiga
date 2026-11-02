#include "menu.h"
extern u8 *screens[2];
extern void render_copper(unsigned);
#define PLANE (40*720)
static unsigned origin;
static void pixel(unsigned b,unsigned x,unsigned y,unsigned color){
 unsigned a=(origin+y)*40+4+(x>>3);u8 bit=128>>(x&7);
 for(unsigned p=0;p<5;p++){u8 *d=screens[b]+p*PLANE+a;if(color&(1<<p))*d|=bit;else *d&=~bit;}
}
static void rect(unsigned b,unsigned y,unsigned h,unsigned color){for(unsigned p=0;p<5;p++)for(unsigned yy=y;yy<y+h;yy++)memset(screens[b]+p*PLANE+(origin+yy)*40+4,(color&(1<<p))?255:0,32);}
static unsigned glyph(char c){
 if(c>='A'&&c<='Z')return c=='O'?0xf4:0xda+c-'A';
 if(c>='0'&&c<='9')return 0xf4+c-'0';
 if(c=='-')return 0xe8;
 return 0;
}
static void text(unsigned b,unsigned x,unsigned y,const char *s,unsigned color){
 for(;*s && x<=248;s++,x+=8){unsigned t=glyph(*s);if(!t)continue;const u8 *g=chr+t*16;
  for(unsigned r=0;r<8;r++)for(unsigned k=0;k<8;k++)if((g[r]|g[r+8])&(128>>k))pixel(b,x+k,y+r,color);
 }
}
static void centered(unsigned b,unsigned y,const char *s,unsigned color){unsigned n=0;while(s[n])n++;text(b,(256-n*8)/2,y,s,color);}
static void number(char *s,u32 n,unsigned digits){s[digits]=0;while(digits){s[--digits]='0'+n%10;n/=10;}}
void menu_draw(unsigned b,unsigned kind,unsigned choice,unsigned cursor,const char *initials,u32 score,int status){
 render_menu_preview(b,choice,kind==1);
 origin=((frame_ctrl&2)?240:0)+frame_sy;if(origin>=480)origin-=480;
 frame_pal[17]=0x30;frame_pal[18]=0x28;frame_pal[19]=0x12;
 if(kind==1){
  rect(b,0,40,0);rect(b,184,56,0);rect(b,39,1,18);rect(b,184,1,18);
  centered(b,8,"STAGE SELECT",17);
  char label[]="STAGE 00 OF 16";label[6]='0'+(choice+1)/10;label[7]='0'+(choice+1)%10;centered(b,24,label,18);
  centered(b,196,"ARROWS CHOOSE STAGE",17);centered(b,212,"FIRE OR ENTER START",18);centered(b,228,"TAB HIGH SCORES",17);
 }else if(kind==2){
  centered(b,12,"TOP 10 HIGH SCORES",18);text(b,16,36,"NO  NAME   SCORE   STAGE",19);
  for(unsigned i=0;i<10;i++){
   unsigned y=52+i*12;char n[7];number(n,i+1,2);text(b,16,y,n,17);char name[4];memcpy(name,scores[i].initials,3);name[3]=0;text(b,48,y,name,17);
   number(n,scores[i].score,6);text(b,104,y,n,18);
   if(scores[i].score){number(n,scores[i].stage,2);text(b,192,y,n,17);}else text(b,192,y,"--",17);
  }
  if(status==1)centered(b,184,"SCORES SAVED",18);
  if(status<0){centered(b,184,"SAVE FAILED",18);centered(b,200,"FIRE RETRIES SAVE",17);}
  else centered(b,216,"FIRE OR TAB BACK",17);
 }else if(kind==4){
  centered(b,24,"GAME OVER",18);centered(b,60,"CONTINUE",17);
  centered(b,100,choice?"  YES      - NO -":"- YES -      NO  ",18);
  centered(b,144,"CURRENT STAGE",17);centered(b,160,"THREE LIVES",17);centered(b,176,"SCORE RESETS TO ZERO",18);
  centered(b,212,"ARROWS CHOOSE",17);centered(b,228,"FIRE OR ENTER CONFIRM",17);
 }else{
  centered(b,24,"NEW HIGH SCORE",18);char n[7];number(n,score,6);centered(b,48,n,17);
  centered(b,76,"ENTER YOUR INITIALS",17);
  for(unsigned i=0;i<3;i++){char c[2]={initials[i],0};text(b,104+i*16,112,c,i==cursor?18:17);if(i==cursor)for(unsigned x=104+i*16;x<112+i*16;x++)pixel(b,x,123,18);}
  centered(b,156,"UP DOWN CHANGE LETTER",17);centered(b,172,"LEFT RIGHT MOVE",17);centered(b,196,"FIRE NEXT LETTER",18);centered(b,212,"ENTER SAVES INITIALS",17);
 }
 render_copper(b);
}
