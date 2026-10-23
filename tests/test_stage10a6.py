"""Stage10a6 assembled-code checks; py65 model, not hardware or XEMU."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import analyze_attack_descriptors as P
from test_stage10a5 import Flat, namespace, ROOT, RETURN
ART=ROOT/'releases/stage_10a/stage10a6'
SYM=(ART/'STAGE10A6.sym').read_text()
L,A,E,G,S,D,F,AU=[namespace(SYM,n) for n in ('level','attack','entry','game','shots','s3b','fireevents','audio8')]
DATA=(ROOT/'assets/VYLV.DAT').read_bytes()
RECORDS=list(P.parse(DATA))
class Machine(Flat):
 def __init__(self):
  super().__init__((ART/'STAGE10A6.PRG').read_bytes());self.bank=bytearray(65536);self.events=[]
 def call(self,addr,stops=(),limit=200000):
  c=self.cpu;c.sp=255;c.pc=addr;c.stPushWord(RETURN-1)
  for _ in range(limit):
   if c.pc==RETURN or c.pc in stops:return c.pc
   if c.pc==D['dma_copy']:
    m=self.mem
    def val(prefix):return m[D[prefix+'_lo']]+256*m[D[prefix+'_hi']]+65536*m[D[prefix+'_bank']]
    src,dst=val('dma_src'),val('dma_dst');n=m[D['dma_len_lo']]+256*m[D['dma_len_hi']]
    for i in range(n):
     a=src+i;b=dst+i
     v=DATA[a-0x40000] if 0x40000<=a<0x40000+len(DATA) else self.bank[a-0x10000] if 0x10000<=a<0x20000 else m[a]
     if 0x10000<=b<0x20000:self.bank[b-0x10000]=v
     else:m[b]=v
    c.pc=c.stPopWord()+1
   elif c.pc in (AU['attack'],F['attack_plan'],F['attack_tick']):
    self.events.append(c.pc);c.pc=c.stPopWord()+1
   else:c.step()
  raise AssertionError(('routine did not return',hex(c.pc)))
 def level(self,n):
  self.mem[L['number']]=n;self.call(L['load_record']);return self
 def xy(self,i):
  return tuple(int.from_bytes(bytes((self.mem[E[lo]+i],self.mem[E[hi]+i])),'little',signed=True) for lo,hi in [('e_xlo','e_xhi'),('e_ylo','e_yhi')])
 def fixture(self,n):
  self.level(n);m=self.mem;_,_,_,enemies,curves=RECORDS[n-1];shift=min(e[1] for e in enemies)
  m[A['a_curve_count']]=len(curves);ptr=0x3000
  for j,b in enumerate(curves):
   m[A['a_ptrlo']+j]=ptr&255;m[A['a_ptrhi']+j]=ptr>>8;m[A['a_length']+j]=len(b);self.bank[ptr:ptr+len(b)]=b;ptr+=len(b)
  for i,(x,y,g,index) in enumerate(enemies):
   m[A['a_index']+i]=index;m[E['e_tx']+i]=x;m[E['e_ty']+i]=y-shift
   m[E['e_xlo']+i]=x;m[E['e_ylo']+i]=y-shift;m[E['e_phase']+i]=3;m[G['c_es']+i]=1
  m[A['a_enabled']]=m[A['a_ready']]=1;m[G['c_ps']]=0
  return enemies,curves
class SpecialAttacks(unittest.TestCase):
 def test_all_100_headers_enable_attacks(self):
  for n in range(1,101):
   m=Machine().level(n);self.assertEqual(m.mem[L['attack_allowed']],1,n);self.assertFalse(m.cpu.p&1,n)
 def test_scheduler_starts_without_bypassing_ban_then_caps_at_three(self):
  for n in (25,50,99,100):
   m=Machine();m.fixture(n);d=m.mem
   for _ in range(300):m.call(A['a_postframe'])
   self.assertEqual(sum(d[G['c_es']+i]==3 for i in range(22)),3,n)
   self.assertEqual(m.events.count(AU['attack']),3);self.assertEqual(m.events.count(F['attack_plan']),3)
   for i in range(22):self.assertEqual(d[E['e_phase']+i],4 if d[G['c_es']+i]==3 else 3)
 def test_respawn_and_transition_still_block_new_starts(self):
  for n in (25,50,99,100):
   for state in (1,2,3):
    m=Machine();m.fixture(n);d=m.mem;d[G['c_ps']]=state;d[G['c_respawn']]=255
    for _ in range(120):m.call(A['a_postframe'])
    self.assertNotIn(AU['attack'],m.events,(n,state))
   m=Machine();m.fixture(n);m.mem[L['mode']]=2
   for _ in range(120):m.call(A['a_postframe'])
   self.assertNotIn(AU['attack'],m.events,n)
 def test_all_88_actors_exact_points_bottom_and_return(self):
  results=[]
  for n in (25,50,99,100):
   m=Machine();enemies,curves=m.fixture(n);counts=[]
   for i,(_,_,_,index) in enumerate(enemies):
    d=m.mem;m.cpu.x=i;m.call(A['a_start']);x,y=m.xy(i);count=0;before=len(m.events)
    while y<200:
     dx,dy=P.decode(curves[index][count%len(curves[index])]);x+=dx;y+=dy;count+=1
     m.cpu.x=i;m.call(A['a_step']);self.assertEqual(m.xy(i),(x,y),(n,i,count))
     self.assertEqual(d[E['e_phase']+i],5 if y>=200 else 4);self.assertLess(count,350)
    self.assertEqual(m.events[before:].count(F['attack_tick']),count)
    self.assertNotIn(AU['attack'],m.events[before:]);self.assertNotIn(F['attack_plan'],m.events[before:])
    m.cpu.x=i;m.call(A['a_step']);self.assertEqual(m.xy(i),(x,-16));self.assertEqual(d[E['e_phase']+i],2)
    for _ in range(600):
     if d[E['e_phase']+i]==3:break
     m.cpu.x=i;m.call(E['e_return'])
    self.assertEqual(d[E['e_phase']+i],3);self.assertEqual(m.xy(i),(d[E['e_tx']+i],d[E['e_ty']+i]));counts.append(count)
   results.append((n,len(enemies),min(counts),max(counts)))
  print('Exact assembled trajectories (level, actors, min/max points):',results)
if __name__=='__main__':unittest.main()
