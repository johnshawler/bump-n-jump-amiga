from pathlib import Path
import sys,struct,json,statistics
sys.path.insert(0,str(Path(__file__).parent));from reference import Bus,MPU,R
T=R/sys.argv[1];inputs=(T/'native-input.bin').read_bytes();N=len(inputs)
raw=(T/'tick-audit.bin').read_bytes();size=len(raw)//min(N,4096);assert size in [16,20],(size,N,len(raw))
rows=[struct.unpack('>IIIHBB'+('I' if size==20 else ''),raw[i:i+size])for i in range(0,len(raw),size)]
class TraceBus(Bus):
 def __init__(self):
  super().__init__();self.hash=2166136261;self.writes=0;self.events=[]
 def __setitem__(self,a,v):
  a&=65535;v&=255
  if 0x4000<=a<0x4020 and a not in [0x4014,0x4016]:
   self.hash=((self.hash*33)^((a<<8)|v))&0xffffffff;self.writes+=1;self.events.append([a,v])
  super().__setitem__(a,v)
b=TraceBus();b.oam[:]=bytes(256);m=MPU(memory=b,pc=None)
def run():
 for _ in range(100000):
  if (m.pc==0x8070 and not b.ram[14]) or (m.pc==0x9321 and b.ram[0x401]):return
  m.step()
 raise RuntimeError('source stalled')
run();cues=[];lastmode=0
starts=(T/'stage-starts.bin').read_bytes() if (T/'stage-starts.bin').exists() else b''
overrides=dict(struct.iter_unpack('>II',starts))
for tick,pad in enumerate(inputs):
 if tick in overrides:b.ram[0x3c]=overrides[tick]
 b.pad=pad;before=b.writes;b.events=[]
 if b.ctrl&128:m.nmi()
 run()
 if tick<len(rows):
  row=rows[tick];assert row[2]==b.hash,('audio source hash',tick,row[2],b.hash)
  assert row[3]==b.writes-before,('audio writes',tick,row[3],b.writes-before)
  assert list(row[4:6])==[b.ram[0x85]&15,b.ram[20]],('game event',tick)
  if size==20:
   h=0
   for v in [m.a,m.x,m.y,m.sp,m.p,m.pc]:h=(h*33+v)&0xffffffff
   assert h==row[6],('CPU tick',tick,h,row[6])
 mode=b.ram[0x85]&15
 if mode!=lastmode:
  cues.append({'source_tick':tick+1,'player_mode':mode,'source_audio_writes':b.writes-before,'register_writes':b.events})
 lastmode=mode
assert (T/'native-apu.bin').read_bytes()==bytes(b.apu)
publications,writes,hash_value=struct.unpack('>3I',(T/'audio-stats.bin').read_bytes())
assert publications==N,(publications,N);assert writes==b.writes and hash_value==b.hash
freq=312*49.9201
windows=[]
for lo,hi,label in [(0,len(rows),'whole_recording'),(700,min(1500,len(rows)),'gameplay_700_1500'),(900,min(1500,len(rows)),'crowded_900_1500')]:
 a=rows[lo:hi]
 if len(a)<61:continue
 intervals=[(y[0]-x[0])/freq*1000 for x,y in zip(a,a[1:])];costs=[(r[1]-r[0])/freq*1000 for r in a]
 rates=[60*freq/(a[i+60][0]-a[i][0])for i in range(len(a)-60)]
 windows.append({'window':label,'ticks':len(a),'mean_update_hz':(len(a)-1)*freq/(a[-1][0]-a[0][0]),'mean_CPU_audio_ms':statistics.mean(costs),'max_CPU_audio_ms':max(costs),'max_update_start_gap_ms':max(intervals),'lowest_60_tick_window_hz':min(rates),'highest_60_tick_window_hz':max(rates)})
report={'source_ticks':N,'per_tick_records_checked':len(rows),'per_tick_CPU_state_hash':'PASS' if size==20 else 'not recorded','all_original_ROM_APU_writes_in_order':'PASS','total_original_APU_register_writes':writes,'audio_publications':publications,'audio_published_once_per_source_tick':True,'final_APU_registers':'PASS','timing':windows,'game_event_transitions':cues,'scope':'Source ROM audio requests and native publication cadence checked; Paula synthesis remains approximate.'}
(T/'clock-audio-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='game_event_transitions'},indent=2))
