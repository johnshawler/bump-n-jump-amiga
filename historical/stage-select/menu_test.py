from pathlib import Path
import os,subprocess,time,re,json,shutil,hashlib
R=Path(__file__).resolve().parent;T=R/os.environ.get('BUMP_TEST_DIR','controller-final');T.mkdir(exist_ok=True)
assert not (T/'results/stats.bin').exists(), 'Use a fresh test directory'
for p in (R/'test').iterdir():
 if p.is_dir():(T/p.name).mkdir(exist_ok=True)
theme=T/'theme';theme.mkdir(exist_ok=True)
E=Path('/path/to/local-user/Documents/Codex/2026-10-12/i-w/outputs/bad-news-baseball-amiga/work/headless-emulator-source/fs-uae-3.2.35')
EXE=Path('/path/to/local-user/Documents/Codex/2026-10-12/i-w/outputs/bad-news-baseball-amiga/releases/runner-two-player-2026-10-15/headless-input-test-fs-uae')
if os.environ.get('BUMP_EMULATOR'):EXE=Path(os.environ['BUMP_EMULATOR'])
events={name:i+1 for i,name in enumerate(re.findall(r'^DEFEVENT2?\(\s*(\w+)',(E/'src/inputevents.def').read_text(),re.M))}
objdump='/path/to/local-user/.vscode/extensions/bartmanabyss.amiga-debug-1.8.2/bin/darwin/opt/bin/m68k-amiga-elf-objdump'
sy={v[2]:int(v[0],16) for line in subprocess.check_output([objdump,'-t',str(R/'build/game.elf')],text=True).splitlines() if len(v:=line.split('\t')[-1].split())==3}
# Read the unambiguous global names from the ELF symbol table.
sy={}
for line in subprocess.check_output([objdump,'-t',str(R/'build/game.elf')],text=True).splitlines():
 v=line.split()
 if len(v)>=6 and v[0].isalnum():
  try:sy[v[-1]]=int(v[0],16)
  except ValueError:pass
