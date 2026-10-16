"""Stage10a1 engine/controller fixture derived from the Stage9b1 model, not XEMU."""
import os,re,sys,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'releases/stage_10a/stage10a1'
def namespace(text,name):
 start=text.index('.namespace '+name+' {');a=text.index('{',start);depth=1;b=a+1
 while depth:
  if text[b]=='{':depth+=1
  if text[b]=='}':depth-=1
  b+=1
 return start,b,text[a+1:b-1]
def labels(text):return {k:int(v,16) for k,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',text)}
SYMBOLS=(ART/'STAGE10A1.sym').read_text();G=labels(namespace(SYMBOLS,'audio8')[2]);BOOT=labels(namespace(SYMBOLS,'audioboot')[2]);C=labels((ART/'stage10a1_audio_core.sym').read_text())
clean=SYMBOLS
for ns in ('audio8','audioboot','hslink','twop'):
 a,b,_=namespace(clean,ns);clean=clean[:a]+clean[b:]
ALIAS=tempfile.TemporaryDirectory(prefix='stage10a1-engine-model-');alias=Path(ALIAS.name)
for f in ART.iterdir():
 name=f.name.replace('STAGE10A1','STAGE7B5B');(alias/name).symlink_to(f)
(alias/'STAGE7B5B.sym').unlink();(alias/'STAGE7B5B.sym').write_text(clean)
os.environ['STAGE7B5B_ARTIFACTS']=str(alias)
import test_stage7b5b as M
B=M.B;N=M.N
class AudioMemory(B.MenuMemory):
 def __getitem__(self,a):
  if a in (0xd011,0xd012):
   raster=(self.clock_cycles%810000)*312//810000
   return raster&255 if a==0xd012 else (self.data[a]&127)|((raster&256)>>1)
  if not getattr(self,'linear',False) and 0xa000<=a<0xc000 and self.map_mask&32:return self.data[a+self.map_offset]
  if a==0xd6f5:return self.mixer[self.data[0xd6f4]]
  if a==0xd7fa:return self.frame_counter
  if 0x08000000<=a<0x080b0000:return self.attic[(a-0x08000000)&self.attic_mask]
  return super().__getitem__(a)
 def __setitem__(self,a,v):
  v&=255
  if a in (0xd720,0xd740) and v&0x88==0x80 and self.data[a]&0x88!=0x80:
   source=(a-0xd720)//32
   self.starts.append((source,self.data[C['choices']+0x14000+source],self.frame_counter,len(self.samples[source])))
  if not getattr(self,'linear',False) and 0xa000<=a<0xc000 and self.map_mask&32:self.data[a+self.map_offset]=v;return
  if a==0xd6f5:self.mixer[self.data[0xd6f4]]=v;return
  if 0x08000000<=a<0x080b0000:self.attic[(a-0x08000000)&self.attic_mask]=v;return
  if a!=0xd705:return super().__setitem__(a,v)
  self.data[a]=v;p=self.data[0xd701]*256+v+(self.data[0xd702]&15)*65536
  assert self.data[0xd704]==0
  srcmb=dstmb=0
  while self.data[p]:
   opt=self.data[p];p+=1
   if opt==0x80:srcmb=self.data[p];p+=1
   elif opt==0x81:dstmb=self.data[p];p+=1
   else:assert opt==0xa
  p+=1;d=self.data[p:p+11];assert d[0] in (0,3) and d[9:]==bytes(2)
  n=int.from_bytes(d[1:3],'little');assert n
  src=int.from_bytes(d[3:6],'little')+(srcmb<<20);dst=int.from_bytes(d[6:9],'little')+(dstmb<<20)
  if getattr(self,'title_active',False):
   for lo,hi in B.OLD.TITLE_RANGES+[(0xff82000,0xff82a50)]:assert not(dst<hi and dst+n>lo),('Title overwritten',hex(dst),n)
  prev=self.linear;self.linear=True
  try:
   if d[0]==3:payload=bytes([d[3]])*n
   elif 0xff7e000<=src<0xff80000:payload=self.char_wom[src-0xff7e000:src-0xff7e000+n]
   else:payload=bytes(self[src+i] for i in range(n))
   for i,v in enumerate(payload):self[dst+i]=v
  finally:self.linear=prev
  self.base.transfers.append((src,dst,n))
  self.elapse(n*4)
 def elapse(self,cycles):
  self.clock_cycles+=cycles
  self.frame_counter=(self.clock_cycles//810000)&255
  self.elapsed_cycles+=cycles
  if not self.simulate_audio:return
  for source in (0,1):
   r=0xd720+32*source
   if self.data[r]&0x88!=0x80:self.fractions[source]=0;continue
   rate=int.from_bytes(self.data[r+4:r+7],'little')
   count,self.fractions[source]=divmod(self.fractions[source]+rate*cycles,1<<24)
   self.advance(source,count)
 def advance(self,source,n):
  d=self.data;r=0xd720+32*source;base=(0x16400,0x5c500)[source]
  for i in range(n):
   if d[r]&0x88!=0x80:break
   p=int.from_bytes(d[r+10:r+13],'little');assert base<=p<base+4096,hex(p)
   self.samples[source].append(d[p]);p+=1
   if p&65535==int.from_bytes(d[r+7:r+9],'little'):
    if d[r]&64:p=int.from_bytes(d[r+1:r+4],'little')
    else:d[r]|=8
   d[r+10:r+13]=p.to_bytes(3,'little')
class AudioCPU(B.Machine().cpu.__class__):
 def step(self):
  before=self.processorCycles;result=self.execute_step()
  self.memory.elapse(self.processorCycles-before)
  if self.memory.map_mask&32:
   assert self.p&4, ("IRQ enabled with banked audio/bootstrap mapping",hex(self.pc),hex(self.memory.map_mask))
  return result
 def execute_step(self):
  op=self.memory[self.pc]
  if op in (0xda,0x5a,0xdb):
   self.stPush({0xda:self.x,0x5a:self.y,0xdb:self.z}[op]);self.pc+=1;self.processorCycles+=3;return self
  if op in (0xfa,0x7a,0xfb):
   v=self.stPop();setattr(self,{0xfa:'x',0x7a:'y',0xfb:'z'}[op],v);self.FlagsNZ(v);self.pc+=1;self.processorCycles+=4;return self
  if op==0xa3:
   self.z=self.memory[self.pc+1];self.FlagsNZ(self.z);self.pc+=2;self.processorCycles+=2;return self
  if op==0x5c:
   assert self.p&4,'MAP without SEI'
   assert self.a==self.x==0 and (self.y,self.z) in ((0x40,0x20),(0x40,0x21),(0,0x83))
   self.memory.map_mask=self.z&0xf0;self.memory.map_offset=(self.y<<8)|((self.z&15)<<16)
   self.pc+=1;self.processorCycles+=2;return self
  return super().step()
class Machine(B.Machine):
 def __init__(self):
  super().__init__();self.memory.__class__=AudioMemory;self.memory.attic=bytearray(0xb0000)
  self.memory.map_mask=0x80;self.memory.map_offset=0x30000;self.memory.mixer=bytearray((7+13*i)&255 for i in range(256));self.memory.frame_counter=0;self.memory.samples=[bytearray(),bytearray()];self.memory.starts=[];self.memory.attic_mask=0xfffff;self.memory.clock_cycles=0;self.memory.simulate_audio=False;self.memory.elapsed_cycles=0;self.memory.fractions=[0,0]
  for i in range(4):self.memory.data[0xd720+16*i]=2
  self.memory.data[0xd711]=0;self.cpu.__class__=AudioCPU
  self.files['VYSO.DAT']=(ART/'VYSO.DAT').read_bytes();self.files['VYHS.DAT']=(ART/'VYHS.DAT').read_bytes();self.before=bytes(self.memory.data);self.mixer_before=bytes(self.memory.mixer)
 def trap(self):
  assert self.memory.map_mask==0x80 and self.memory.map_offset==0x30000,('KERNAL with banked audio map',hex(self.cpu.pc))
  super().trap()
 def run_to(self,targets,limit=50_000_000):return super().run_to(targets,limit)
 def frame(self,key=0,buttons=255):
  return super().frame(key,buttons)
 def sound(self,name,x=0):
  self.cpu.x=x;return self.call_at(G[name])
 def call_at(self,p):
  self.cpu.pc=p;self.cpu.stPushWord(0x1ff);return self.run_to([0x200],3_000_000)
def core(m,n,i=0):return m.memory.data[C[n]+0x14000+i]
# Highscore persistence uses the confirmed constrained DOS model; engine loads
# continue using the existing SEQ/ROM model. Neither is a physical drive emulator.
import test_stage9c2 as HI
import test_stage3b2_runtime
sys.modules['stage3b2_legacy_model']=test_stage3b2_runtime.LEGACY
HS=labels((ART/'highscore.sym').read_text())
H=labels(namespace(SYMBOLS,'hslink')[2]);TP=labels(namespace(SYMBOLS,'twop')[2])
MN=labels((ART/'MENU_OVERLAY.sym').read_text())
B.MN=MN
EngineMachine=Machine
class Machine(EngineMachine):
 KERNAL=EngineMachine.KERNAL|HI.Machine.KERNAL
 def __init__(self,files=None,fault=None):
  super().__init__();self.files['VYHI.DAT']=(ART/'VYHI.DAT').read_bytes()
  if files is not None:
   self.files.pop('VYHI.DAT',None);self.files.update(files)
  self.fault=fault;self.channels={};self.input=None;self.output=None;self.status=0;self.dos=0;self.events=[];self.written=[]
 def trap(self):
  if self.memory.data[0x2100]==8:
   assert self.memory.map_mask==0x80 and self.memory.map_offset==0x30000
   HI.Machine.trap(self)
  else:super().trap()
 def run_to(self,targets,limit=50_000_000):
  targets=set(targets)
  from collections import deque
  trace=deque(maxlen=24)
  for _ in range(limit):
   trace.append((hex(self.cpu.pc),hex(self.cpu.sp),hex(self.memory[self.cpu.pc])))
   if self.cpu.pc not in self.KERNAL and self.cpu.pc!=0x200 and (self.cpu.pc>=0xd000 or self.memory[self.cpu.pc]==0):raise AssertionError(("invalid execution",list(trace),"error",self.error))
   if self.cpu.pc in targets:return self
   if self.cpu.pc==N['enter_menu']:self.memory.watch_title=False;self.memory.title_active=False
   if self.cpu.pc in self.KERNAL:self.trap()
   else:self.cpu.step()
  raise AssertionError(('CPU timeout',hex(self.cpu.pc)))
 def boot(self):return self.run_to([MN['menu_loop'],0x200])
 def menu_frame(self,key=0,joy=255,matrix=255):
  self.memory.key=key;self.memory.data[0xdc00]=joy;self.memory.data[0xd613]=matrix;self.memory.data[0xd60f]=0
  self.cpu.pc=MN['menu_loop'];seen=False
  for _ in range(1000000):
   if self.cpu.pc==0x200 or self.memory.data[0x2100]==8 and self.cpu.pc==HS['main_loop']:return self
   if seen and self.cpu.pc==MN['menu_loop']:return self
   if self.cpu.pc==MN['menu_input']:seen=True
   if self.cpu.pc in self.KERNAL:self.trap()
   else:self.cpu.step()
  raise AssertionError(('Menu frame timeout',hex(self.cpu.pc)))
 def hi_frame(self,key=0,joy=255,matrix=255):
  self.memory.key=key;self.memory.data[0xdc00]=joy;self.memory.data[0xd613]=matrix;self.memory.data[0xd60f]=0
  self.cpu.pc=HS['main_loop'];clock=self.memory.data[HS['band_clock']]
  for _ in range(3000000):
   if self.cpu.pc in (MN['menu_loop'],0x200) or self.memory.data[0x2100]!=8 and self.cpu.pc==N['main_loop']:return self
   if self.memory.data[0x2100]==8 and self.cpu.pc==HS['main_loop'] and self.memory.data[HS['band_clock']]!=clock:return self
   if self.cpu.pc in self.KERNAL:self.trap()
   else:self.cpu.step()
  raise AssertionError(('HS frame timeout',hex(self.cpu.pc)))
 def entries(self):return HI.F.decode(bytes(self.memory.data[HS['hi_table']:HS['hi_table']+592]))
 def finish_ready(self):
  saved_pc=self.cpu.pc
  # Fixture setup executes each real FSM tick; full 50Hz-loop timing is tested separately.
  for _ in range(100):
   if self.memory.data[N['mode']]!=3:break
   self.call_at(N['tick'])
  assert self.memory.data[N['mode']]==0
  self.cpu.pc=saved_pc
  return self
 def game(self,number=1,wait_ready=True):
  self.menu_frame()
  super().game(number)
  return self.finish_ready() if wait_ready else self
 def game_frame(self,key=0,joy=255):
  self.memory.data[0xdc00]=joy;self.cpu.pc=N['main_loop'];sampled=False
  for _ in range(2000000):
   if self.cpu.pc in (MN['menu_loop'],0x200) or self.memory.data[0x2100]==8 and self.cpu.pc==HS['main_loop'] or sampled and self.cpu.pc==N['main_loop']:return self
   if self.cpu.pc==0xffe4:
    sampled=True;self.cpu.a=key;self.cpu.pc=self.cpu.stPopWord()+1
   elif self.cpu.pc in self.KERNAL:self.trap()
   else:self.cpu.step()
  raise AssertionError(('Game frame timeout',hex(self.cpu.pc)))
