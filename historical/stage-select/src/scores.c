#include "menu.h"
struct Score scores[10];
u32 scores_generation;
static u32 get32(const u8 *p){return ((u32)p[0]<<24)|((u32)p[1]<<16)|((u32)p[2]<<8)|p[3];}
static void put32(u8 *p,u32 n){p[0]=n>>24;p[1]=n>>16;p[2]=n>>8;p[3]=n;}
static u32 checksum(const u8 *p){u32 h=2166136261u;for(unsigned i=0;i<92;i++)h=(h^p[i])*16777619u;return h;}
void scores_reset(void){memset(scores,0,sizeof(scores));scores_generation=0;for(unsigned i=0;i<10;i++)memcpy(scores[i].initials,"---",3);}
/* Fixed byte format; validate before changing the live table. */
int scores_unpack(const u8 *d){
 const char *magic="BNJHS001";for(unsigned i=0;i<8;i++)if(d[i]!=magic[i])return 0;
 if(get32(d+92)!=checksum(d))return 0;
 u32 generation=get32(d+8),previous=1000000;
 for(unsigned i=0;i<10;i++){
  const u8 *p=d+12+i*8;u32 n=get32(p);
  if(n>999999 || n>previous)return 0;
  previous=n;
  if(n){if(p[7]<1 || p[7]>16)return 0;for(unsigned j=4;j<7;j++)if(p[j]<'A'||p[j]>'Z')return 0;}
  else if(p[7] || p[4]!='-'||p[5]!='-'||p[6]!='-')return 0;
 }
 if(scores_generation && (int)(generation-scores_generation)<=0)return 0;
 for(unsigned i=0;i<10;i++){const u8 *p=d+12+i*8;scores[i].score=get32(p);memcpy(scores[i].initials,p+4,3);scores[i].stage=p[7];}
 scores_generation=generation;return 1;
}
void scores_pack(u8 *d,u32 generation){
 memcpy(d,"BNJHS001",8);put32(d+8,generation);
 for(unsigned i=0;i<10;i++){u8 *p=d+12+i*8;put32(p,scores[i].score);memcpy(p+4,scores[i].initials,3);p[7]=scores[i].stage;}
 put32(d+92,checksum(d));
}
int scores_rank(u32 n){if(!n || n>999999)return -1;for(unsigned i=0;i<10;i++)if(n>scores[i].score)return i;return -1;}
void scores_insert(u32 n,unsigned stage,const char *initials){
 int rank=scores_rank(n);if(rank<0)return;
 for(int i=9;i>rank;i--)scores[i]=scores[i-1];
 scores[rank].score=n;scores[rank].stage=stage;memcpy(scores[rank].initials,initials,3);
}
u32 game_score(void){u32 n=0;for(int i=5;i>=0;i--){if(ram[0x4e + i]>9)return 0;n=n*10+ram[0x4e + i];}return n;}
