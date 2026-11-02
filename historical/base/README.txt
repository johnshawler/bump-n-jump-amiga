Bump n Jump — stock A1200 source package

The delivered HDF boots a standalone 68020 executable with translated
cartridge logic, native bitplanes, hardware scrolling, software sprites,
and approximate Paula audio. It does not need an NES emulator installed
on the Amiga. Unvisited CPU paths have a bounded C fallback.

Build the included generated source:
  python3 build.py
Set AMIGA_TOOLS to a BartmanAbyss-style m68k-amiga-elf toolchain directory
containing opt/bin/m68k-amiga-elf-gcc and elf2hunk. The default is the
installed 1.8.2 extension on the originating Mac. No Amiga C library is
required; Kickstart 3.1 libraries supply OS services.

Regeneration:
  Install requirements.txt and put the original supplied cartridge next
to these scripts as Bump 'n' Jump (USA).nes. Its SHA256 is checked.
  python3 generate_asm.py
  python3 generate_sprites.py
  python3 build.py
The generated sources and atlases are already included, so the original
cartridge file is not needed for an ordinary build.

CPU: src/cpu_native.s keeps the source CPU state in 68020 registers.
The generator conservatively removes flag values overwritten before use.
Six complete routines use source-checked C fast paths. src/cpu.c is the
slower C reference implementation and is not linked into the release.

Graphics: two 320x720 five-plane buffers hold the circular 480-line world
plus its wrap. A copper list selects the 256x240 viewport. Sprite rows use
pre-shifted plane/mask data. Source input is sampled from the real Amiga
joystick registers and keyboard serial interface. Source ticks are kept
on an NTSC/PAL accumulator; catch-up is bounded per publication.

Tests: 15,000 C-reference frames, 18,000 randomized ROM routine comparisons,
10,000 guarded memory operations, native CPU/RAM/VRAM/OAM/palette and
61,440-pixel checks, and an exact release HDF run driven through emulated
Amiga keyboard and joystick hardware. Details and scope are in evidence.
The controller test needs a local FS-UAE build with Lua input sending
and headless raster capture enabled; it is not required to play the HDF.

This is an experimental port. Audio is approximate. It has not completed
a physical A1200 test or an entire-campaign playthrough. Busy-scene
slowdowns are documented in the delivered Read-Me.txt.

Original game: Data East / Vic Tokai. The supplied USA cartridge is the
source. Py65 opcode metadata/reference testing uses its accompanying BSD
license. The original handoff archive contained engineering notes only;
its Windows project source and unfinished 034 executable were not used.

The diagnostic input recorder retains at most 16,384 source ticks.

To package a rebuilt executable as an HDF, install amitools and run
python3 package.py. It also creates the test configuration. Update the
Kickstart path for another host. Hardware tests use a private local FS-UAE
with Lua input sending, configured in controller_test.py.
