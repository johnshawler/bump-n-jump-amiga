from pathlib import Path
import hashlib,json,shutil,struct,zipfile,re,zlib
from PIL import Image
R=Path(__file__).resolve().parent;N='BumpNJump-A1200-StageSelect';O=R.parent/'outputs'/N;S=R/'menus-source-package'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
final_hash=sha(R/'build/BumpNJump-A1200.hdf')
assert sha(O/(N+'.hdf'))==final_hash
assert (R/'build/release-readback-menus').read_bytes()==(R/'build/BumpNJump').read_bytes()
all_stages=read(R/'build/all-stages-verification.json');assert [r['stage']for r in all_stages]==list(range(1,17))
regression=read(R/'build/final-stage-regression.json');assert all(r['hdf_sha256']==final_hash for r in regression)
C=R/'controller-menus-final';B=R/'benchmark-menus-final';H=R/'scores-release-final'
for T in [C,B]:
 assert sha(T/'boot.hdf')==final_hash
 assert read(T/'results/native-verification.json')['logic']=='PASS'
 assert read(T/'results/clock-audio-verification.json')['per_tick_CPU_state_hash']=='PASS'
assert read(C/'raster-verification.json')['mismatches']==0
score_test=read(H/'score-save-verification.json')
for name,text in [('scores-flush-cold','PERSISTED 654321 123456 gen=2'),('scores-flush-fallback','PERSISTED 123456 0 gen=1')]:
 assert text in (R/name/'logs/fs-uae.log.txt').read_text(errors='replace')
