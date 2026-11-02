from pathlib import Path
import hashlib,json,shutil,struct,zipfile,re,zlib
from PIL import Image
R=Path(__file__).resolve().parent;N='BumpNJump-A1200-60Hz';O=R.parent/'outputs'/N;S=R/'clock-source-package';C=R/'controller-clock-final';B=R/'benchmark-clock-final';L=R/'benchmark-clock-long-final'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
for t in [C,B,L]:
 assert read(t/'results/native-verification.json')['logic']=='PASS'
 a=read(t/'results/clock-audio-verification.json');assert a['per_tick_CPU_state_hash']=='PASS' and a['audio_published_once_per_source_tick']
assert read(C/'raster-verification.json')['mismatches']==0
assert 'BUMP_PROFILE_READY' in (R/'profile-smoke-clock-final/logs/fs-uae.log.txt').read_text(errors='replace')
assert (R/'build/release-readback-clock-final').read_bytes()==(R/'build/BumpNJump').read_bytes()
hdf=O/(N+'.hdf');assert sha(hdf)==sha(R/'build/BumpNJump-A1200.hdf')==sha(C/'boot.hdf')==sha(B/'boot.hdf')==sha(L/'boot.hdf')
def timing(t):
 s=struct.unpack('>19I',(t/'results/stats.bin').read_bytes());assert not s[11]
 clock=struct.unpack('>4I',(t/'results/clock-stats.bin').read_bytes())
 return {'ticks':s[1],'emulated_run_scanlines':clock[0],'mean_game_updates_hz':s[1]*312*49.9201/clock[0],'publications':s[2],'mean_display_fps':s[2]*312*49.9201/clock[0],'pending_at_exit':s[12],'maximum_pending_including_loading':s[13],'cpu_profile_scanlines':s[14],'render_profile_scanlines':s[15],'idle_profile_scanlines':s[16],'full_cache_invalidations':s[17],'physical_tiles_rebuilt':s[18],'error':s[11]}
