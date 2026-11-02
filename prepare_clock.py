from pathlib import Path
import shutil
R=Path(__file__).resolve().parent;N='BumpNJump-A1200-60Hz';O=R.parent/'outputs'/N;O.mkdir(exist_ok=True)
shutil.copyfile(R/'build/BumpNJump-A1200.hdf',O/(N+'.hdf'))
s=(R.parent/'outputs/BumpNJump-A1200.fs-uae').read_text().replace('./BumpNJump-A1200.hdf','./'+N+'.hdf').replace('Bump n Jump - Stock A1200','Bump n Jump - 60 Hz game clock - Stock A1200');(O/(N+'.fs-uae')).write_text(s)
p=O/'Play-BumpNJump-60Hz.command';p.write_text('#!/bin/zsh\ncd -- "${0:A:h}"\nexec /Applications/FS-UAE.app/Contents/MacOS/fs-uae ./'+N+'.fs-uae\n');p.chmod(0o755)
(O/'Read-Me.txt').write_text('''BUMP 'N' JUMP — 60 HZ GAME CLOCK BUILD

A bootable 8 MiB HDF for a stock PAL A1200: 68EC020, AGA, 2 MB Chip RAM,
no Fast/Slow/Z3 RAM or accelerator. Use your own A1200 Kickstart 3.1 ROM.
No Workbench installation is required.

PLAY

Unzip the package and double-click Play-BumpNJump-60Hz.command on this Mac.
The supplied FS-UAE profile uses the Kickstart ROM already installed here.
Select your own A1200 ROM elsewhere. Leave floppy drives empty.

For other setups, attach BumpNJump-A1200-60Hz.hdf as the first bootable DH0.
It is a plain FFS partition hardfile without an RDB. Geometry: 512-byte
blocks, 32 sectors, 1 surface, 2 reserved blocks. Disable JIT and expansion
RAM. A physical drive needs an appropriate Amiga partition setup.

CONTROLS

Joystick in Amiga game port 2:
  Fire: start at the title; jump at 150 km/h or faster during play
  Up / Down: accelerate / slow down
  Left / Right: steer
Hold Up to build speed; release Fire between jumps.

Keyboard:
  Return: Start / pause
  Arrows or W/A/S/D: drive
  Space or Ctrl: Fire / jump
  Shift: second NES action button
  Tab: Select
  Escape: quit; reset the Amiga to play again
The profile also maps Q to joystick Fire. Click the window for keyboard focus.

WHAT CHANGED

The game now services its original roughly 60.1-Hz clock between small
pieces of drawing work. Crowded graphics cannot hold up several game ticks.
Each picture uses a frozen snapshot, so gameplay can continue while it is
built. The display swaps at vertical blank. Road tiles are drawn only when
needed in the visible area. Native return/dispatch handling is also faster.

Sound is published on every game tick. Short original event cues are no
longer skipped between displayed pictures. Original sound-register writes
were checked in order against the cartridge. Game-Event-Audio.wav contains
actual emulated Paula output around a jump and subsequent gameplay.
Paula synthesis remains approximate.

The original logic, level data, collisions, scoring, fuel and jump rules
are retained. Every due game tick is kept. Drawing yields to gameplay and
sound, so the visible frame rate varies and can be low in crowded scenes.
Level-loading pauses remain. This build prioritizes the game clock.

Verification.json records timing, per-tick CPU/audio replays, pixel checks
and test scope. Tests used stock A1200 emulation with only 2 MB Chip RAM.
The build has not been tested on a physical A1200 or through the complete
campaign. The previous optimized HDF remains available separately.

No Kickstart ROM or Workbench files are included.
Original game: Data East / Vic Tokai. Built from the supplied USA cartridge.
''')
print(O)
