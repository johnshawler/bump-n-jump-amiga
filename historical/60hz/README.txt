Bump n Jump — stock A1200 original-game-clock source

Build the generated native source with python3 build.py, then create the
plain 8 MiB FFS HDF with python3 package.py. Set AMIGA_TOOLS to a toolchain
folder containing opt/bin/m68k-amiga-elf-gcc and elf2hunk, in the layout of
the BartmanAbyss extension. Its originating-Mac path is the default. No
Workbench files or NES emulator installation are needed on the Amiga.
Use your own A1200 Kickstart 3.1 ROM and update the generated test profile.

Generated assembly, cartridge assets and atlas binaries are included, so
the raw NES file is not needed for an ordinary build. Regeneration needs
requirements.txt plus the supplied Bump 'n' Jump (USA).nes beside the
scripts. generate.py checks its SHA256. Run generate_asm.py, then
generate_sprites.py, then build.py. cpu.c is a host reference; release
execution uses cpu_native.s and cpu_helpers.c. The jump table stays in
A6 during execution, including native return/indirect dispatch. Amiga ABI
preserves it across C helpers, and cpu_run restores the caller's A6.

The game clock is based on coherent beam/vertical-blank time with the
original NTSC/PAL ratio. All due ticks are serviced before more drawing.
frame.c snapshots source nametables, OAM, palette and display state. The
inactive renderer reads only this snapshot. Background work is divided
into small tile batches; sprite loops call render_yield to service due
game ticks. The host renderer uses a weak no-op hook. Audio publishes on
every game tick, including ones serviced from inside rendering. Rendering
profiling excludes those nested CPU/audio intervals. A small VBlank IRQ
publishes a queued, finished copper list before sprite DMA control fetch.

The circular 480-line world plus wrap still uses two 320x720 five-plane
buffers. Only visible physical tiles need to be valid; source changes
invalidate the right logical page and its independent physical wrap copy.
Software sprites invalidate tiles below them for the next use. Hardware
sprites retain vertical channel reuse, exact palette matching and safe
software fallback for overlaps/priority or channel pressure. No objects
are removed to conceal capacity limits. hw_export is diagnostic only.

Verification includes 1,100 source/random renderer cases over 15,000
source ticks. Cache continuity and live-memory mutations after freezing
are checked against independent expected pixels. Final native controller,
scripted stress and 6,001-tick restart runs compare exact inputs against
the original ROM. Every recorded tick checks CPU-state and ordered APU
write hashes; at most 4,096 such records are retained. Input logs retain
16,384 ticks. Full final RAM/VRAM/OAM/palette, APU registers and viewport
pixels are compared as well. The paused actual emulator raster matches
all 245,760 display pixels. Both tested jumps retain 96-tick duration.
See evidence/Verification.json for precise scopes and timing limits.

Sound checks confirm one Paula publication per source tick and the
original ordered sound-register requests. A separate copy of the local
emulator's dummy audio backend captured real mixed Paula PCM; no emulator
CPU/timing logic was changed. The short delivered WAV covers a jump and
subsequent gameplay. The original emulator and unrelated project files
were reused read-only. Optional capture/test scripts refer to those local
host dependencies and are not needed to build or play the HDF.

For host CPU tests, build build/engine.dylib on macOS using clang
-dynamiclib -O2 -fno-builtin src/cpu.c src/bus.c src/assets.c src/audio.c
src/memory.c -o build/engine.dylib (one command), then run check_cpu.py or
test_intrinsics.py. The preceding build's unchanged C game semantics had
15,000-frame and 24,000-random-case ROM checks. This version also checks
native state on each recorded tick. Host renderer tests need the dylib,
clang and NumPy. Headless controller tests need the documented local
FS-UAE Lua input/raster API. Tests are optional for ordinary compilation.

A clean rebuild is checked by parsed hunks: code, data, allocation sizes,
relocations and symbols. elf2hunk can vary ignored bytes after a debug
symbol's terminating null; raw-file identity is not required for that
comparison. The delivered HDF itself has an exact recorded SHA256 and
was used unchanged for the final native tests.

This remains experimental. Level-loading source work can cause pauses
and catch-up. Display poses can be sparse in busy scenes because game
logic and sound take priority. Paula synthesis/PPU handling are approximate.
Physical hardware and the complete campaign have not been verified.

Original game: Data East / Vic Tokai; source is the supplied USA cartridge.
No Kickstart ROM or Workbench files are included. Py65's BSD license is
included. The original handoff contained engineering notes only.
