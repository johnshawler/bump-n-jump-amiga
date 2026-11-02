import os,pty,socket,json,select,time,termios,sys,signal
from pathlib import Path
R=Path(__file__).resolve().parent;T=R/(sys.argv[1] if len(sys.argv)>1 else 'test');sockpath=str(T/'control.sock')
try:os.unlink(sockpath)
except FileNotFoundError:pass
pid,fd=pty.fork()
if pid==0:
 os.chdir(T);os.environ.update(XDG_DATA_HOME=str(T/'userdata'),XDG_CONFIG_HOME=str(T/'userconfig'),XDG_CACHE_HOME=str(T/'usercache'),TMPDIR=str(T/'temp'))
 os.execv('/Applications/FS-UAE.app/Contents/MacOS/fs-uae',['fs-uae',str(T/'test.fs-uae')])
(T/'pid').write_text(str(pid));print('Owned emulator PID',pid,flush=True)
t=termios.tcgetattr(fd);t[3]&=~termios.ECHO;termios.tcsetattr(fd,termios.TCSANOW,t)
log=(T/'pty-console.txt').open('ab',buffering=0)
def drain(timeout=10,prompt=True):
 data=b'';end=time.monotonic()+timeout
 while time.monotonic()<end:
  r,_,_=select.select([fd],[],[],.1)
  if r:
   try:b=os.read(fd,65536)
   except OSError:break
   log.write(b);data+=b
   if prompt and data.endswith(b'>'):break
 return data.decode(errors='replace')
s=socket.socket(socket.AF_UNIX);s.bind(sockpath);s.listen()
while True:
 c,_=s.accept();f=c.makefile('rwb');req=json.loads(f.readline());outputs=[]
 try:
  if req.get('wait'):outputs.append(drain())
  for cmd in req.get('commands',[]):os.write(fd,(cmd+'\n').encode());outputs.append(drain())
  if req.get('kill'):os.kill(pid,signal.SIGTERM)
  f.write((json.dumps({'ok':True,'output':''.join(outputs)})+'\n').encode())
 except Exception as e:f.write((json.dumps({'ok':False,'error':str(e)})+'\n').encode())
 f.flush();c.close()
 if req.get('kill'):break
