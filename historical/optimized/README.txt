Bump n Jump — optimized stock A1200 source package

The HDF boots a standalone 68020 executable using the cartridge's original
logic and data, native bitplanes, hardware scrolling, hybrid hardware /
software sprites and approximate Paula audio. No NES emulator installation
or Workbench files are needed on the Amiga.

BUILD
  python3 build.py
  python3 package.py
Set AMIGA_TOOLS to a BartmanAbyss-style m68k-amiga-elf toolchain directory
containing opt/bin/m68k-amiga-elf-gcc and elf2hunk. The originating Mac's
installed extension is the default. The generated source and atlases are
included; the raw cartridge is unnecessary for an ordinary build. A clean
rebuild reproduces every parsed hunk (code, data, sizes, relocations and
symbols). elf2hunk can leave different ignored padding bytes after debug
symbol names; see evidence/source-rebuild-verification.json.
package.py uses amitools to create the 8 MiB plain FFS HDF. The test profile
needs your own A1200 Kickstart 3.1 ROM; update its local path as needed.

REGENERATION
Install requirements.txt and supply Bump 'n' Jump (USA).nes next to these
scripts. generate.py checks the ROM SHA256. Then run:
  python3 generate_asm.py
  python3 generate_sprites.py
  python3 build.py

CPU
The primary path in cpu_native.s keeps source CPU registers in 68020
registers. cpu_helpers.c supplies source-checked fast routines and a bounded
unseen-instruction fallback. cpu.c is a host-testable C reference, not part
of the release binary. Eight routines have randomized original-ROM tests;
the coordinate helper uses an equivalent short native assembly path.
The common car builder uses known RAM/ROM addresses directly. The sprite
copy uses bulk copying only in a safe RAM range without source overlap.
The serial controller sampler retains all original RAM and CPU outputs.

GRAPHICS
Two 320x720 five-plane bitmaps cache a 480-line circular world plus wrap.
The copper selects a 256x240 viewport without copying the whole display.
hw_sprites.c groups adjacent NES tiles into 16-pixel-wide sprites, matches
four source palettes to the four hardware channel pairs, and reuses each
channel vertically with a blank line between objects. Each buffer has
8 x 1024 bytes of Chip RAM for DMA lists. These and the copper are swapped
outside active display, before initial sprite control fetch when near the
top of a field. BPLCON4 selects color bank 16 for both even and odd sprites.
The horizontal origin was checked against the actual completed AGA raster.

Overlapping groups, behind-background groups, source 8x16/upper-table modes
and channel overflow use the original software path. There is no object
culling to conceal capacity limits. Empty tiles are ignored. Hardware data
is built in the inactive buffer. Gameplay never copies hardware objects
into the bitmaps; hw_export decodes the emitted DMA lists only for debug
receipts. Actual-raster comparison independently checks the hardware output.

VALIDATION
15,000 source frames compare CPU state and all RAM/VRAM/OAM/palettes against
py65. Eight fast routines pass 24,000 randomized original-ROM cases. The
renderer has 1,100 source/random cases spanning 15,000 source ticks and all
67,584,000 compared pixels. The controller and stress tests replay their
exact native input logs against the source ROM. The final paused emulator
raster has zero differences across 245,760 displayed pixels. Both jumps
retain their original 96-tick duration without held-button retriggering.
See evidence/Verification.json for performance and precise test scope.

Host C-reference tests need a Mac-built build/engine.dylib. Build it with
clang -dynamiclib -O2 -fno-builtin src/cpu.c src/bus.c src/assets.c
src/audio.c src/memory.c -o build/engine.dylib (as one command).
The controller/benchmark/raster tests use the originating Mac's private
FS-UAE build with Lua input sending and raster capture. Those optional
host dependencies are not needed to build or play the HDF. Diagnostic
input logs retain at most 16,384 source ticks.

LIMITS
This is an experimental port. Heavy scenes can still slow down. Paula
sound and frame-boundary PPU handling are approximate. Physical A1200
hardware and the complete campaign remain untested. The source clock keeps
all due ticks; these optimizations do not discard gameplay updates.

Original game: Data East / Vic Tokai. Source: supplied USA cartridge.
No Kickstart ROM or Workbench files are included. Py65's BSD license is
included. The handoff supplied engineering notes, not the old source tree.
