exec(open('work/verify_raster.py').read().split("best=(999999,None)")[0].replace('R=Path(__file__).resolve().parent;T=R/sys.argv[1]','R=Path("work").resolve();T=R/"controller-hw-v2"'))
import struct
st=struct.unpack('>19I',(T/'results/stats.bin').read_bytes());ctrl,bank,sy=st[6],st[8],st[10]
nt=np.frombuffer((T/'results/native-nt.bin').read_bytes(),np.uint8).astype(np.int32);cdata=np.frombuffer((R/"Bump 'n' Jump (USA).nes").read_bytes()[32784:],np.uint8)
yy,xx=np.indices((240,256));q=(yy+sy)%240;page=((((ctrl&2)>>1)+(yy+sy)//240)&1)*1024;tile=nt[page+(q//8)*32+xx//8];at=nt[page+960+(q//32)*8+xx//32];at=(at>>(((q&16)>>2)|((xx&16)>>3)))&3
ad=bank*8192+(4096 if ctrl&16 else 0)+tile*16+(q&7);v=((cdata[ad]>>(7-(xx&7)))&1)|(((cdata[ad+8]>>(7-(xx&7)))&1)<<1);bg=np.where(v,v+at*4,0).astype(np.uint8)
hw=np.full((240,256),-1,np.int16);lists=(T/'results/hardware-lists.bin').read_bytes()
for ch in range(8):
 words=struct.unpack('>512H',lists[ch*1024:(ch+1)*1024]);i=0
 while words[i] or words[i+1]:
  pos,ctl=words[i:i+2];i+=2;x=(pos&255)*2+(ctl&1)-161;y=(pos>>8)+((ctl&4)<<6)-52;stop=(ctl>>8)+((ctl&2)<<7)-52
  for y in range(y,stop):
   b0,b1=words[i:i+2];i+=2
   for j in range(16):
    p=((b0>>(15-j))&1)|(((b1>>(15-j))&1)<<1)
    if p and 0<=x+j<256 and 0<=y<240:hw[y,x+j]=16+ch//2*4+p
orig=a.copy();orig[hw>=0]=bg[hw>=0]
for dy in range(-1,2):
 for dx in range(-2,3):
  e=orig.copy();ys,xs=np.nonzero(hw>=0);ys2=ys+dy;xs2=xs+dx;keep=(ys2>=0)&(ys2<240)&(xs2>=0)&(xs2<256);e[ys2[keep],xs2[keep]]=hw[ys[keep],xs[keep]]
  rgb=colors[pal[np.where(e%4==0,0,e)]&63];rgb=np.repeat(np.repeat(rgb,2,0),2,1);bad=np.count_nonzero(np.any(actual[52:532,138:650]!=rgb,axis=2));print(dx,dy,bad)
