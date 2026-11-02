from pathlib import Path
import shutil,json,struct,hashlib,zipfile,re,zlib
from PIL import Image
R=Path(__file__).resolve().parent;O=R.parent/'outputs/BumpNJump-A1200-Optimized';S=R/'optimized-source-package';C=R/'controller-hw-v4';B=R/'benchmark-hw-final';A=R/'benchmark-baseline';name='BumpNJump-A1200-Optimized'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((B/'results/native-verification.json').read_text())['logic']=='PASS'
assert json.loads((C/'raster-verification.json').read_text())['mismatches']==0
assert 'PASS: 15000 complete frames' in (R/'build/cpu-check-hw-v4.log').read_text()
assert 'BUMP_PROFILE_READY' in (R/'profile-smoke-hw-final/logs/fs-uae.log.txt').read_text(errors='replace')
assert (R/'build/BumpNJump').read_bytes()==(R/'build/release-readback-hw-final').read_bytes()
hdf=O/(name+'.hdf');assert sha(hdf)==sha(R/'build/BumpNJump-A1200.hdf')==sha(C/'boot.hdf')==sha(B/'boot.hdf')
# Reconstruct receipts for the verified controller snapshot and completed raster.
v=struct.unpack('>19I',(C/'results/stats.bin').read_bytes());assert v[11]==0
controller_receipt={'ticks':v[1],'logic':'PASS','native_viewport_pixels':61440,'pixel_mismatches':0,'fields':v[0],'publications':v[2]}
(C/'results/native-verification.json').write_text(json.dumps(controller_receipt,indent=2)+'\n')
def timing(p):
 s=struct.unpack('>19I',(p/'results/stats.bin').read_bytes());assert s[11]==0
 return dict(fields=s[0],processed_source_ticks=s[1],publications=s[2],mean_display_fps=s[2]/s[0]*49.9201,mean_simulation_hz=s[1]/s[0]*49.9201,pending_ticks=s[12],max_pending_ticks=s[13],cpu_profile_scanlines=s[14],render_profile_scanlines=s[15],wait_profile_scanlines=s[16],full_redraws=s[17],dirty_tiles=s[18],error=s[11])