lua=r'''
local delta=nil;local field=0;local frame=nil;local ram=nil;local ticks=nil;local control=nil;local delay=0
local function rd(a)return uae_read_u16(a)or 0 end
local function rb(a)return uae_read_u8(a)or 0 end
local function long(a)return rd(a)*65536+rd(a+2)end
local function wl(a,v)uae_write_u16(a,math.floor(v/65536));uae_write_u16(a+2,v%65536)end
local function log(s)uae_log('BUMP '..s..' field='..field..' tick='..(ticks and long(ticks)or 0)..' mode='..(ram and rb(ram+20)or 0)..'\n')end
local function wait(n)delay=n;coroutine.yield()end
local function until_true(fn,limit,label)for i=1,limit do if fn()then return end;wait(1)end;error('timeout '..label)end
local function wait_ticks(n)local target=long(ticks)+n;until_true(function()return long(ticks)>=target end,4000,'ticks')end
local function tap(event)fs_uae_send_input_event(event,1);wait(15);fs_uae_send_input_event(event,0);wait(15)end
local function capture(name)
 local bytes,w,h,stride,pixels=bnb_video_frame()
 if bytes then local hex=string.gsub(bytes,'.',function(c)return string.format('%02x',string.byte(c))end);uae_log('BUMP_CAPTURE '..name..' '..w..' '..h..' '..stride..' '..pixels..' '..hex..'\n')end
end
local task=coroutine.create(function()
 until_true(function()
  local irq=long(0x6c)
  if irq<0x200000 and rd(irq)==0x48e7 and rd(irq+22)==0x52b9 then
   frame=long(irq+24);delta=frame-FIELD_ELF
   ram=RAM_ELF+delta;ticks=TICKS_ELF+delta;control=CONTROL_ELF+delta
   return true
  end
  return false
 end,20000,'native takeover')
 wl(control,2);log('TAKEOVER')
 until_true(function()return rb(ram+20)==2 end,4000,'title')
 wait_ticks(SCENARIO==3 and 10 or 120);capture('title');log('TITLE')
 if SCENARIO==2 then
  tap(KEY_TAB);until_true(function()return long(KIND_ELF+delta)==2 end,500,'saved table');wait(30);assert(long(GEN_ELF+delta)==EXPECT_GEN,'persisted generation');assert(long(SCORES_ELF+delta)==EXPECT_SCORE,'persisted first score');capture('persisted-scores');log('PERSISTED '..long(SCORES_ELF+delta)..' '..long(SCORES_ELF+delta+8)..' gen='..long(GEN_ELF+delta))
 else
  tap(KEY_RETURN);until_true(function()return long(MENU_ELF+delta)==1 end,1000,'stage selector');wait(30)
  if SCENARIO==0 then
   tap(JOY2_LEFT);assert(long(CHOICE_ELF+delta)==15,'left wrap');capture('stage-16-wrap')
   tap(JOY2_RIGHT);assert(long(CHOICE_ELF+delta)==0,'right wrap')
   tap(KEY_TAB);assert(long(KIND_ELF+delta)==2,'top ten');capture('empty-scores');tap(KEY_TAB)
  end
  if SCENARIO==3 and TARGET_STAGE>9 then for i=1,17-TARGET_STAGE do tap(JOY2_LEFT)end else for i=2,TARGET_STAGE do tap(JOY2_RIGHT)end end
  assert(long(CHOICE_ELF+delta)==TARGET_STAGE-1,'stage choice');capture('stage-select');log('SELECT_STAGE '..TARGET_STAGE)
  tap(JOY2_FIRE_BUTTON)
  until_true(function()return rb(ram+20)==12 and rb(ram+0x56)==TARGET_STAGE-1 end,5000,'selected stage gameplay');log('STAGE_LOADED '..rb(ram+0x56));wait_ticks(30);capture('selected-gameplay')
  if SCENARIO==1 then
   -- Synthetic completed runs exercise initials, ranking and disk writes.
   -- Gameplay and stage loading above use only real emulated input.
   local function end_run(n)
    for i=0,5 do uae_write_u8(ram+0x4e+i,n%10);n=math.floor(n/10)end
    uae_write_u8(ram+0x4d,1);uae_write_u8(ram+20,19);uae_write_u8(ram+21,0);uae_write_u8(ram+22,0)
    until_true(function()return long(KIND_ELF+delta)==3 and long(MENU_ELF+delta)==1 end,2000,'initial entry')
   end
   end_run(123456);wait(10);capture('initial-entry');tap(KEY_RETURN)
   until_true(function()return long(KIND_ELF+delta)==2 and long(GEN_ELF+delta)==1 end,2000,'first disk save');capture('scores-first');log('FIRST_SAVE')
   tap(KEY_RETURN);assert(long(KIND_ELF+delta)==4,'continue prompt');capture('continue');tap(KEY_RETURN)
   until_true(function()return rb(ram+20)==12 end,5000,'continued gameplay')
   for i=0,5 do assert(rb(ram+0x4e+i)==0,'continue score zero')end
   assert(rb(ram+0x4d)==3,'three lives');assert(rb(ram+0x56)==TARGET_STAGE-1,'same stage');log('CONTINUE_SCORE_ZERO')
   end_run(654321);tap(KEY_Z);tap(KEY_E);tap(KEY_D);tap(KEY_RETURN)
   until_true(function()return long(KIND_ELF+delta)==2 and long(GEN_ELF+delta)==2 end,2000,'second disk save');wait(20);capture('scores-second');log('SECOND_SAVE')
   tap(KEY_RETURN);assert(long(KIND_ELF+delta)==4,'second continue prompt');tap(JOY2_DOWN);tap(KEY_RETURN)
   until_true(function()return long(MENU_ELF+delta)==0 end,500,'decline continue');until_true(function()return rb(ram+20)==2 end,2000,'title after no');log('CONTINUE_DECLINED')
  else
   fs_uae_send_input_event(JOY2_UP,1);wait_ticks(SCENARIO==3 and 30 or 360);fs_uae_send_input_event(JOY2_UP,0)
  end
 end
 capture('gameplay');log('ESCAPE');fs_uae_send_input_event(KEY_ESC,1);wait(20);fs_uae_send_input_event(KEY_ESC,0);wait(30);log('DONE')
end)
function on_uae_vsync()
 field=field+1
 if field%500==0 then log('PROGRESS')end
 if delay>0 then delay=delay-1;return end
 if coroutine.status(task)~='dead' then local ok,e=coroutine.resume(task);if not ok then log('ERROR '..tostring(e));error(e)end end
end
'''
if os.environ.get('BUMP_PAUSED_CAPTURE'):
 lua=lua.replace("capture('gameplay');log('ESCAPE')", "tap(KEY_RETURN);wait(45);capture('paused');capture('gameplay');log('ESCAPE')")
