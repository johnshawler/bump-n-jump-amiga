#include "engine.h"
void *memcpy(void *d,const void *s,unsigned long n){
 u8 *a=d;const u8 *b=s;
 if(!(((unsigned long)a|(unsigned long)b)&3)){
  u32 *x=(u32*)a;const u32 *y=(const u32*)b;
  while(n>=32){x[0]=y[0];x[1]=y[1];x[2]=y[2];x[3]=y[3];x[4]=y[4];x[5]=y[5];x[6]=y[6];x[7]=y[7];x+=8;y+=8;n-=32;}
  while(n>=4){*x++=*y++;n-=4;}a=(u8*)x;b=(const u8*)y;
 }
 while(n--)*a++=*b++;return d;
}
void *memset(void *d,int v,unsigned long n){
 u8 *a=d;u32 fill=(u8)v;fill|=fill<<8;fill|=fill<<16;
 while(n && ((unsigned long)a&3)){*a++=v;n--;}
 u32 *x=(u32*)a;
 while(n>=32){x[0]=fill;x[1]=fill;x[2]=fill;x[3]=fill;x[4]=fill;x[5]=fill;x[6]=fill;x[7]=fill;x+=8;n-=32;}
 while(n>=4){*x++=fill;n-=4;}a=(u8*)x;while(n--)*a++=v;return d;
}