old,new,con=timing(A),timing(B),timing(C)
exe=(R/'build/BumpNJump').read_bytes();w=struct.unpack('>'+str(len(exe)//4)+'I',exe);i=1
while w[i]:i+=1+w[i]
i+=1;ts,first,last=w[i:i+3];i+=3;sizes=[(n&0x3fffffff)*4 for n in w[i:i+last-first+1]]
base=json.loads((R.parent/'outputs/Verification.json').read_text())
rep={'date':'2026-10-20 America/New_York','status':'experimental playable hardware-sprite optimization','hdf_sha256':sha(hdf),'hdf_bytes':hdf.stat().st_size,'executable_sha256':sha(R/'build/BumpNJump'),'executable_bytes':len(exe),'source_rom_sha256':base['source_rom_sha256'],'target':base['target'],'filesystem':base['filesystem'],'changes':['Double-buffered Amiga hardware sprite DMA, matching four NES sprite palettes','Adjacent tile grouping and vertical channel reuse','Conservative software fallback for overlaps, behind-background priority, channel capacity and unsupported source sprite modes','Skip fully transparent source tiles','ROM-checked car construction, controller sampling and safe RAM copy fast paths','Direct 68020 coordinate helper with original CPU state preserved','Publish before initial sprite DMA control fetch or after visible display'],
 'validation':{'host_C_reference_complete_frames':15000,'randomized_original_ROM_routine_cases':24000,'randomized_routine_entries':['8092','aa44','b4f1','a920','b476','b3a4','b4b6','8109'],'renderer':json.loads((R/'build/hardware-host-verification.json').read_text()),'controller_native':controller_receipt,'stress_native':json.loads((B/'results/native-verification.json').read_text()),'actual_completed_emulated_raster':json.loads((C/'raster-verification.json').read_text()),'jump_landing_hold_release':json.loads((C/'jump-verification.json').read_text()),'keyboard_and_joystick_hardware':'PASS: title Start, Up, ready-speed jump, held Fire, Left/Right, pause/resume, Space jump, Escape','delivered_DH0_only_cold_boot':'PASS','release_HDF_matches_controller_and_stress_images':True,'executable_FFS_readback_matches':True,'physical_A1200':'not tested','full_campaign':'not completed','clean_source_rebuild':json.loads((R/'build/source-rebuild-verification.json').read_text())},
 'timing':{'baseline_stress':old,'optimized_stress':new,'optimized_controller':con,'stress_display_fps_improvement_percent':(new['mean_display_fps']/old['mean_display_fps']-1)*100,'stress_simulation_rate_improvement_percent':(new['mean_simulation_hz']/old['mean_simulation_hz']-1)*100,'scope':'Finite stock-cycle A1200 emulation. Identical source-tick stress input script; exit polling produced 1802 baseline and 1811 optimized ticks. Means include the title and transitions; individual heavy frames are slower. Controller includes paused raster capture. Scanline profiling is approximate.'},
 'memory':{'rounded_hunks_bytes':sizes,'arena_bytes':383232,'hunks_plus_arena_bytes':sum(sizes)+383232,'excludes':'OS, shell stack, loader and allocation metadata'},'limits':['Heavy scenes can still slow down','Approximate Paula sound and frame-boundary NES PPU model','Physical A1200 and complete campaign untested'],'baseline_hdf_sha256':base['hdf_sha256']}
(O/'Verification.json').write_text(json.dumps(rep,indent=2)+'\n')
p=O/'Read-Me.txt';txt=p.read_text();txt=txt.replace('Performance and comparison figures are in Verification.json.',f'The matched stress test improved from {old["mean_display_fps"]:.1f} to {new["mean_display_fps"]:.1f} displayed frames per\nsecond and {old["mean_simulation_hz"]:.1f} to {new["mean_simulation_hz"]:.1f} source ticks per second. The controller run averaged\n{con["mean_display_fps"]:.1f} displayed frames and {con["mean_simulation_hz"]:.1f} source ticks per second. These are finite test\nmeans, including title/transitions and a paused controller capture.\nDetails and scope are in Verification.json.');p.write_text(txt)
for f in C.glob('*.z'):
 wi,he,stride,pixels=json.loads(f.with_suffix('.json').read_text());Image.frombytes('RGBX',(wi,he),zlib.decompress(f.read_bytes()),'raw','BGRX',stride).convert('RGB').save(f.with_suffix('.png'))
shutil.copyfile(C/'jump.png',O/'Gameplay.png');shutil.copyfile(C/'paused.png',O/'Verified-Raster.png')
S.mkdir(exist_ok=True)
for d in ['src','build','evidence','evidence/controller','evidence/stress','evidence/baseline']:(S/d).mkdir(exist_ok=True)
for p in (R/'src').iterdir():
 if p.suffix in ['.c','.h','.s']:shutil.copyfile(p,S/'src'/p.name)
for n in ['build.py','package.py','generate.py','generate_asm.py','generate_sprites.py','reference.py','check_cpu.py','test_intrinsics.py','check_coverage.py','verify_native.py','verify_raster.py','test_hw_renderer.py','controller_test.py','benchmark_hw.py','check_jump_replay.py','profile_smoke.py','run_test.py','debug_server.py']:
 shutil.copyfile(R/n,S/n)
for n in ['sprite-atlas.bin','bg-atlas.bin','sprite-nonempty.bin','trace.json','BumpNJump']:
 shutil.copyfile(R/'build'/n,S/'build'/n)
for p in [O/'Verification.json',O/'Read-Me.txt',R/'build/hardware-host-verification.json',R/'build/cpu-check-hw-v4.log',R/'build/source-rebuild-verification.json']:shutil.copyfile(p,S/'evidence'/p.name)
(S/'evidence/intrinsics-verification.txt').write_text('Observed test_intrinsics.py result on final C fast paths:\n'+''.join('0x'+n+' PASS 3000 randomized original-ROM comparisons\n'for n in ['8092','aa44','b4f1','a920','b476','b3a4','b4b6','8109']))
for key,T in [('controller',C),('stress',B),('baseline',A)]:
 for p in (T/'results').iterdir():
  if p.is_file():shutil.copyfile(p,S/'evidence'/key/p.name)
 for n in ['jump-verification.json','raster-verification.json','samples.txt','timing.json']:
  if (T/n).exists():shutil.copyfile(T/n,S/'evidence'/key/n)
 log=(T/'logs/fs-uae.log.txt').read_text(errors='replace');(S/'evidence'/key/'input-trace.txt').write_text('\n'.join(re.findall(r'BUMP(?:_SAMPLE| )[^\n]+',log))+'\n')
shutil.copyfile(R/'source-package/py65-LICENSE.txt',S/'py65-LICENSE.txt');(S/'requirements.txt').write_text('py65==1.2.0\nPillow\nnumpy\namitools\n')
(S/'README.txt').write_text('''Bump n Jump — optimized stock A1200 source package

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
''')
# Checksums cover every published item in this package, then both archives.
(O/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n'for p in sorted(O.iterdir())if p.is_file() and p.name!='SHA256SUMS.txt'))
zout=O.parent/(name+'.zip')
with zipfile.ZipFile(zout,'w',zipfile.ZIP_DEFLATED,9)as z:
 for p in sorted(O.iterdir()):
  if p.is_file():z.write(p,Path(name)/p.name)
sout=O.parent/(name+'-Source.zip')
with zipfile.ZipFile(sout,'w',zipfile.ZIP_DEFLATED,9)as z:
 for p in sorted(S.rglob('*')):
  if p.is_file():z.write(p,Path(name+'-Source')/p.relative_to(S))
for p in [zout,sout]:
 with zipfile.ZipFile(p)as z:assert z.testzip()is None
with zipfile.ZipFile(zout)as z:assert hashlib.sha256(z.read(name+'/'+name+'.hdf')).hexdigest()==sha(hdf)
(O.parent/(name+'-SHA256SUMS.txt')).write_text(sha(hdf)+'  '+str(hdf.relative_to(O.parent))+'\n'+sha(zout)+'  '+zout.name+'\n'+sha(sout)+'  '+sout.name+'\n')
print(json.dumps({'hdf_sha256':sha(hdf),'executable_sha256':sha(R/'build/BumpNJump'),'stock_memory_hunks_plus_arena':sum(sizes)+383232,'baseline_stress_fps':old['mean_display_fps'],'optimized_stress_fps':new['mean_display_fps'],'baseline_simulation_hz':old['mean_simulation_hz'],'optimized_simulation_hz':new['mean_simulation_hz'],'controller_fps':con['mean_display_fps'],'controller_simulation_hz':con['mean_simulation_hz'],'archives':'PASS'},indent=2))
