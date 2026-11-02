from pathlib import Path
import os,subprocess,time,re,shutil,sys,struct,json
R=Path(__file__).resolve().parent;T=R/sys.argv[1];T.mkdir()
H=R/(sys.argv[2] if len(sys.argv)>2 else 'build/BumpNJump-A1200.hdf');ELF=R/(sys.argv[3] if len(sys.argv)>3 else 'build/game.elf')
E=Path('/path/to/local-user/Documents/Codex/2026-10-12/i-w/outputs/bad-news-baseball-amiga/work/headless-emulator-source/fs-uae-3.2.35')
EXE=Path('/path/to/local-user/Documents/Codex/2026-10-12/i-w/outputs/bad-news-baseball-amiga/releases/runner-two-player-2026-10-15/headless-input-test-fs-uae')
objdump='/path/to/local-user/.vscode/extensions/bartmanabyss.amiga-debug-1.8.2/bin/darwin/opt/bin/m68k-amiga-elf-objdump'
sy={}
for line in subprocess.check_output([objdump,'-t',str(ELF)],text=True).splitlines():
 v=line.split()
 if len(v)>=6:
  try:sy[v[-1]]=int(v[0],16)
  except ValueError:pass
for p in (R/'test').iterdir():
 if p.is_dir():(T/p.name).mkdir()
theme=T/'theme';theme.mkdir()
lua=r'''
local active=false;local delta=nil;local field=0;local sample=0
local function rd(a)return uae_read_u16(a)or 0 end
local function long(a)return rd(a)*65536+rd(a+2)end
local function wl(a,v)uae_write_u16(a,math.floor(v/65536));uae_write_u16(a+2,v%65536)end
function on_uae_vsync()
 field=field+1
 if not active then
  local irq=long(0x6c)
  if irq<0x200000 and rd(irq)==0x48e7 and rd(irq+22)==0x52b9 then
   delta=long(irq+24)-FIELD_ELF;active=true;wl(CONTROL_ELF+delta,1)
  end
 elseif long(CONTROL_ELF+delta)==1 then
  local n=long(TICKS_ELF+delta)
  if n>=sample then
   uae_log('BUMP_SAMPLE '..n..' '..long(FIELD_ELF+delta)..' '..long(PUBS_ELF+delta)..' '..long(CPU_ELF+delta)..' '..long(RENDER_ELF+delta)..' '..long(IDLE_ELF+delta)..'\n');sample=sample+300
  end
  if n>=1802 then wl(CONTROL_ELF+delta,57005)end
 end
end
'''
for k,n in {'FIELD_ELF':'fields','CONTROL_ELF':'test_control','TICKS_ELF':'source_ticks','PUBS_ELF':'publications','CPU_ELF':'cpu_lines','RENDER_ELF':'render_lines','IDLE_ELF':'idle_lines'}.items():lua=re.sub(r'\b'+k+r'\b',str(sy[n]),lua)
(theme/'theme.lua').write_text(lua);shutil.copyfile(H,T/'boot.hdf')
s=(R/'test/test.fs-uae').read_text().replace(str(R/'test'),str(T)).replace(str(R/'build/BumpNJump-A1200.hdf'),str(T/'boot.hdf'))
s+='\nvideo_driver = sdl-software\nvideo_sync = off\naudio_driver = dummy\nbenchmark = 0\nwarp_mode = 0\nlog_flush = 1\ntheme = '+str(theme)+'\n';(T/'test.fs-uae').write_text(s)
env=dict(os.environ);env.update(SDL_VIDEODRIVER='dummy',SDL_VIDEO_DRIVER='dummy',SDL_AUDIODRIVER='dummy',XDG_DATA_HOME=str(T/'userdata'),XDG_CONFIG_HOME=str(T/'userconfig'),XDG_CACHE_HOME=str(T/'usercache'))
with (T/'console.txt').open('wb')as f:
 p=subprocess.Popen([str(EXE),str(T/'test.fs-uae')],cwd=E,env=env,stdout=f,stderr=subprocess.STDOUT);print('Benchmark',T.name,'PID',p.pid,flush=True)
 try:
  start=time.monotonic()
  while time.monotonic()-start<240:
   receipt=T/'results/stats.bin'
   if receipt.exists() and receipt.stat().st_size==76:time.sleep(.3);break
   if p.poll()is not None:raise RuntimeError('emulator exited '+str(p.returncode))
   time.sleep(.5)
  else:raise TimeoutError('benchmark')
 finally:
  p.terminate()
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
s=struct.unpack('>19I',(T/'results/stats.bin').read_bytes());out={'ticks':s[1],'fields':s[0],'pictures':s[2],'fps':s[2]/s[0]*49.9201,'simulation_hz':s[1]/s[0]*49.9201,'cpu_lines':s[14],'render_lines':s[15],'idle_lines':s[16],'dirty_tiles':s[18],'error':s[11]}
print(json.dumps(out),flush=True);(T/'timing.json').write_text(json.dumps(out,indent=2))
txt=(T/'logs/fs-uae.log.txt').read_text(errors='replace');(T/'samples.txt').write_text('\n'.join(re.findall(r'BUMP_SAMPLE [^\n]+',txt))+'\n')
