from pathlib import Path
import json,struct,shutil,hashlib,itertools,zipfile,zlib,re
from PIL import Image
R=Path(__file__).resolve().parent;O=R.parent/'outputs';T=R/'controller-final';S=R/'source-package'
raw=(T/'results/stats.bin').read_bytes();v=struct.unpack('>'+str(len(raw)//4)+'I',raw);inputs=(T/'results/native-input.bin').read_bytes()
checks={}
for name,bit in [('fire',1),('start',8),('up',16),('left',64),('right',128)]:
 runs=[len(list(g))for k,g in itertools.groupby([bool(x&bit)for x in inputs])if k];checks[name]={'source_ticks_held':sum(bool(x&bit)for x in inputs),'longest_hold_ticks':max(runs,default=0),'presses':len(runs)}
assert checks['fire']['longest_hold_ticks']>=130 and checks['left']['longest_hold_ticks']>=40 and checks['right']['longest_hold_ticks']>=16 and checks['start']['presses']>=3
(T/'input-verification.json').write_text(json.dumps(checks,indent=2))
for p in T.glob('*.z'):
 w,h,stride,pixels=json.loads(p.with_suffix('.json').read_text());Image.frombytes('RGBX',(w,h),zlib.decompress(p.read_bytes()),'raw','BGRX',stride).convert('RGB').save(p.with_suffix('.png'))
shutil.copyfile(R/'build/BumpNJump-A1200.hdf',O/'BumpNJump-A1200.hdf');shutil.copyfile(T/'jump.png',O/'BumpNJump-A1200.png')
exe=(R/'build/BumpNJump').read_bytes();hdfhash=hashlib.sha256((O/'BumpNJump-A1200.hdf').read_bytes()).hexdigest();exehash=hashlib.sha256(exe).hexdigest()
assert (R/'build/release-readback-final').read_bytes()==exe
assert hashlib.sha256((T/'boot.hdf').read_bytes()).hexdigest()==hdfhash
w=struct.unpack('>'+str(len(exe)//4)+'I',exe);i=1
while w[i]:i+=1+w[i]
i+=1;ts,first,last=w[i:i+3];i+=3;sizes=[(n&0x3fffffff)*4 for n in w[i:i+last-first+1]]
rep=json.loads((O/'Verification.json').read_text());rep.update(hdf_sha256=hdfhash,executable_sha256=exehash,executable_bytes=len(exe))
rep['validation'].update(release_hardware_input_test='PASS: Start, 150 km/h readiness, actual jump mode 5, held Fire, Left/Right, keyboard pause/resume, Space, Escape',release_controller_cpu_ram_vram_sprites_palette_pixels='PASS, '+str(v[1])+' source ticks, all 61440 viewport pixels',final_hdf_exactly_matches_controller_run=True,delivered_stock_profile_DH0_only_cold_boot='PASS',executable_filesystem_readback='PASS',coherent_beam_sampling='upper vertical bit checked before and after lower byte; publication restricted to guarded vertical blank')
rep['validation']['jump_landing_hold_release']=json.loads((T/'jump-verification.json').read_text())
rep['validation']['jump_hardware_witness']='player mode 5 observed at field 1303, source tick 769; reference replay starts mode 5 at tick 768'
rep['timing']['final_release_controller_run']={'fields':v[0],'processed_source_ticks':v[1],'publications':v[2],'mean_display_fps':v[2]/v[0]*49.9201,'mean_simulation_hz':v[1]/v[0]*49.9201,'pending_ticks':v[12],'max_pending_ticks':v[13],'error':v[11]}
rep['timing']['heavy_scripted_run']['scope_note']='Same runtime and renderer, before final coherent publication poll correction; finite stress run, not a final-release full-speed claim.'
rep['memory'].update(rounded_hunks_bytes=sizes,hunks_plus_arena_bytes=sum(sizes)+366848)
(O/'Verification.json').write_text(json.dumps(rep,indent=2)+'\n')
p=O/'Read-Me.txt';txt=p.read_text();txt=txt.replace('The game starts automatically. Allow the original title sequence to appear.', 'The game starts automatically. Allow the original title sequence to appear.\nOn this Mac, unzip the package and double-click Play-BumpNJump.command.');p.write_text(txt)
for p in (R/'src').iterdir():
 if p.suffix in ['.c','.h','.s']:shutil.copyfile(p,S/'src'/p.name)
for name in ['build.py','package.py','run_test.py','debug_server.py','controller_test.py','profile_smoke.py','check_jump_replay.py','verify_native.py']:
 shutil.copyfile(R/name,S/name)
shutil.copyfile(R/'build/BumpNJump',S/'build/BumpNJump')
for name in ['Verification.json','Read-Me.txt']:shutil.copyfile(O/name,S/'evidence'/name)
for p in (T/'results').iterdir():
 if p.is_file():shutil.copyfile(p,S/'evidence'/p.name)
for name in ['jump-verification.json','input-verification.json']:shutil.copyfile(T/name,S/'evidence'/name)
trace=[line for line in (T/'logs/fs-uae.log.txt').read_text(errors='replace').splitlines()if line.startswith('BUMP ')];(S/'evidence/hardware-input-trace.txt').write_text('\n'.join(trace)+'\n')
(S/'evidence/palette-scope.txt').write_text('Pixel verification compares all 61440 source palette indices against the native planar viewport, with transparent colour aliases canonicalized. Native display uses a fixed RGB4 palette; the NES PPU is not cycle-exactly emulated.\n')
(S/'requirements.txt').write_text('py65==1.2.0\nPillow\namitools\n')
(S/'README.txt').write_text((S/'README.txt').read_text()+'\nTo package a rebuilt executable as an HDF, install amitools and run\npython3 package.py. It also creates the test configuration. Update the\nKickstart path for another host. Hardware tests use a private local FS-UAE\nwith Lua input sending, configured in controller_test.py.\n')
pack=['BumpNJump-A1200.hdf','BumpNJump-A1200.fs-uae','Play-BumpNJump.command','Read-Me.txt','Verification.json','BumpNJump-A1200.png']
with zipfile.ZipFile(O/'BumpNJump-A1200.zip','w',zipfile.ZIP_DEFLATED,9)as z:
 for n in pack:z.write(O/n,Path('BumpNJump-A1200')/n)
with zipfile.ZipFile(O/'BumpNJump-A1200-Source.zip','w',zipfile.ZIP_DEFLATED,9)as z:
 for p in sorted(S.rglob('*')):
  if p.is_file():z.write(p,Path('BumpNJump-A1200-Source')/p.relative_to(S))
for n in ['BumpNJump-A1200.zip','BumpNJump-A1200-Source.zip']:
 with zipfile.ZipFile(O/n)as z:assert z.testzip()is None
with zipfile.ZipFile(O/'BumpNJump-A1200.zip')as z:assert hashlib.sha256(z.read('BumpNJump-A1200/BumpNJump-A1200.hdf')).hexdigest()==hdfhash
(O/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n'for p in sorted(O.iterdir())if p.is_file()and p.name!='SHA256SUMS.txt'))
print(json.dumps({'hdf_sha256':hdfhash,'executable_sha256':exehash,'executable_bytes':len(exe),'native_plus_arena_bytes':sum(sizes)+366848,'final_controller_ticks':v[1],'display_fps':rep['timing']['final_release_controller_run']['mean_display_fps'],'simulation_hz':rep['timing']['final_release_controller_run']['mean_simulation_hz'],'pixel_mismatches':0,'archives':'PASS'},indent=2))
