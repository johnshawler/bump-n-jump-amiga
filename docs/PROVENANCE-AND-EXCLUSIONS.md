# Provenance and exclusions

Consolidated November 2, 2026, from preserved Mac source packages and working files dated October 19–20, 2026. Source originals, old builds, checkpoints and archives were not modified or removed. No preexisting local Git history was imported; only the audited publication tree is committed.

## Recovered

The four filtered historical snapshots correspond to `source-package`, `clock-source-package`, `optimized-source-package`, and `menus-source-package`. The root collects the later local working runtime, standalone Python tooling and stage-select generators. Original source-package release notes are retained as historical descriptions, even where they mention files omitted here. Local username paths in copied text were replaced with `/path/to/local-user`. Root build/packaging entry points received small portability changes described in `provenance.json`.

Earlier Windows project locators in the handoff notes are historical references, not available source trees. Raw task conversations and their message dumps were not copied into the public repository. Copied verification JSON is historical reported evidence, not a new test pass. `release-inventory.json` inventories original local outputs without distributing them.

## Excluded from the public tree

- Original `.nes` cartridge, other original ROMs, Kickstart, Workbench and unrelated games.
- `src/assets.c` (literal cartridge PRG/CHR), `src/cpu.c`, `src/cpu_native.s`, `src/cpu_helpers.c` (generated cartridge logic), `src/stage_previews.c` (original-game snapshots), and generated `src/sprites.s` (regenerated alongside private atlases).
- Binary graphics atlases, game executables, objects, libraries, disk images, save states, RAM/VRAM dumps, screenshots and audio captures.
- Original release/source ZIPs and LHA files; these can contain the above material. Hashes identify the retained originals.
- Private tool installations, virtual environments, unrelated conversations, credentials and machine/account configuration. No original Git history was published.
- Promotional images whose underlying asset/branding permissions were not established.

The generators are supplied so an owner can reconstruct the missing cartridge-derived inputs privately. Generated files remain ignored. No claim is made that the public checkout is a ready-to-run game or that its complete regeneration has been validated during consolidation.

## Later patch-based work and unavailable material

The separate October 25 DX/WHDLoad task began from an HDF containing a compiled `BumpNJump`, startup files and high scores. Original source/build files were requested but were not supplied. This was a binary-patching task, not evidence of an available complete original source tree.

The later record describes patch/build tooling in a cloud project at `/workspace/bumpnjump`, including `tools/build.py`, `tools/build_whdload.py`, `tools/package_whdload.py`, `tools/build_stage_music.py`, native/menu changes, `delivery/WHDLOAD-RELEASE.md`, `delivery/whdload-manifest.json`, and validation receipts under `evidence/whdload-final-validation/`.

The following final outputs were recorded there but not located on this Mac or resolved in Library searches:

- `/workspace/bumpnjump/delivery/BumpNJump-DX-WHDLoad.lha`
- `/workspace/bumpnjump/delivery/BumpNJump-DX-WHDLoad.zip`
- `/workspace/bumpnjump/delivery/BumpNJumpDX/` and its slave/data files
- The later patch/build scripts, wrapper/native/menu changes, resource inputs, dependency versions and validation receipts

These paths identify missing material on a different host; they are not local paths or download links. The original cloud task was readable as a development record, but was not resumed and its filesystem could not be retrieved with the available tools. Recovering those patch/build materials and final outputs is necessary before this repository can document the full later DX effort. Even that recovery would not establish that the original pre-patch source was ever supplied. Any recovered additions need the same cartridge-data and rights review before publication.
