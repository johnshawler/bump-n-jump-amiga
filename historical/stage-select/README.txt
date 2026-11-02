Native Bump n Jump — stage select, scores and Continue sources

Use BartmanAbyss amiga-debug 1.8.2 m68k-amiga-elf toolchain. Set AMIGA_TOOLS
to its bin/darwin directory if different. Run python3 build.py for the native
executable. Generated CPU/assets/previews are included. The original USA
ROM is needed only for regenerating assets or independent ROM replay tests.
Copy your own Bump 'n' Jump (USA).nes here; expected SHA256 is
40e45122fc9ecbda7e94a18c3b4ff6b5022675220872bbc6f02107ec842ce6a6.

package.py builds the 8 MiB FFS boot HDF with Amitools; update the PYTHONPATH
and private Kickstart paths for your installation. No Kickstart is included.
Some native test scripts refer to an existing private headless FS-UAE build;
adapt paths to a local compatible test installation. Always use fresh test
directories. test_scores.py is a standalone host test. Previews can be
regenerated with stage-select/generate_previews.py and the supplied ROM.

scores.c validates/serializes the 96-byte save format. main.c performs DOS
I/O while OS services are restored, verifies file readback and flushes the
filesystem before taking the display back. Menus reuse existing bitmaps;
source NT/OAM and game RAM stay untouched until a stage is chosen or a
Continue is accepted. Stage overrides are explicit in replay receipts.

The pre-flush all-stage evidence and final regression evidence are labeled
separately in Verification.json. Original source game assets remain the
property of their respective owners. py65 license is included separately.
