#include "engine.h"
/* Rendering owns this immutable snapshot until its copper list is published.
 * The original game can keep updating while the inactive bitmap is built. */
u8 frame_nt[2048],frame_oam[256],frame_pal[32];
u8 frame_ctrl,frame_mask,frame_bank,frame_sx,frame_sy;
/* Host rendering tests have no clock. The native main supplies the clock
 * service hook so long sprite passes can yield between small pieces. */
void __attribute__((weak)) render_yield(void){}
void render_snapshot(void){
 memcpy(frame_nt,nt,sizeof(frame_nt));memcpy(frame_oam,oam,sizeof(frame_oam));memcpy(frame_pal,pal,sizeof(frame_pal));
 frame_ctrl=ctrl;frame_mask=mask;frame_bank=bank;frame_sx=sx;frame_sy=sy;
}
