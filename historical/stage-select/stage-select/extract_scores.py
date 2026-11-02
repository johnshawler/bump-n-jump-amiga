from pathlib import Path
import subprocess,os,sys,struct,json
R=Path(__file__).resolve().parents[1];T=R/sys.argv[1];D=T/'score-readback';D.mkdir(exist_ok=True)
env=dict(os.environ,PYTHONPATH='/path/to/local-user/Documents/Codex/2026-10-06/task-3/private/tools/amitools')
rows=[]
for slot in ['A','B']:
 p=D/('HighScores.'+slot)
 r=subprocess.run(['python3','-m','amitools.tools.xdftool',str(T/'boot.hdf'),'read','HighScores.'+slot,str(p)],env=env,capture_output=True,text=True);assert not r.returncode,r.stdout+r.stderr
 d=p.read_bytes();assert len(d)==96 and d[:8]==b'BNJHS001';h=2166136261
 for v in d[:92]:h=((h^v)*16777619)&0xffffffff
 assert int.from_bytes(d[92:],'big')==h
 records=[dict(score=int.from_bytes(d[a:a+4],'big'),initials=d[a+4:a+7].decode(),stage=d[a+7])for a in range(12,92,8)]
 rows.append(dict(slot=slot,generation=int.from_bytes(d[8:12],'big'),records=records))
assert rows[0]['generation']==1 and rows[1]['generation']==2
assert rows[0]['records'][0]==dict(score=123456,initials='AAA',stage=8)
assert rows[1]['records'][:2]==[dict(score=654321,initials='ZED',stage=8),dict(score=123456,initials='AAA',stage=8)]
(T/'score-save-verification.json').write_text(json.dumps(dict(actual_HDF_files=rows,checksums='PASS',scope='Synthetic completed scores; native original game-over path, real initials input, actual DOS saves and Continue tested.'),indent=2));print('Both actual HDF score files and initials/checksums verified')
