#include "engine.h"
#define R16(o) (*(volatile u16*)(0xdff000+(o)))
#define R32(o) (*(volatile u32*)(0xdff000+(o)))
u8 *waves;
u32 audio_write_hash=2166136261u,audio_writes,audio_publications;
u16 audio_period[4],audio_volume[4];
static u8 length[4],env[4],envclock[4],envstart[4],linear,reload;
static const u8 lengthtable[32]={10,254,20,2,40,4,80,6,160,8,60,10,14,12,26,14,12,16,24,18,48,20,96,22,192,24,72,26,16,28,32,30};
static const u16 noiseperiod[16]={4,8,16,32,64,96,128,160,202,254,380,508,762,1016,2034,4068};
static u8 dutylast[2]={255,255};
void apu_write(unsigned addr,u8 value){
 audio_write_hash=(audio_write_hash*33)^((addr<<8)|value);audio_writes++;
 unsigned r=addr-0x4000,c=r>>2;
 if(r==0x15){for(unsigned j=0;j<4;j++)if(!(value&(1<<j)))length[j]=0;return;}
 if(c>=4)return;
 if((r&3)==3){if(apu[0x15]&(1<<c))length[c]=lengthtable[value>>3];envstart[c]=1;if(c==2)reload=1;}
}
void audio_init(void){
 u16 lfsr=1;
 for(unsigned i=0;i<1024;i++){
  unsigned feedback=(lfsr^(lfsr>>1))&1;lfsr=(lfsr>>1)|(feedback<<14);waves[128+i]=(lfsr&1)?100:-100;
 }
 for(unsigned i=0;i<32;i++)waves[64+i]=(i<16)?(u8)(120-i*16):(u8)(-120+(i-16)*16);
 for(unsigned c=0;c<4;c++){
  unsigned offset=c*16;if(c==2)offset=64;if(c==3)offset=128;
  R32(0xa0+c*16)=(u32)(waves+offset);R16(0xa4+c*16)=c<2?8:c==2?16:512;R16(0xa6+c*16)=400;R16(0xa8+c*16)=0;
 }
}
void audio_tick(void){
 for(unsigned quarter=0;quarter<4;quarter++){
  for(unsigned c=0;c<4;c++)if(c!=2){u8 v=apu[c*4];if(envstart[c]){envstart[c]=0;env[c]=15;envclock[c]=v&15;}else if(envclock[c])envclock[c]--;else{envclock[c]=v&15;if(env[c])env[c]--;else if(v&32)env[c]=15;}}
  if(reload)linear=apu[8]&127;else if(linear)linear--;
  if(!(apu[8]&128))reload=0;
  if(quarter&1)for(unsigned c=0;c<4;c++){if(length[c] && !(apu[c*4]&(c==2?128:32)))length[c]--;}
 }
}
void audio_publish(void){
 audio_publications++;
 for(unsigned c=0;c<4;c++){
  unsigned v=apu[c*4],timer=apu[c*4+2]|((apu[c*4+3]&7)<<8),per=(timer+1)*2,vol=0;
  if(c<2){unsigned duty=v>>6;if(duty!=dutylast[c]){dutylast[c]=duty;unsigned count=duty==0?2:duty==1?4:duty==2?8:12;for(unsigned k=0;k<16;k++)waves[c*16+k]=k<count?100:-100;}
   if(length[c] && timer>=8)vol=((v&16)?v&15:env[c])*4;
  }else if(c==2){if(length[c] && linear && timer>=2)vol=32;}
  else{per=noiseperiod[apu[14]&15]*2;if(length[c])vol=((v&16)?v&15:env[c])*3;}
  if(per<124)per=124;if(per>65535)per=65535;
  audio_period[c]=per;audio_volume[c]=vol;R16(0xa6+c*16)=per;R16(0xa8+c*16)=vol;
 }
}