vals={'FIELD_ELF':sy['fields'],'RAM_ELF':sy['ram'],'TICKS_ELF':sy['source_ticks'],'CONTROL_ELF':sy['test_control'],'MENU_ELF':sy['menu_active'],'KIND_ELF':sy['menu_kind'],'CHOICE_ELF':sy['menu_choice'],'SCORES_ELF':sy['scores'],'GEN_ELF':sy['scores_generation'],'TARGET_STAGE':int(os.environ.get('BUMP_STAGE','1')),'SCENARIO':int(os.environ.get('BUMP_SCENARIO','0')),'EXPECT_GEN':int(os.environ.get('BUMP_EXPECT_GEN','2')),'EXPECT_SCORE':int(os.environ.get('BUMP_EXPECT_SCORE','654321'))}
for key in ['KEY_RETURN','KEY_SPACE','KEY_ESC','JOY2_UP','JOY2_LEFT','JOY2_RIGHT','JOY2_FIRE_BUTTON','KEY_TAB','KEY_Z','KEY_E','KEY_D','JOY2_DOWN']:vals[key]=events[key]
for k,v in vals.items():lua=re.sub(r'\b'+k+r'\b',str(v),lua)
lua='local OUT='+json.dumps(str(T))+'\n'+lua;(theme/'theme.lua').write_text(lua)
shutil.copyfile(Path(os.environ.get('BUMP_BOOT_HDF',str(R/'build/BumpNJump-A1200.hdf'))),T/'boot.hdf')
s=(R/'test/test.fs-uae').read_text().replace(str(R/'test'),str(T)).replace(str(R/'build/BumpNJump-A1200.hdf'),str(T/'boot.hdf'))
s=s.replace('hard_drive_0_read_only = 1','hard_drive_0_read_only = 0')
s+='\nvideo_driver = sdl-software\nvideo_sync = off\naudio_driver = dummy\nbenchmark = 0\nwarp_mode = 0\nlog_flush = 1\ntheme = '+str(theme)+'\n'
(T/'test.fs-uae').write_text(s)
env=dict(os.environ);env.update(SDL_VIDEODRIVER='dummy',SDL_VIDEO_DRIVER='dummy',SDL_AUDIODRIVER='dummy',XDG_DATA_HOME=str(T/'userdata'),XDG_CONFIG_HOME=str(T/'userconfig'),XDG_CACHE_HOME=str(T/'usercache'))
with (T/'console.txt').open('wb') as f:
 p=subprocess.Popen([str(EXE),str(T/'test.fs-uae')],cwd=E,env=env,stdout=f,stderr=subprocess.STDOUT);print('Hardware-input test PID',p.pid,flush=True)
 start=time.monotonic();seen=''
 try:
  while time.monotonic()-start<240:
   time.sleep(.5);log=(T/'logs/fs-uae.log.txt');txt=log.read_text(errors='replace') if log.exists() else ''
   rows=re.findall(r'BUMP [^\n]+',txt)
   if rows and rows[-1]!=seen:seen=rows[-1];print(seen,flush=True)
   receipt=T/'results/stats.bin'
   if receipt.exists() and receipt.stat().st_size==76:time.sleep(.3);print('Release hardware-input receipt saved',flush=True);break
   if 'BUMP ERROR' in txt:raise RuntimeError(rows[-1])
   if p.poll()is not None:raise RuntimeError('emulator exited '+str(p.returncode))
  else:raise TimeoutError('controller run')
 finally:
  if p.poll()is None:p.terminate()
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
for name,w,h,stride,pixels,data in re.findall(r'BUMP_CAPTURE ([\w-]+) (\d+) (\d+) (\d+) (\d+) ([0-9a-f]+)',txt):
 (T/(name+'.z')).write_bytes(bytes.fromhex(data));(T/(name+'.json')).write_text(json.dumps([int(w),int(h),int(stride),int(pixels)]))
print('Release HDF hash',hashlib.sha256((T/'boot.hdf').read_bytes()).hexdigest())
