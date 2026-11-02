from pathlib import Path
import sys,json,itertools
sys.path.insert(0,str(Path(__file__).parent));from reference import *
T=R/'controller-final';inputs=(T/'results/native-input.bin').read_bytes();b=Bus();b.oam[:]=bytes(256);m=MPU(memory=b,pc=None)
def run():
 while not((m.pc==0x8070 and not b.ram[14]) or (m.pc==0x9321 and b.ram[0x401])):m.step()
run();modes=[];events=[]
for tick,pad in enumerate(inputs):
 b.pad=pad
 if b.ctrl&128:m.nmi()
 run();mode=b.ram[0x85]&15;modes.append(mode)
 if not tick or mode!=modes[-2]:events.append([tick+1,mode])
starts=[i for i,x in enumerate(modes) if x==5 and (i==0 or modes[i-1]!=5)]
proof=[]
for start in starts:
 landing=next((j for j in range(start+1,len(modes)) if modes[j] not in [5,6,7]),None)
 release=next((j for j in range(start,len(inputs)) if not inputs[j]&1),None)
 proof.append({'start_tick':start+1,'next_non_jump_tick':landing+1 if landing else None,'duration_ticks':landing-start if landing else None,'landing_mode':modes[landing] if landing else None,'release_tick':release+1 if release else None,'retrigger_before_release':any(j>start and release and j<release for j in starts)})
print('player mode transitions',events);print(json.dumps(proof,indent=2))
assert proof and proof[0]['duration_ticks']==96 and not proof[0]['retrigger_before_release']
(T/'jump-verification.json').write_text(json.dumps({'jump_sequences':proof,'reference_replay_of_exact_native_hardware_inputs':'PASS'},indent=2))
