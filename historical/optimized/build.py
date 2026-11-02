from pathlib import Path
import subprocess,sys,os
R=Path(__file__).resolve().parent
T=Path(os.environ.get('AMIGA_TOOLS','/path/to/local-user/.vscode/extensions/bartmanabyss.amiga-debug-1.8.2/bin/darwin'));cc=str(T/'opt/bin/m68k-amiga-elf-gcc')
def run(a):
 r=subprocess.run(a,cwd=R,capture_output=True,text=True)
 if r.returncode:print((r.stdout+r.stderr)[-8000:]);sys.exit(r.returncode)
objs=[]
for name in ['start','cpu_native','cpu_helpers','sprites','assets','bus','render','hw_sprites','audio','main','memory']:
 src=R/'src'/(name+('.s' if name in ['start','cpu_native','sprites'] else '.c'));obj=R/'build'/(name+'.o');objs.append(str(obj))
 if not obj.exists() or obj.stat().st_mtime<src.stat().st_mtime or name=='main':
  print('Compiling',name,flush=True)
  run([cc,'-m68020','-O2','-fomit-frame-pointer','-fno-builtin','-nostdlib','-ffunction-sections','-fdata-sections','-Wall','-Wextra','-Wno-unused-parameter','-DAUTOTEST='+('1' if '--test' in sys.argv else '0'),'-c',str(src),'-o',str(obj)])
run([cc,'-m68020','-nostdlib','-Wl,--emit-relocs,--gc-sections,-Ttext=0,-e,_start,-Map='+str(R/'build/game.map'),*objs,'-o',str(R/'build/game.elf')])
run([str(T/'elf2hunk'),str(R/'build/game.elf'),str(R/'build/BumpNJump')])
print('Amiga executable:',(R/'build/BumpNJump').stat().st_size)