log=(H/'logs/fs-uae.log.txt').read_text(errors='replace');assert 'CONTINUE_SCORE_ZERO' in log and 'CONTINUE_DECLINED' in log
assert 'BUMP_PROFILE_READY' in (R/'profile-smoke-menus-release/logs/fs-uae.log.txt').read_text(errors='replace')
exe=(R/'build/BumpNJump').read_bytes();w=struct.unpack('>'+str(len(exe)//4)+'I',exe);i=1
while w[i]:i+=1+w[i]
i+=1;ts,first,last=w[i:i+3];i+=3;sizes=[(n&0x3fffffff)*4 for n in w[i:i+last-first+1]]
clock=read(B/'results/clock-audio-verification.json')
report=dict(date='2026-10-20',hdf_sha256=final_hash,executable_sha256=sha(R/'build/BumpNJump'),target='Stock PAL A1200, 68EC020, AGA, 2 MB Chip RAM, no expansion RAM/JIT/accelerator; Kickstart 3.1',features=['16-stage selector before original stage initialization','Original cartridge scenery previews and font glyphs','Top 10 table with three initials and stage reached','Two alternating checksummed HDF saves; explicit filesystem flush before resuming','Continue restarts the current stage through original setup, with three lives and zero score','Original stage progression, game clock and event-audio requests preserved'],memory=dict(hunks_bytes=sizes,arena_bytes=383232,total_bytes=sum(sizes)+383232,excludes='OS, stack, loader metadata'),validation=dict(all_16_stages=all_stages,final_build_stage_regression=regression,stage_test_scope='All 16 stage logic/renderer/menu paths tested before the final save-handling changes; stages 1, 8, 16 rechecked on the exact final HDF. Those changes flush pending disk writes and clear keys consumed by the OS during saving; stage/gameplay paths are unchanged.',controller=read(C/'results/native-verification.json'),controller_CPU_audio=read(C/'results/clock-audio-verification.json'),actual_raster=read(C/'raster-verification.json'),jump=read(C/'jump-verification.json'),heavy_scene=clock,score_saves=score_test,score_format=read(R/'build/score-format-verification.json'),fresh_source_rebuild=read(R/'build/menus-source-rebuild-verification.json'),score_retention_cold_boot='PASS',corrupt_latest_save_falls_back='PASS',continue_same_stage_three_lives_zero_score='PASS',decline_continue_returns_to_title='PASS',renderer=read(R/'build/hardware-host-verification.json'),final_profile_cold_boot='PASS',executable_HDF_readback='PASS'),limits=['Physical A1200 and full campaign untested','Variable display rate; loading pauses remain','Paula synthesis is approximate','Score-save/Continue tests use two deliberately injected completed scores to exercise entry and persistence, with actual emulated controls and DOS filesystem writes'])
(O/'Verification.json').write_text(json.dumps(report,indent=2)+'\n')
# Native emulator pixels, cropped only to the game display.
for T in [C,H,R/'scores-flush-cold']:
 txt=(T/'logs/fs-uae.log.txt').read_text(errors='replace')
 for name,ww,hh,stride,pix,data in re.findall(r'BUMP_CAPTURE ([\w-]+) (\d+) (\d+) (\d+) (\d+) ([0-9a-f]+)',txt):
  im=Image.frombytes('RGBX',(int(ww),int(hh)),zlib.decompress(bytes.fromhex(data)),'raw','BGRX',int(stride)).convert('RGB');im.crop((138,52,650,532)).save(T/(name+'.png'))
for a,b,T in [('stage-select.png','Stage-Select.png',C),('persisted-scores.png','High-Scores.png',R/'scores-flush-cold'),('continue.png','Continue.png',H),('jump.png','Gameplay.png',C)]:shutil.copyfile(T/a,O/b)
S.mkdir(exist_ok=True)
for dirname in ['src','build','stage-select','evidence']:(S/dirname).mkdir(exist_ok=True)
for p in (R/'src').iterdir():
 if p.suffix in ['.c','.h','.s']:shutil.copyfile(p,S/'src'/p.name)
for name in ['build.py','package.py','generate.py','generate_asm.py','generate_sprites.py','reference.py','verify_native.py','verify_clock_audio.py','verify_raster.py','check_jump_replay.py','test_scores.py','test_hw_renderer.py','menu_test.py','controller_test.py','benchmark_hw.py','test_all_stages.py','profile_smoke.py','check_cpu.py','test_intrinsics.py']:
 shutil.copyfile(R/name,S/name)
for name in ['BumpNJump','sprite-atlas.bin','sprite-nonempty.bin','bg-atlas.bin','trace.json']:shutil.copyfile(R/'build'/name,S/'build'/name)
for name in ['generate_previews.py','extract_scores.py','previews.json']:shutil.copyfile(R/'stage-select'/name,S/'stage-select'/name)
for p in [O/'Verification.json',O/'Read-Me.txt',R/'build/score-format-verification.json',R/'build/all-stages-verification.json',R/'build/final-stage-regression.json']:shutil.copyfile(p,S/'evidence'/p.name)
for label,T in [('controller',C),('stress',B),('scores',H)]:
 D=S/'evidence'/label;D.mkdir(exist_ok=True)
 for p in (T/'results').iterdir():
  if p.is_file():shutil.copyfile(p,D/p.name)
 (D/'input-trace.txt').write_text('\n'.join(re.findall(r'BUMP [^\n]+',(T/'logs/fs-uae.log.txt').read_text(errors='replace')))+'\n')
shutil.copyfile(R/'source-package/py65-LICENSE.txt',S/'py65-LICENSE.txt')
(S/'requirements.txt').write_text('py65==1.2.0\nPillow\nnumpy\namitools\n')
(S/'README.txt').write_text('''Native Bump n Jump — stage select, scores and Continue sources

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
''')
for root,output in [(O,R.parent/'outputs'/(N+'.zip')),(S,R.parent/'outputs'/(N+'-Source.zip'))]:
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,9) as z:
  for p in sorted(root.rglob('*')):
   if p.is_file():z.write(p,Path(N if root==O else N+'-Source')/p.relative_to(root))
 with zipfile.ZipFile(output) as z:assert z.testzip() is None
manifest=[O/(N+'.hdf'),R.parent/'outputs'/(N+'.zip'),R.parent/'outputs'/(N+'-Source.zip')]
(R.parent/'outputs'/(N+'-SHA256SUMS.txt')).write_text(''.join(sha(p)+'  '+p.name+'\n' for p in manifest))
print('Published',N,final_hash,'hunks + arena',sum(sizes)+383232)
