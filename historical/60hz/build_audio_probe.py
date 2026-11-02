from pathlib import Path
import subprocess,shutil,shlex
R=Path(__file__).resolve().parent;O=R/'audio-probe';O.mkdir(exist_ok=True)
E=Path('/path/to/local-user/Documents/Codex/2026-10-12/i-w/outputs/bad-news-baseball-amiga/work/headless-emulator-source/fs-uae-3.2.35')
s=(E/'libfsemu/src/audio/dummy-audio.c').read_text().replace('#define FSE_INTERNAL_API','#include <stdio.h>\n#include <stdlib.h>\n#define FSE_INTERNAL_API')
s=s.replace('    return 0;\n}',r'''    extern int g_fs_uae_frame;
    static FILE *capture,*mapping;
    static unsigned long long position;
    static int checked;
    if (!checked) {checked=1;const char *path=getenv("BUMP_CAPTURE_PCM");if(path){capture=fopen(path,"wb");if(capture){setvbuf(capture,NULL,_IONBF,0);char map_path[4096];snprintf(map_path,sizeof(map_path),"%s.csv",path);mapping=fopen(map_path,"w");if(mapping)setvbuf(mapping,NULL,_IONBF,0);}}}
    if (stream==0 && capture && size>0) {if(mapping)fprintf(mapping,"%d,%llu,%d\n",g_fs_uae_frame,position,size);fwrite(data,1,size,capture);position+=size;}
    return 0;
}''',1)
(O/'dummy-audio.c').write_text(s)
subprocess.run(['clang','-DHAVE_CONFIG_H','-I'+str(E),'-I'+str(E/'libfsemu/include'),'-std=gnu99','-O2','-c',str(O/'dummy-audio.c'),'-o',str(O/'dummy-audio.o')],check=True)
shutil.copyfile(E/'libfsemu.a',O/'libfsemu.a');subprocess.run(['ar','r',str(O/'libfsemu.a'),str(O/'dummy-audio.o')],check=True)
line=(R/'build/emulator-relink.txt').read_text().split('\n')[-2]
assert line.startswith('g++ ')
a=shlex.split(line);a[a.index('-o')+1]=str(O/'fs-uae-audio-probe');a[a.index('libfsemu.a')]=str(O/'libfsemu.a')
subprocess.run(a,cwd=E,check=True,capture_output=True)
print('Read-only reuse of existing objects; separate PCM-capture emulator:',O/'fs-uae-audio-probe')
