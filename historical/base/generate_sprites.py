from pathlib import Path
import struct
R=Path(__file__).resolve().parent;c=(R/"Bump 'n' Jump (USA).nes").read_bytes()[32784:];out=bytearray()
def rev(v):return int(f'{v:08b}'[::-1],2)
for bank in range(4):
 for tile in range(256):
  for flip in range(2):
   for shift in range(8):
    for row in range(8):
     p0=c[bank*8192+tile*16+row];p1=c[bank*8192+tile*16+row+8]
     if flip:p0=rev(p0);p1=rev(p1)
     a=(p0<<8)>>shift;b=(p1<<8)>>shift;out+=struct.pack('>HHH',a,b,a|b)
(R/'build/sprite-atlas.bin').write_bytes(out)
s='''.section .rodata.sprite_atlas,"a"
.balign 4
.globl sprite_atlas
sprite_atlas:
.incbin "build/sprite-atlas.bin"
.section .text.sprite_rows,"ax"
.globl sprite_rows
sprite_rows:
movem.l %d2-%d7/%a2-%a6,-(%sp)
move.l 48(%sp),%a0
move.l 52(%sp),%a1
move.l 56(%sp),%a2
lea 28800(%a0),%a3
lea 28800(%a3),%a4
lea 28800(%a4),%a5
lea 28800(%a5),%a6
move.l 60(%sp),%d7
subq.w #1,%d7
move.l 68(%sp),%d5
move.l 72(%sp),%d6
move.l 80(%sp),%d4
tst.l 76(%sp)
bne choose_behind
tst.l 64(%sp)
bmi row_front_reverse
bra row_front_forward
choose_behind:
tst.l 64(%sp)
bmi row_behind_reverse
bra row_behind_forward
'''
for behind in [False,True]:
 for reverse in [False,True]:
  label='row_'+('behind' if behind else 'front')+'_'+('reverse' if reverse else 'forward')
  s+=label+''':
move.w (%a1)+,%d1
move.w (%a1)+,%d2
move.w (%a1)+,%d0
and.w %d4,%d0
move.w (%a2),%d3
or.w %d0,(%a2)
not.w %d3
and.w %d3,%d0
'''
  if behind:s+='move.w (%a0),%d3\nor.w (%a3),%d3\nnot.w %d3\nand.w %d3,%d0\n'
  s+='''tst.w %d0
beq 1f
move.w %d0,%d3
not.w %d3
and.w %d0,%d1
and.w %d0,%d2
and.w %d3,(%a0)
or.w %d1,(%a0)
and.w %d3,(%a3)
or.w %d2,(%a3)
move.w %d0,%d1
and.w %d5,%d1
and.w %d3,(%a4)
or.w %d1,(%a4)
move.w %d0,%d1
and.w %d6,%d1
and.w %d3,(%a5)
or.w %d1,(%a5)
or.w %d0,(%a6)
1:
lea 40(%a0),%a0
lea 40(%a3),%a3
lea 40(%a4),%a4
lea 40(%a5),%a5
lea 40(%a6),%a6
lea 32(%a2),%a2
'''
  if reverse:s+='lea -12(%a1),%a1\n'
  s+=f'dbra %d7,{label}\nbra rows_done\n'
s+='rows_done:\nmovem.l (%sp)+,%d2-%d7/%a2-%a6\nrts\n'
(R/'src/sprites.s').write_text(s);print('Precomputed sprite bytes',len(out))
bg=bytearray()
for bank in range(4):
 for tile in range(256):
  for row in range(8):
   a=c[bank*8192+4096+tile*16+row];b=c[bank*8192+4096+tile*16+row+8];bg+=bytes([a,b,a|b])
(R/'build/bg-atlas.bin').write_bytes(bg)
s+='''
.section .rodata.bg_atlas,"a"
.balign 4
.globl bg_atlas
bg_atlas:
.incbin "build/bg-atlas.bin"
.section .text.draw_bg_tile,"ax"
.globl draw_bg_tile
draw_bg_tile:
movem.l %d2-%d5/%a2-%a5,-(%sp)
move.l 36(%sp),%a0
move.l 40(%sp),%a1
move.l 44(%sp),%d3
move.l 48(%sp),%d4
lea 28800(%a0),%a2
lea 28800(%a2),%a3
lea 28800(%a3),%a4
lea 28800(%a4),%a5
moveq #7,%d5
bg_row:
move.b (%a1)+,(%a0)
move.b (%a1)+,(%a2)
move.b (%a1)+,%d0
move.b %d0,%d1
and.b %d3,%d0
and.b %d4,%d1
move.b %d0,(%a3)
move.b %d1,(%a4)
clr.b (%a5)
lea 40(%a0),%a0
lea 40(%a2),%a2
lea 40(%a3),%a3
lea 40(%a4),%a4
lea 40(%a5),%a5
dbra %d5,bg_row
movem.l (%sp)+,%d2-%d5/%a2-%a5
rts
'''
(R/'src/sprites.s').write_text(s)