exe=(R/'build/BumpNJump').read_bytes();w=struct.unpack('>'+str(len(exe)//4)+'I',exe);i=1
while w[i]:i+=1+w[i]
i+=1;ts,first,last=w[i:i+3];i+=3;sizes=[(n&0x3fffffff)*4 for n in w[i:i+last-first+1]]
prior=read(R.parent/'outputs/BumpNJump-A1200-Optimized/Verification.json')
validation={'controller_native':read(C/'results/native-verification.json'),'stress_native':read(B/'results/native-verification.json'),'long_restart_run_native':read(L/'results/native-verification.json'),'stress_per_tick_CPU_audio':read(B/'results/clock-audio-verification.json'),'long_per_tick_CPU_audio':read(L/'results/clock-audio-verification.json'),'controller_per_tick_CPU_audio':read(C/'results/clock-audio-verification.json'),'actual_completed_raster':read(C/'raster-verification.json'),'actual_Paula_output_capture':read(C/'audio-capture-verification.json'),'jump_landing_hold_release':read(C/'jump-verification.json'),'snapshot_visible_cache_renderer':read(R/'build/hardware-host-verification.json'),'inherited_C_logic_checks':{'frames':15000,'randomized_ROM_cases':24000,'scope':'Unchanged C game semantics, checked in the preceding build. This build additionally checks native CPU state hashes on each recorded tick and complete final source state.'},'stock_DH0_only_cold_boot':'PASS','HDF_executable_readback':'PASS','exact_HDF_used_for_all_final_native_runs':True,'physical_A1200':'not tested','complete_campaign':'not completed'}
if (R/'build/clock-source-rebuild-verification.json').exists():validation['clean_source_rebuild']=read(R/'build/clock-source-rebuild-verification.json')
report={'date':'2026-10-20 America/New_York','status':'experimental playable port with prioritized original game clock','source_ROM_sha256':prior['source_rom_sha256'],'hdf_sha256':sha(hdf),'hdf_bytes':hdf.stat().st_size,'executable_sha256':sha(R/'build/BumpNJump'),'executable_bytes':len(exe),'target':prior['target'],'filesystem':prior['filesystem'],'changes':['Scanline-based original approximately 60.1-Hz game clock','Game and audio service between bounded rendering work pieces','Immutable background, OAM, palette and display-register snapshots','Visible physical tile cache with independent wrap-copy validity','Vertical-blank IRQ publishes a completed copper list','Native return and indirect dispatch retain the jump table in A6 and avoid redundant PC storage','Paula period/volume and envelopes published on every source tick','Every due source tick retained; no object removal or gameplay-rule changes'],
 'timing':{'same_script_stress':timing(B),'long_restart_run':timing(L),'controller_run':timing(C),'crowded_window_900_1500':read(B/'results/clock-audio-verification.json')['timing'][2],'all_scene12_windows_first_4096_long_run':read(L/'results/active-clock-windows.json'),'previous_optimized_same_script':prior['timing']['optimized_stress'],'scope':'Finite stock-cycle emulation. Crowded-window one-second rates use 60 consecutive tick-start intervals. Whole-run rates include menus and loading. The longer test restarts through title state. Loading pauses can be followed by catch-up above 60 Hz; loading is not a steady-clock claim. Visible frame rate can be lower than in the preceding build because logic/audio receive priority. Profiling scanline counts are approximate.'},
 'validation':validation,'memory':{'rounded_hunks_bytes':sizes,'arena_bytes':383232,'hunks_plus_arena_bytes':sum(sizes)+383232,'excludes':'OS, shell stack, loader metadata'},'limits':['Level-loading pauses remain, including approximately 0.38-second source work bursts in these tests','Visible display frame rate varies and can be low in crowded scenes','Approximate Paula synthesis and frame-boundary PPU handling','Physical A1200 and full campaign untested'],'previous_optimized_HDF_sha256':prior['hdf_sha256']}
(O/'Verification.json').write_text(json.dumps(report,indent=2)+'\n')
for p in C.glob('*.z'):
 wi,he,stride,pixels=read(p.with_suffix('.json'));Image.frombytes('RGBX',(wi,he),zlib.decompress(p.read_bytes()),'raw','BGRX',stride).convert('RGB').save(p.with_suffix('.png'))
for a,b in [('jump.png','Gameplay.png'),('paused.png','Verified-Raster.png'),('Game-Event-Audio.wav','Game-Event-Audio.wav')]:shutil.copyfile(C/a,O/b)
for d in ['','src','build','evidence','evidence/controller','evidence/stress','evidence/long']:(S/d).mkdir(exist_ok=True)
for p in (R/'src').iterdir():
 if p.suffix in ['.c','.h','.s']:shutil.copyfile(p,S/'src'/p.name)
for n in ['build.py','package.py','generate.py','generate_asm.py','generate_sprites.py','reference.py','check_cpu.py','test_intrinsics.py','check_coverage.py','verify_native.py','verify_raster.py','verify_clock_audio.py','test_hw_renderer.py','controller_test.py','benchmark_hw.py','check_jump_replay.py','profile_smoke.py','analyze_game_audio.py','build_audio_probe.py','run_test.py','debug_server.py']:shutil.copyfile(R/n,S/n)
for n in ['sprite-atlas.bin','bg-atlas.bin','sprite-nonempty.bin','trace.json','BumpNJump']:shutil.copyfile(R/'build'/n,S/'build'/n)
for p in [O/'Verification.json',O/'Read-Me.txt',R/'build/hardware-host-verification.json']:shutil.copyfile(p,S/'evidence'/p.name)
if (R/'build/clock-source-rebuild-verification.json').exists():shutil.copyfile(R/'build/clock-source-rebuild-verification.json',S/'evidence/source-rebuild-verification.json')
for label,t in [('controller',C),('stress',B),('long',L)]:
 for p in (t/'results').iterdir():
  if p.is_file():shutil.copyfile(p,S/'evidence'/label/p.name)
 for n in ['jump-verification.json','raster-verification.json','audio-capture-verification.json','samples.txt','timing.json']:
  if(t/n).exists():shutil.copyfile(t/n,S/'evidence'/label/n)
 log=(t/'logs/fs-uae.log.txt').read_text(errors='replace');(S/'evidence'/label/'input-trace.txt').write_text('\n'.join(re.findall(r'BUMP(?:_SAMPLE| )[^\n]+',log))+'\n')
shutil.copyfile(R/'source-package/py65-LICENSE.txt',S/'py65-LICENSE.txt');(S/'requirements.txt').write_text('py65==1.2.0\nPillow\nnumpy\namitools\n')
(S/'README.txt').write_text('''Bump n Jump — stock A1200 original-game-clock source

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
''')
(O/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n'for p in sorted(O.iterdir())if p.is_file()and p.name!='SHA256SUMS.txt'))
for path,folder,prefix in [(O.parent/(N+'.zip'),O,N),(O.parent/(N+'-Source.zip'),S,N+'-Source')]:
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,9)as z:
  for p in sorted(folder.rglob('*')):
   if p.is_file():z.write(p,Path(prefix)/p.relative_to(folder))
 with zipfile.ZipFile(path)as z:assert z.testzip()is None
(O.parent/(N+'-SHA256SUMS.txt')).write_text(''.join(sha(p)+'  '+str(p.relative_to(O.parent))+'\n'for p in [hdf,O.parent/(N+'.zip'),O.parent/(N+'-Source.zip')]))
print(json.dumps({'hdf_sha256':sha(hdf),'stock_hunks_plus_arena_bytes':sum(sizes)+383232,'stress':timing(B),'long':timing(L),'crowded_clock':report['timing']['crowded_window_900_1500'],'archives':'PASS'},indent=2))
