# Building the recovered Mac version

These instructions cover the recovered stage-select working tree, not the missing DX/WHDLoad release. Regeneration and building were not run during this publication task. Historic source-package reports describe previous builds of complete local packages that included generated game data. The public tree intentionally omits those files.

## Dependencies and private inputs

Use Python 3 with `requirements.txt`, plus a BartmanAbyss-style Amiga toolchain containing `opt/bin/m68k-amiga-elf-gcc`, the Amiga headers, and `elf2hunk`. Set `AMIGA_TOOLS` to that toolchain directory. Install dependencies into an isolated environment of your choice.

Supply your own authorized USA NES cartridge dump at the repository root as `Bump 'n' Jump (USA).nes`. The generators expect SHA-256:

`40e45122fc9ecbda7e94a18c3b4ff6b5022675220872bbc6f02107ec842ce6a6`

No ROM download is provided. Keep the cartridge and generated files private and ignored by Git.

## Regenerate and compile

From the repository root, with Python dependencies active:

```sh
mkdir -p build
python3 reference.py
python3 generate_asm.py
python3 generate_sprites.py
python3 stage-select/generate_previews.py
export AMIGA_TOOLS=/absolute/path/to/toolchain
python3 build.py
```

`reference.py` generates `build/trace.json` from an original-game run. `generate_asm.py` invokes `generate.py` and creates `src/assets.c`, `src/cpu.c`, `src/cpu_helpers.c` and `src/cpu_native.s`. `generate_sprites.py` creates `src/sprites.s` and binary atlases. The preview generator creates `src/stage_previews.c`. These files are excluded from publication because they contain or translate original-game material. The intended executable output is `build/BumpNJump`.

## Optional HDF packaging

With amitools available in your active Python environment:

```sh
export KICKSTART_FILE=/absolute/path/to/your/authorized/A1200-Kickstart.rom
python3 package.py
```

This creates `build/BumpNJump-A1200.hdf` and a local FS-UAE profile under `test/`. Kickstart is needed for emulator execution, not compilation. The root packaging script uses the active Python interpreter and installed amitools. Other historical scripts retain redacted machine-specific paths and may require local adaptation. Release-publishing scripts also expect the original workspace's sibling `outputs/` layout; they are archived tooling, not the recommended public build entry point.

## Historical snapshots and testing

Each `historical/` snapshot preserves its own scripts and non-generated runtime. Earlier variants lack later menu/preview steps. Consult their preserved README files together with the public exclusions, and adapt their local tool paths before use.

Host comparison tests can require a separately built `build/engine.dylib`, an original ROM, generated files and the originating private FS-UAE build with Lua input/raster hooks. No emulator or gameplay tests were rerun for publication. The provided reports retain their original dates and bounded scopes.
