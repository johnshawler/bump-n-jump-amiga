from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,os,json,hashlib
R=Path(__file__).resolve().parent

def test(stage):
 name=os.environ.get('BUMP_ALL_TAG','native-stage')+'-%02d-final'%stage
 env=dict(os.environ,BUMP_TEST_DIR=name,BUMP_SCENARIO='3',BUMP_STAGE=str(stage))
 p=subprocess.run(['python3',str(R/'menu_test.py')],env=env,capture_output=True,text=True)
 assert p.returncode==0,(stage,p.stdout,p.stderr)
 T=R/name
 for script in ['verify_native.py','verify_clock_audio.py']:
  p=subprocess.run([str(R/'venv/bin/python'),str(R/script),name+'/results'],capture_output=True,text=True);assert not p.returncode,(stage,script,p.stdout,p.stderr)
 assert 'BUMP STAGE_LOADED '+str(stage-1)+' ' in (T/'logs/fs-uae.log.txt').read_text(errors='replace')
 print('Stage',stage,'PASS: real menu input, native game state, pixels, per-tick CPU and event audio',flush=True)
 return dict(stage=stage,test=name,hdf_sha256=hashlib.sha256((T/'boot.hdf').read_bytes()).hexdigest(),native=json.loads((T/'results/native-verification.json').read_text()))
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(test,map(int,os.environ.get('BUMP_ALL_STAGES',','.join(map(str,range(1,17)))).split(','))))
(R/('build/'+os.environ.get('BUMP_ALL_REPORT','all-stages-verification.json'))).write_text(json.dumps(rows,indent=2))
