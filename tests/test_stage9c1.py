"""Execute the standalone assembled6502 subset; constrained VIC/DMA model, not XEMU."""
import hashlib,json,re,tempfile,unittest
from pathlib import Path
from py65.devices.mpu6502 import MPU
import test_stage5d0 as OLD
import build_stage9c1 as BUILD
import build_stage3b1 as DISK
ROOT=BUILD.ROOT;ART=ROOT/'releases/stage_9c1'
N={n:int(v,16) for n,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',(ART/'STAGE9C1.sym').read_text())}
class Memory(OLD.Memory):
 def __init__(self):
  super().__init__();self.wom=bytes((i*17+i//8)&255 for i in range(4096));self.raster=251;self.edges=[];self.right=False;self.left=False;self.joy=255;self.cpu=None
 def __getitem__(self,a):
  if 0xff7e000<=a<0xff7f000:return self.wom[a-0xff7e000]
  if a==0xd619:return self.events[0] if self.events else 255
  if a==0xd613:return 251 if self.right or self.left else 255
  if a==0xd60f:return int(self.left)
  if a==0xdc00:
   return (self.joy&~self.data[0xdc02])|(self.data[0xdc00]&self.data[0xdc02])
  if a==0xd012:
   if self.edges:self.raster=self.edges.pop(0)
   return self.raster
  return super().__getitem__(a)
 def __setitem__(self,a,v):
  if a==0xd619:
   if self.events:self.events.pop(0)
   return
  return super().__setitem__(a,v)
class Machine:
 def __init__(self,irq=False,mode=0xc0,compare=0,decimal=False):
  self.memory=Memory();self.memory.data[0xd031]=mode;self.memory.data[0xd011]=0x1b|(compare<<7);self.memory.data[0xd07a]=0x10|compare
  p=(ART/'STAGE9C1.PRG').read_bytes();self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
  self.cpu=MPU(memory=self.memory);self.cpu.p=0x20|(4 if irq else 0)|(8 if decimal else 0)
  self.before=bytes(self.memory.data);self.before_colour=bytes(self.memory.colour);self.before_banks=[[bytes(c) for c in b] for b in self.memory.banks]
  self.status=self.cpu.p;self.restart()
 def restart(self):
  self.cpu.pc=N['entry'];self.cpu.sp=0xfd;self.cpu.stPushWord(0x1ff)
  return self.run_to((N['main_loop'],))
 def run_to(self,targets,limit=100000):
  for _ in range(limit):
   if self.cpu.pc in targets:return self
   assert self.cpu.pc<0xd000 or self.cpu.pc==0x200,('unexpected KERNAL/ROM call',hex(self.cpu.pc))
   self.cpu.step()
  raise AssertionError(('did not reach target',hex(self.cpu.pc)))
 def call(self,name):
  self.cpu.pc=N[name];self.cpu.stPushWord(0x1ff);return self.run_to((0x200,))
 def frame(self,key=None,left=False,right=False,joy=255):
  if key is not None:self.memory.events.append(key)
  self.memory.left=left;self.memory.right=right;self.memory.joy=joy;self.memory.edges=[250,250,251]
  self.cpu.pc=N['main_loop'];clock=self.memory.data[N['band_clock']]
  for _ in range(100000):
   if self.cpu.pc==0x200 or self.cpu.pc==N['main_loop'] and self.memory.data[N['band_clock']]!=clock:return self
   self.cpu.step()
  raise AssertionError('Frame edge was not serviced')
 def restored(self,test):
  d=self.memory.data
  for r in self.before[N['title_regs']:N['title_saved_compare_bit']]:test.assertEqual(d[0xd000+r],self.before[0xd000+r],f'VIC{r:02x}')
  test.assertEqual(d[0xd614],self.before[0xd614]);test.assertEqual(d[0xdc02],self.before[0xdc02])
  test.assertEqual(bytes(self.memory.colour),self.before_colour)
  test.assertEqual([[bytes(c) for c in b] for b in self.memory.banks],self.before_banks)
  test.assertEqual(self.cpu.p&12,self.status&12);test.assertEqual(self.cpu.sp,0xfd)
  for lo,hi in ((0,0x100),(0x200,0x2000),(0x10000,0x12000),(0x1f800,0x40000)):
   test.assertEqual(bytes(d[lo:hi]),self.before[lo:hi],hex(lo))
  test.assertEqual(self.memory.events,[])
class Highscores(unittest.TestCase):
 def test_all80_test_records_and_single_file_disk(self):
  pages,colours,frame,entries=BUILD.assets()
  self.assertEqual([e['rank'] for e in entries],list(range(1,81)))
  self.assertTrue(all(a['score']>b['score'] for a,b in zip(entries,entries[1:])))
  self.assertEqual(entries[-1]['score'],0);self.assertTrue(any('@' in e['name'] for e in entries));self.assertTrue(all(len(e['name'])==3 for e in entries))
  self.assertEqual((ART/'pages.bin').read_bytes(),b''.join(pages));self.assertEqual((ART/'colours.bin').read_bytes(),colours);self.assertEqual((ART/'frame.bin').read_bytes(),frame)
  self.assertEqual(json.loads((ART/'test-entries.json').read_text()),entries)
  DISK.verify_disk((ART/'VYPER_STAGE9C1.d81').read_bytes(),[('STAGE9C1',(ART/'STAGE9C1.PRG').read_bytes(),0x82)])
  self.assertEqual((ART/'VYPER_STAGE9C1.d81').stat().st_size,819200)
 def test_full_entry_private_font_and_80_column_mode(self):
  m=Machine();d=m.memory.data;pages,_,frame,_=BUILD.assets()
  self.assertEqual(bytes(d[0x7000:0x77d0]),pages[0]);self.assertEqual(d[0xd054],0)
  self.assertEqual(d[0xd031],(m.before[0xd031]&0x40)|0x80)
  self.assertEqual(d[0xd058:0xd05a],bytes((80,0)));self.assertEqual(d[0xd05e],80);self.assertEqual(d[0xd07b],24)
  self.assertNotIn(int.from_bytes(d[0xd068:0xd06b],'little'),(0x1000,0x1800,0x9000,0x9800)) # VIC fetch aliases WOM, not RAM, at these bases
  self.assertEqual(d[0xd068:0xd06b],bytes((0,0x80,0)));self.assertEqual(d[0xd060:0xd064],bytes((0,0x70,0,0)))
  self.assertEqual(d[0x8000:0x8400],m.memory.wom[:1024]);self.assertEqual(d[0x8400:0x8430],frame);self.assertEqual(d[0x8430:0x8800],m.memory.wom[1072:2048])
  self.assertEqual(d[0xd064:0xd066],bytes((0,0x20)));self.assertEqual(d[0xd015],0);self.assertTrue(m.cpu.p&4)
  self.assertEqual(d[0xd05d]&128,0);self.assertEqual(d[0xdc02]&31,0)
 def test_four_pages_rank_positions_exact_words_no_residue(self):
  m=Machine();d=m.memory.data;pages,_,_,entries=BUILD.assets()
  encode=lambda s:bytes(BUILD.screen_code(c) for c in s)
  for page in range(4):
   for _ in range(page-int(d[N['page']])):m.frame(29,right=True);m.frame()
   self.assertEqual(bytes(d[0x7000:0x77d0]),pages[page])
   for col,x in enumerate(BUILD.COLS):
    for row,y in enumerate(BUILD.ROWS):
     e=entries[20*page+10*col+row];text=f"{e['rank']:02d}: {e['name']} {e['score']:7d}"
     self.assertEqual(bytes(d[0x7000+80*y+x:0x7000+80*y+x+15]),encode(text))
   for text,y in ((BUILD.TITLE,3),(BUILD.FOOTER,21)):
    x=(80-len(text))//2;self.assertEqual(bytes(d[0x7000+80*y+x:0x7000+80*y+x+len(text)]),encode(text))
  for _ in range(5):m.frame(29,right=True);m.frame()
  self.assertEqual(d[N['page']],3)
  for _ in range(5):m.frame(157,left=True);m.frame()
  self.assertEqual(d[N['page']],0);self.assertEqual(bytes(d[0x7000:0x77d0]),pages[0])
 def test_keyboard_typematic_held_latch_and_fast_taps(self):
  m=Machine();d=m.memory.data
  for _ in range(50):m.frame(29,right=True)
  self.assertEqual(d[N['page']],1)
  m.frame();m.frame(29,right=True);self.assertEqual(d[N['page']],2)
  m.frame();m.frame(157,left=True);self.assertEqual(d[N['page']],1)
  # FIFO-only quick taps between frame samples also work.
  m.frame();m.frame(29);self.assertEqual(d[N['page']],2)
  m.frame(29);self.assertEqual(d[N['page']],3)
 def test_joystick_port2_neutral_edges_bounds_and_fire(self):
  m=Machine();d=m.memory.data
  for _ in range(40):m.frame(joy=0xf7)
  self.assertEqual(d[N['page']],1)
  m.frame();m.frame(joy=0xf7);self.assertEqual(d[N['page']],2)
  m.frame();m.frame(joy=0xfb);self.assertEqual(d[N['page']],1)
  m.frame();m.frame(joy=0xf3);self.assertEqual(d[N['page']],1) # both directions
  m.frame();m.frame(joy=0xef);self.assertEqual(m.cpu.pc,0x200);m.restored(self)
 def test_frame_title_footer_cycle_exact_existing_algorithm(self):
  self.assertEqual((ROOT/'src/tests/stage9c1_cycling.asm').read_bytes(),(ROOT/'src/engine/stage9b1_cycling.asm').read_bytes())
  m=Machine();d=m.memory.data;word=0xec;phase=2;left=1;delta=(0x20,-0x200,2,-0x20,0x200,-2)
  screen=bytes(d[0x7000:0x77d0])
  for tick in range(1,127):
   word=(word+delta[phase])&65535;left-=1
   if not left:phase=(phase+1)%6;left=7
   m.frame()
   self.assertEqual(int.from_bytes(d[N['cc_word']:N['cc_word']+2],'little'),word)
   self.assertEqual([m.memory.banks[1][c][2] for c in range(3)],[((word>>s)&15)*17 for s in (8,4,0)])
   self.assertEqual(bytes(d[0x7000:0x77d0]),screen)
  for index in (80+4,3*80+27,21*80+18):self.assertEqual(m.memory.colour[0x2000+index],2)
 def test_blue_yellow_red_bands_move_up_in_both_columns_without_reset(self):
  m=Machine();d=m.memory.data;initial=bytes(m.memory.colour)
  for tick in range(1,193):
   if tick in (27,71,121):m.frame(29,right=True)
   else:m.frame()
   phase=(tick//8)%12;self.assertEqual(d[N['band_phase']],phase)
   for row,y in enumerate(BUILD.ROWS):
    expected=3+(((row+phase)%12)//4)
    for x in BUILD.COLS:self.assertEqual(bytes(m.memory.colour[0x2000+80*y+x:0x2000+80*y+x+15]),bytes([expected]*15))
   for y in (1,3,21,23):self.assertEqual(bytes(m.memory.colour[0x2000+80*y:0x2000+80*(y+1)]),initial[0x2000+80*y:0x2000+80*(y+1)])
  self.assertEqual(d[N['page']],3)
 def test_any_other_key_return_X_and_held_fire_entry_clean_exit_twice(self):
  for key in (13,88,120,65,32,17,255):
   for irq,mode,compare,decimal in ((False,0xc0,0,False),(True,0x40,1,True)):
    m=Machine(irq=irq,mode=mode,compare=compare,decimal=decimal)
    for repeat in range(2):
     m.frame();m.frame(key);self.assertEqual(m.cpu.pc,0x200);m.restored(self)
     if repeat==0:m.restart()
  m=Machine();m.frame(joy=0xef);self.assertEqual(m.cpu.pc,N['main_loop']) # held trigger at entry ignored
  m.frame();m.frame(joy=0xef);self.assertEqual(m.cpu.pc,0x200)
 def test_waits_once_for_raster_edge_and_bounded_work(self):
  m=Machine();d=m.memory.data;phase=d[N['cc_phase']];word=bytes(d[N['cc_word']:N['cc_word']+2])
  m.memory.raster=250;m.cpu.pc=N['main_loop']
  for _ in range(500):m.cpu.step()
  self.assertEqual(bytes(d[N['cc_word']:N['cc_word']+2]),word)
  m.memory.raster=251
  for _ in range(10000):
   m.cpu.step()
   if m.cpu.pc==N['main_loop'] and bytes(d[N['cc_word']:N['cc_word']+2])!=word:break
  self.assertNotEqual(bytes(d[N['cc_word']:N['cc_word']+2]),word)
  costs=[];dma=[]
  for _ in range(96):
   before=m.cpu.processorCycles;n=len(m.memory.transfers);m.frame();costs.append(m.cpu.processorCycles-before);dma.append(sum(t[2] for t in m.memory.transfers[n:]))
  self.assertLess(max(costs),13000);self.assertEqual(max(dma),2000)
  print('Host instruction-model max cycles/frame (DMA latency excluded):',max(costs),'max DMA bytes/frame:',max(dma),flush=True)
 def test_X_exits_even_when_no_animation_frame_is_due(self):
  m=Machine();m.memory.raster=77;m.memory.events.append(88);m.cpu.pc=N['main_loop']
  m.run_to((0x200,));m.restored(self)
 def test_all_DMA_ranges_memory_boundaries_and_no_engine_assets(self):
  m=Machine();m.frame();m.frame(29,right=True);m.frame();m.frame(88)
  allowed=((0x7000,0x77d0),(0x8000,0x8800),(0x15000,0x157d0),(0xff82000,0xff827d0))
  for src,dst,n in m.memory.transfers:self.assertTrue(any(lo<=dst and dst+n<=hi for lo,hi in allowed),(hex(dst),n))
  for n in ('VYHI.DAT','VYLV.DAT','VYSO.DAT'):self.assertFalse((ART/n).exists())
  source=(ROOT/'src/tests/stage9c1.asm').read_text();self.assertNotIn('$ffbd',source.lower());self.assertNotIn('stage9b1_',source)
if __name__=='__main__':unittest.main()
