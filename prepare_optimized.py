from pathlib import Path
import shutil
R=Path(__file__).resolve().parent;O=R.parent/'outputs/BumpNJump-A1200-Optimized';O.mkdir(exist_ok=True)
name='BumpNJump-A1200-Optimized'
shutil.copyfile(R/'build/BumpNJump-A1200.hdf',O/(name+'.hdf'))
s=(R.parent/'outputs/BumpNJump-A1200.fs-uae').read_text().replace('./BumpNJump-A1200.hdf','./'+name+'.hdf').replace('Bump n Jump - Stock A1200','Bump n Jump - Optimized Stock A1200')
(O/(name+'.fs-uae')).write_text(s)
p=O/'Play-BumpNJump-Optimized.command';p.write_text('#!/bin/zsh\ncd -- "${0:A:h}"\nexec /Applications/FS-UAE.app/Contents/MacOS/fs-uae ./'+name+'.fs-uae\n');p.chmod(0o755)
(O/'Read-Me.txt').write_text('''BUMP 'N' JUMP — OPTIMIZED STOCK A1200 BUILD

Bootable 8 MiB hard disk image for a PAL A1200:
68EC020, AGA, 2 MB Chip RAM, no Fast/Slow/Z3 RAM or accelerator.
Use your own A1200 Kickstart 3.1 ROM. No Workbench installation is needed.

PLAY ON THIS MAC

Unzip the package and double-click Play-BumpNJump-Optimized.command.
Allow the original title sequence to appear. The supplied profile uses the
Kickstart ROM already present on this Mac. Choose your own ROM elsewhere.

CONTROLS

Joystick in Amiga game port 2:
  Fire: start from title; jump during play at 150 km/h or faster
  Up: accelerate
  Down: slow down
  Left / Right: steer
Hold Up to build speed. Release Fire between jumps.

Keyboard:
  Return: Start / pause
  Arrow keys or W/A/S/D: drive
  Space or Ctrl: Fire / jump
  Shift: second NES action button
  Tab: Select
  Escape: quit; reset the Amiga to play again
The included FS-UAE profile also maps Q to joystick Fire. Click the
emulator window if it does not have keyboard focus.

HDF SETUP

Attach BumpNJump-A1200-Optimized.hdf as the first bootable hard drive, DH0.
This is a plain FFS partition hardfile, without an RDB partition table.
Geometry: 512-byte blocks, 32 sectors, 1 surface, 2 reserved blocks.
Leave floppy drives empty and disable JIT, Fast/Slow/Z3 RAM and accelerators.

WHAT CHANGED

Native Amiga hardware sprites now draw most cars and many HUD elements.
Channels are reused vertically. Objects that overlap or exceed channel
capacity use the original software renderer, preserving drawing order.
Transparent tiles are skipped. Hardware sprite data is double buffered.

Car construction, controller sampling, a RAM sprite copy, and a common
coordinate routine have faster implementations checked against the ROM.
The original cartridge logic, level data, collision rules, scoring, fuel,
jump timing and source clock are retained. No source ticks are discarded.

VALIDATION AND LIMITS

The final release was tested in stock A1200 emulation with 2 MB Chip RAM
and no expansion RAM, JIT or accelerator. Exact controller inputs were
replayed against the original ROM: CPU state, RAM, background data,
sprite data, palette and all 61,440 viewport pixels matched. The actual
emulated raster also matched, including hardware sprite color/alignment.
Both tested jumps lasted the original 96 source ticks and held Fire did
not trigger a second jump.

Performance and comparison figures are in Verification.json. This is an
experimental port: heavy scenes can still slow down, Paula sound is
approximate, and physical A1200 hardware and the full campaign remain
untested. The earlier HDF is preserved separately as a fallback.

Built from the supplied USA cartridge. No Kickstart ROM or Workbench
files are included. Original game: Data East / Vic Tokai.
''')
print(O)
