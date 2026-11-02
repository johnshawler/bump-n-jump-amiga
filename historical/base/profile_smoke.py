from pathlib import Path
import os,re,subprocess,time
R=Path(__file__).resolve().parent;O=R.parent/'outputs';T=R/'profile-smoke-final';T.mkdir(exist_ok=True)
for d in ['base','logs','state','cache','userdata','userconfig','usercache','theme']:(T/d).mkdir(exist_ok=True)
objdump='/path/to/local-user/.vscode/extensions/bartmanabyss.amiga-debug-1.8.2/bin/darwin/opt/bin/m68k-amiga-elf-objdump';sy={}
for line in subprocess.check_output([objdump,'-t',str(R/'build/game.elf')],text=True).splitlines():
 v=line.split()
 if len(v)>=6:
  try:sy[v[-1]]=int(v[0],16)
  except ValueError:pass
lua='''local once=false
local function rd(a)return uae_read_u16(a)or 0 end
local function long(a)return rd(a)*65536+rd(a+2)end
function on_uae_vsync()
 local irq=long(0x6c)
 if irq<0x200000 and rd(irq)==0x48e7 and rd(irq+22)==0x52b9 then
  local delta=long(irq+24)-FIELD;local mode=uae_read_u8(RAM+delta+20)or 0
  if mode==2 and not once then once=true;uae_log('BUMP_PROFILE_READY\\n')end
 end
end
'''.replace('FIELD',str(sy['fields'])).replace('RAM',str(sy['ram']));(T/'theme/theme.lua').write_text(lua)
exe='/path/to/local-user/Documents/Codex/2026-10-12/i-w/outputs/bad-news-baseball-amiga/releases/runner-two-player-2026-10-15/headless-input-test-fs-uae'
E=Path('/path/to/local-user/Documents/Codex/2026-10-12/i-w/outputs/bad-news-baseball-amiga/work/headless-emulator-source/fs-uae-3.2.35')
args=[exe,str(O/'BumpNJump-A1200.fs-uae'),'--video_driver=sdl-software','--video_sync=off','--audio_driver=dummy','--benchmark=0','--warp_mode=0','--log_flush=1','--theme='+str(T/'theme')]
for key,name in [('base_dir','base'),('logs_dir','logs'),('state_dir','state'),('cache_dir','cache')]:args+=['--'+key+'='+str(T/name)]
env=dict(os.environ);env.update(SDL_VIDEODRIVER='dummy',SDL_VIDEO_DRIVER='dummy',SDL_AUDIODRIVER='dummy',XDG_DATA_HOME=str(T/'userdata'),XDG_CONFIG_HOME=str(T/'userconfig'),XDG_CACHE_HOME=str(T/'usercache'))
with(T/'console.txt').open('wb')as f:
 p=subprocess.Popen(args,cwd=E,env=env,stdout=f,stderr=subprocess.STDOUT)
 try:
  start=time.monotonic()
  while time.monotonic()-start<45:
   time.sleep(.5);log=T/'logs/fs-uae.log.txt';txt=log.read_text(errors='replace')if log.exists()else''
   if 'BUMP_PROFILE_READY'in txt:print('PASS: delivered relative-path profile, DH0 only, cold boots the native title');break
   if p.poll()is not None:raise RuntimeError('profile emulator exited')
  else:raise TimeoutError('profile boot')
 finally:
  if p.poll()is None:p.terminate()
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
