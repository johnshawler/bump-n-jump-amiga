from pathlib import Path
import subprocess,ctypes as C,json,random
R=Path(__file__).resolve().parent
(R/'stage-select/score-stubs.c').write_text('unsigned char ram[2048];\n')
subprocess.run(['clang','-dynamiclib','-O2','-fno-builtin','-I'+str(R/'src'),str(R/'src/scores.c'),str(R/'src/memory.c'),str(R/'stage-select/score-stubs.c'),'-o',str(R/'build/scores.dylib')],check=True)
s=C.CDLL(str(R/'build/scores.dylib'));s.scores_rank.argtypes=[C.c_uint];s.scores_unpack.argtypes=[C.c_void_p];s.scores_pack.argtypes=[C.c_void_p,C.c_uint];s.scores_insert.argtypes=[C.c_uint,C.c_uint,C.c_char_p]
class Score(C.Structure):_fields_=[('score',C.c_uint),('initials',C.c_char*3),('stage',C.c_ubyte)]
table=(Score*10).in_dll(s,'scores');gen=C.c_uint.in_dll(s,'scores_generation');buf=(C.c_ubyte*96)()
s.scores_reset();assert s.scores_rank(0)==-1
random.seed(42);expected=[]
for i in range(1000):
 n=random.randint(1,999999);letters=bytes(random.randint(65,90)for _ in range(3));stage=random.randint(1,16)
 s.scores_insert(n,stage,letters);expected.append((n,letters,stage));expected=sorted(expected,key=lambda x:-x[0])[:10]
 assert [(v.score,v.initials,v.stage) for v in table[:len(expected)]]==expected
s.scores_pack(buf,4);valid=bytes(buf);s.scores_reset();assert s.scores_unpack(buf)==1 and gen.value==4
assert [(v.score,v.initials,v.stage)for v in table]==expected
assert s.scores_unpack(buf)==0 # duplicate/older generation
# Every single-byte corruption is rejected and preserves the existing table.
for i in range(96):
 bad=bytearray(valid);bad[i]^=0x80;a=(C.c_ubyte*96).from_buffer_copy(bad);assert not s.scores_unpack(a)
 assert [(v.score,v.initials,v.stage)for v in table]==expected
# Checksummed malformed payloads must also fail validation.
def sign(d):
 h=2166136261
 for v in d[:92]:h=((h^v)*16777619)&0xffffffff
 d[92:]=h.to_bytes(4,'big');return(C.c_ubyte*96).from_buffer_copy(d)
for i,v in [(12,0xff),(16,ord('!')),(19,17),(20,0xff)]:
 d=bytearray(valid);d[8:12]=(5).to_bytes(4,'big');d[i]=v;assert not s.scores_unpack(sign(d))
# Original score digits are little-endian decimal bytes, not packed BCD.
ram=(C.c_ubyte*2048).in_dll(s,'ram')
for i,v in enumerate([6,5,4,3,2,1]):ram[0x4e+i]=v
assert s.game_score()==123456
(R/'build/score-format-verification.json').write_text(json.dumps(dict(ranking_cases=1000,round_trip=True,corruptions_rejected=96,checksummed_invalid_records_rejected=4,old_generation_rejected=True,score_decode=123456),indent=2));print('Score ranking, exact format, corruption fallback and decimal score decoding pass')
