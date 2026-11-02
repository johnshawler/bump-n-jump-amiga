from pathlib import Path
import struct,re,json,wave,bisect
import numpy as np
R=Path(__file__).resolve().parent;T=R/'controller-clock-final';P=R/'audio-probe/controller-final.pcm'
a=np.frombuffer(P.read_bytes(),'<i2').reshape(-1,2);mapping=[list(map(int,l.split(','))) for l in P.with_suffix('.pcm.csv').read_text().splitlines()];frames=[r[0]for r in mapping]
log=(T/'logs/fs-uae.log.txt').read_text(errors='replace');jump_field=int(re.search(r'BUMP JUMP_CONFIRMED field=(\d+)',log)[1])
raw=(T/'results/tick-audit.bin').read_bytes();ticks=[struct.unpack('>IIIHBBI',raw[i:i+20])for i in range(0,len(raw),20)]
jump=next(i for i,v in enumerate(ticks)if v[4]==5);impact=next(i for i,v in enumerate(ticks)if i>jump+96 and v[4]==2)
impact_field=jump_field+round((ticks[impact][0]-ticks[jump][0])/312)
def offset(frame):
 i=max(0,min(len(mapping)-1,bisect.bisect_left(frames,frame)));return mapping[i][1]//4
clips=[];checks=[]
for label,field,start,end in [('jump',jump_field,-10,90),('subsequent_gameplay',impact_field,-5,60)]:
 clip=a[offset(field+start):offset(field+end)];assert len(clip)>44100
 rms=float(np.sqrt(np.mean(clip.astype(float)**2)));assert rms>100
 checks.append({'event':label,'emulator_field':field,'seconds':len(clip)/44100,'RMS':rms,'peak':int(np.max(np.abs(clip.astype(int))))});clips.extend([clip,np.zeros((6615,2),np.int16)])
with wave.open(str(T/'Game-Event-Audio.wav'),'wb')as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(np.concatenate(clips).astype('<i2').tobytes())
report={'actual_emulated_Paula_PCM_capture':'PASS','format':'44100 Hz stereo signed 16-bit','field_to_sample_mapping':'emulator output callback CSV','source_jump_tick':jump+1,'subsequent_player_state_2_tick':impact+1,'clips':checks,'scope':'Real emulator sound output; original ROM audio requests are checked separately by verify_clock_audio.py. No subjective listening claim.'}
(T/'audio-capture-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
