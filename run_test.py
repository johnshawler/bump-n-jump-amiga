from pathlib import Path
import os,subprocess,time,json,signal,sys
R=Path(__file__).resolve().parent;T=R/(sys.argv[1] if len(sys.argv)>1 else 'test')
env=dict(os.environ);env.update(XDG_DATA_HOME=str(T/'userdata'),XDG_CONFIG_HOME=str(T/'userconfig'),XDG_CACHE_HOME=str(T/'usercache'),TMPDIR=str(T/'temp'))
f=(T/'console.txt').open('wb')
p=subprocess.Popen(['/Applications/FS-UAE.app/Contents/MacOS/fs-uae',str(T/'test.fs-uae')],cwd=T,env=env,stdout=f,stderr=subprocess.STDOUT)
(T/'pid').write_text(str(p.pid));print('Owned emulator PID',p.pid,flush=True)
start=time.monotonic()
while p.poll() is None and time.monotonic()-start<240:
 if (T/'results/stats.bin').exists():print('Results saved after',round(time.monotonic()-start,1),'seconds',flush=True);break
 time.sleep(.5)
if not (T/'results/stats.bin').exists():print('No results; emulator status',p.poll(),flush=True)
# Leave the window available for inspection; caller terminates this exact PID.
