#ifndef MENU_H
#define MENU_H
#include "engine.h"
struct Score {u32 score;char initials[3];u8 stage;};
extern struct Score scores[10];
extern u32 scores_generation;
void scores_reset(void);
int scores_unpack(const u8 *data);
void scores_pack(u8 *data,u32 generation);
int scores_rank(u32 score);
void scores_insert(u32 score,unsigned stage,const char *initials);
u32 game_score(void);
void menu_draw(unsigned b,unsigned kind,unsigned choice,unsigned cursor,const char *initials,u32 score,int status);
void render_invalidate(void);
void render_menu_preview(unsigned b,unsigned choice,int preview);
#endif
