# Bump ’n’ Jump — Amiga A1200 port archive

Recovered port code, generators, development tools and historical reports for an experimental Bump ’n’ Jump Amiga port. Target: stock PAL A1200, 68EC020, AGA, 2 MiB Chip RAM, no expansion RAM or JIT.

**This is a partial source archive. The later DX/WHDLoad patch/build materials and release files have not been recovered.** The root contains the latest preserved Mac working files from October 20, 2026, including stage selection, saved high scores and continue. It is not the later DX release. No playable binary, original game ROM, cartridge-derived generated code, graphics, audio or Kickstart is distributed here.

## Contents

- `src/`: recovered Amiga runtime, rendering, hardware sprites, menu, score, audio and memory code.
- Root Python scripts: code and graphics generators, host comparisons, packaging, profiling and earlier script revisions.
- `stage-select/`: preview generation and score-readback tools.
- `historical/{base,60hz,optimized,stage-select}/`: filtered source snapshots of four preserved source packages. Their README files describe the original complete local packages; the exclusions below take precedence for this public archive.
- `evidence/`: preserved stage-select verification summaries. They are historical reports, not new test results.
- `docs/handoff-2026-10-19/`: engineering notes from an earlier Windows-host effort; referenced Windows source and raw evidence were not recovered here.
- `docs/provenance.json`: per-file origins and original/published hashes.
- `docs/release-inventory.json`: 44 preserved local release files, with sizes and SHA-256 hashes; original files remain untouched on the owner's Mac.

See [build instructions](docs/BUILD.md), [provenance and exclusions](docs/PROVENANCE-AND-EXCLUSIONS.md), and [rights and dependencies](RIGHTS.md).

## Status

The preserved Mac reports describe CPU/reference comparisons, renderer comparisons, input replay, score persistence and emulator observations in their stated scopes. They do not establish physical A1200 validation or a completed full campaign. Audio and PPU handling have known approximations; heavy scenes can slow down.

The separate later DX/WHDLoad development record reported stock PAL A1200 **FS-UAE** checks for gameplay, cold-boot high scores and F10/Escape exit, with the 50 FPS target still unmet. That task patched a compiled game image; original source/build files were not supplied. Its later patch/build materials, releases and machine-readable receipts are unavailable in this archive, so those claims have not been independently verified during consolidation.

## Credits

Credits recorded for the later DX work:

- Original Arcade version Copyright 1982 Data East
- Original NES version Copyright 1988 Vic Tokai
- Amiga DX version by Boatofcar
- Special Thanks to JOTD

These credits do not grant redistribution rights to the original game. No blanket open-source license is assigned to this collection; see `RIGHTS.md`.
