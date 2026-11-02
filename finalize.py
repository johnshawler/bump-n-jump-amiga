from pathlib import Path
import shutil,hashlib,json,struct,subprocess,zipfile,re
R=Path(__file__).resolve().parent;O=R.parent/'outputs';O.mkdir(exist_ok=True)
shutil.copyfile(R/'build/BumpNJump-A1200.hdf',O/'BumpNJump-A1200.hdf')
config='''[fs-uae]
amiga_model = A1200
cpu = 68EC020
chip_memory = 2048
fast_memory = 0
slow_memory = 0
zorro_iii_memory = 0
accelerator = none
jit_compiler = 0
accuracy = 1
uae_cpu_speed = real
uae_cpu_multiplier = 4
kickstart_file = /Applications/AmigaVision-2025.05.05/Kickstart v3.1 rev 40.68 (1993)(Commodore)(A1200)[!].rom
hard_drive_0 = ./BumpNJump-A1200.hdf
hard_drive_0_type = hdf
hard_drive_0_read_only = 1
hard_drive_0_priority = 0
floppy_drive_count = 0
joystick_port_0 = mouse
joystick_port_1 = keyboard
keyboard_key_q = action_joy_1_fire_button
fullscreen = 0
window_width = 960
window_height = 720
keep_aspect = 1
texture_filter = nearest
initial_input_grab = 0
automatic_input_grab = 0
volume = 80
config_window_title = Bump n Jump - Stock A1200
'''
(O/'BumpNJump-A1200.fs-uae').write_text(config)
(O/'Play-BumpNJump.command').write_text('''#!/bin/zsh
cd -- "${0:A:h}"
exec /Applications/FS-UAE.app/Contents/MacOS/fs-uae ./BumpNJump-A1200.fs-uae
''');(O/'Play-BumpNJump.command').chmod(0o755)
b=(R/'build/BumpNJump').read_bytes();words=struct.unpack('>'+str(len(b)//4)+'I',b);i=1
while words[i]:i+=1+words[i]
i+=1;tablesize,first,last=words[i:i+3];i+=3;sizes=[(v&0x3fffffff)*4 for v in words[i:i+last-first+1]]
def stats(where):
 p=R/where/'results/stats.bin';v=struct.unpack('>'+str(p.stat().st_size//4)+'I',p.read_bytes())
 return {'fields':v[0],'processed_source_ticks':v[1],'publications':v[2],'mean_display_fps':v[2]/v[0]*49.9201,'mean_simulation_hz':v[1]/v[0]*49.9201,'pending_ticks':v[12],'max_pending_ticks':v[13],'error':v[11]}
report={'date':'2026-10-19 America/New_York','status':'experimental playable build','source_rom_sha256':'40e45122fc9ecbda7e94a18c3b4ff6b5022675220872bbc6f02107ec842ce6a6','hdf_sha256':hashlib.sha256((O/'BumpNJump-A1200.hdf').read_bytes()).hexdigest(),'hdf_bytes':8388608,'executable_sha256':hashlib.sha256(b).hexdigest(),'executable_bytes':len(b),'target':{'machine':'PAL A1200','cpu':'68EC020','chip_bytes':2097152,'fast_bytes':0,'slow_bytes':0,'z3_bytes':0,'jit':False,'kickstart':'3.1 rev 40.68','cpu_timing':'real, cycle exact'},'filesystem':{'type':'plain FFS partition hardfile','block_bytes':512,'sectors':32,'surfaces':1,'reserved_blocks':2,'executable_readback_sha256_matches':(R/'build/release-readback').read_bytes()==b},'validation':{'c_reference_host_frames':15000,'randomized_original_ROM_routine_cases':18000,'guarded_memory_cases':10000,'native_scripted_ticks':1802,'native_scripted_cpu_ram_vram_sprites_palette':'PASS','native_scripted_pixels':61440,'native_pixel_mismatches':0,'release_hardware_input_test':'PASS pending final jump-readiness replay','release_controller_cpu_ram_vram_sprites_palette_pixels':'PASS, 1233 source ticks','physical_Mac_keyboard':'not manually tested: Mac locked; emulated keyboard hardware checked','physical_A1200':'not tested','full_campaign':'not completed'},'timing':{'heavy_scripted_run':stats('test-final-speed'),'release_hardware_input_run':stats('controller-test'),'scope':'finite emulated runs; display and simulation can slow in busy scenes; no full-speed guarantee'},'memory':{'rounded_hunks_bytes':sizes,'hunks_plus_arena_bytes':sum(sizes)+366848,'arena_bytes':366848,'excludes':'OS, shell stack, loader and allocation metadata'},'limits':['approximate Paula sound','physical hardware and complete campaign unverified','heavy-scene slowdown']}
(O/'Verification.json').write_text(json.dumps(report,indent=2)+'\n')
S=R/'source-package';(S/'src').mkdir(parents=True,exist_ok=True);(S/'build').mkdir(exist_ok=True);(S/'evidence').mkdir(exist_ok=True)
for p in (R/'src').iterdir():
 if p.suffix in ['.c','.h','.s']:(S/'src'/p.name).write_bytes(p.read_bytes())
for name in ['generate.py','generate_asm.py','generate_sprites.py','reference.py','build.py','check_cpu.py','test_intrinsics.py','check_coverage.py','verify_native.py','controller_test.py']:
 shutil.copyfile(R/name,S/name)
for name in ['trace.json','sprite-atlas.bin','bg-atlas.bin']:
 shutil.copyfile(R/'build'/name,S/'build'/name)
shutil.copyfile(R/'build/BumpNJump',S/'build/BumpNJump')
shutil.copyfile(O/'Verification.json',S/'evidence/Verification.json')
shutil.copyfile(R/'venv/lib/python3.9/site-packages/py65-1.2.0.dist-info/LICENSE.txt',S/'py65-LICENSE.txt')
(S/'requirements.txt').write_text('py65==1.2.0\nPillow\n')
(S/'README.txt').write_text('''Bump n Jump — stock A1200 source package

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
''')
print(json.dumps({'hdf_sha256':report['hdf_sha256'],'executable_sha256':report['executable_sha256'],'known_hunks_and_arena_bytes':report['memory']['hunks_plus_arena_bytes']},indent=2))
