.section .text.start,"ax"
.globl _start
_start:
 movem.l %d2-%d7/%a2-%a6,-(%sp)
 jsr main
 movem.l (%sp)+,%d2-%d7/%a2-%a6
 rts
.globl get_vbr
get_vbr:
 movem.l %a5-%a6,-(%sp)
 move.l 4.w,%a6
 lea vbr_super(%pc),%a5
 jsr -30(%a6)
 movem.l (%sp)+,%a5-%a6
 rts
vbr_super:
 movec %vbr,%d0
 rte
.globl vblank_irq
vblank_irq:
 movem.l %d0/%a0,-(%sp)
 lea 0xdff000,%a0
 move.w 0x1e(%a0),%d0
 and.w #0x20,%d0
 beq 1f
 addq.l #1,fields
 move.w #0x20,0x9c(%a0)
 move.w #0x20,0x9c(%a0)
1:
 movem.l (%sp)+,%d0/%a0
 rte
