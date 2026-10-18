"""Stage10a1 actual assembled phase/score code; constrained models, not XEMU."""
import copy,hashlib,json,re,unittest,os
from pathlib import Path
from py65.devices.mpu6502 import MPU
import test_stage9c2 as OLD
import highscore_format as F
import d81_highscore as DISK
ROOT=Path(__file__).resolve().parents[1];ART=Path(os.getenv('STAGE10A1_ARTIFACTS',str(ROOT/'releases/stage_10a/stage10a1'))).resolve()
N={n:int(v,16) for n,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',(ART/'highscore.sym').read_text())}
class Table(OLD.Machine):
 def __init__(self,reason=0,score=0,entries=None,files=None,fault=None):
  self.files={'VYHI.DAT':F.encode(entries or [])} if files is None else files
  self.fault=fault;self.channels={};self.input=None;self.output=None;self.status=0;self.dos=0;self.events=[];self.written=[];self.memory=OLD.Memory()
  p=(ART/'HIGHSCORE.PRG').read_bytes();self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
  self.memory.data[0x1fe9]=0;self.memory.data[0x1fe4]=reason;self.memory.data[0x1fe0:0x1fe4]=score.to_bytes(4,'little')
  self.cpu=MPU(memory=self.memory);self.cpu.pc=N['entry'];self.cpu.sp=0xfd;self.cpu.stPushWord(0x1ff)
  self.run_to((N['main_loop'],0x1923))
 def call(self,name):self.cpu.pc=N[name];self.cpu.stPushWord(0x1ff);return self.run_to((0x200,))
 def frame(self,key=None,joy=255,enter=False):
  if key is not None:self.memory.events.append(key)
  self.memory.joy=joy;self.memory.enter=enter;self.memory.edges=[250,250,251]
  self.cpu.pc=N['main_loop'];clock=self.memory.data[N['band_clock']]
  for _ in range(3000000):
   if self.cpu.pc==0x1923 or self.cpu.pc==N['main_loop'] and self.memory.data[N['band_clock']]!=clock:return self
   self.step()
  raise AssertionError(('HS frame',hex(self.cpu.pc)))
 def packet(self):return bytes(self.memory.data[N['hi_table']:N['hi_table']+592])
 def save(self,name):
  self.frame()
  for c in name:self.frame(ord(c))
  self.frame(13,enter=True)
class TableIntegration(unittest.TestCase):
 def test_boot_validates_without_showing_or_writing(self):
  m=Table(2,entries=[(b'OLD',12)]);self.assertEqual(m.cpu.pc,0x1923);self.assertEqual(m.memory.data[0x1fea:0x1fee],bytes((12,0,0,0)));self.assertEqual(m.written,[]);self.assertEqual(m.channels,{})
 def test_game_score_equal_first_equal_last_and_unsigned_boundaries(self):
  fixtures=[([],0),([],0xffffffff),([(b'AAA',20),(b'BBB',10),(b'CCC',10)],10),([(f'A{i:02d}'.encode(),5) for i in range(80)],5),([(b'OLD',100-i) for i in range(80)],21)]
  for entries,score in fixtures:
   m=Table(1,score,entries);self.assertEqual(m.memory.data[N['hi_mode']],2);m.save('NEW');self.assertEqual(m.entries(),F.insert(entries,b'NEW',score));self.assertEqual(F.decode(m.files['VYHI.DAT']),m.entries());self.assertEqual(m.channels,{})
   after=dict(m.files)
   for _ in range(4):
    m.frame(13,enter=True);self.assertEqual(m.cpu.pc,N['main_loop'])
   self.assertEqual(m.files,after)
   m.frame();m.frame(13);self.assertEqual(m.cpu.pc,0x1923)
   reload=Table(0,files=m.files);self.assertEqual(reload.entries(),m.entries())
 def test_nonqualification_and_cancel_never_write(self):
  entries=[(b'OLD',100-i) for i in range(80)];m=Table(1,20,entries);self.assertEqual(m.cpu.pc,0x1923);self.assertEqual(m.written,[])
  m=Table(1,500,entries);before=dict(m.files);m.frame();m.frame(ord('A'));m.frame(27);self.assertEqual(m.cpu.pc,0x1923);self.assertEqual(m.files,before)
 def test_table_any_key_exits_to_menu_and_x_requests_basic_no_simulator(self):
  for key in (13,83,65,0x86):
   m=Table();m.frame();m.frame(key);self.assertEqual(m.cpu.pc,0x1923);self.assertEqual(m.memory.data[0x1fe9],0);self.assertEqual(m.written,[])
  m=Table();m.frame();m.frame(88);self.assertEqual(m.memory.data[0x1fe9],1)
 def test_input_edit_error_feedback_and_protected_recovery(self):
  for fault in ('wp','full','promote'):
   m=Table(1,20,[(b'OLD',10)],fault=fault);m.save('NEW');self.assertEqual(m.entries(),[(b'OLD',10)]);self.assertEqual(m.memory.data[N['hi_blocked']],1);self.assertEqual(m.channels,{})
  packet=bytearray(F.encode([(b'OLD',10)]));packet[100]^=1
  m=Table(1,20,files={'VYHI.DAT':bytes(packet),'VYHI.BAK':F.encode([(b'BAK',9)])});before=dict(m.files);m.save('NEW');self.assertEqual(m.files,before);self.assertEqual(m.memory.data[N['hi_blocked']],1)
 def test_four_pages_frames_colours_and_separate_resident_gates(self):
  m=Table(entries=[(b'ABC',0xffffffff-i) for i in range(80)])
  for page in range(4):
   m.frame()
   for y in range(2,23):
    for x in (4,75):self.assertEqual(m.memory.data[0x7000+80*y+x],129)
   for row in range(10):
    phase=m.memory.data[N['band_phase']];expected=3+(row+phase)%3
    for x in (16,49):self.assertEqual(bytes(m.memory.colour[0x2000+80*(7+row)+x:0x2000+80*(7+row)+x+18]),bytes([expected])*18)
   if page<3:m.frame(29);m.frame()
  self.assertEqual(m.memory.data[N['page']],3)
 def test_d81_nine_assets_chains_bam_and_original_audio(self):
  report=json.loads((ART/'build-report.json').read_text());entries=[]
  for f in report['files']:
   payload=(ART/('STAGE10A1.PRG' if f['name']=='STAGE10A1' else f['name'])).read_bytes();entries.append((f['name'],payload,0x82 if f['name']=='STAGE10A1' else 0x81))
  self.assertEqual(len(entries),10);DISK.verify_disk((ART/'VYPER_STAGE10A1.d81').read_bytes(),entries)
  for name in ('VYLV.DAT','VYGR.DAT','VYCL.DAT','VYSH.DAT','VYSO.DAT','VYTI.DAT','AUDIO_CORE.PRG'):
   reference=ROOT/'releases/stage_9b1'
   if 'hardware_reference' in report and name in ('VYSO.DAT','AUDIO_CORE.PRG'):
    reference=ROOT/'releases/stage_10a/stage10a1_hw'
   self.assertEqual((ART/name).read_bytes(),(reference/name).read_bytes(),name)

class Presentation(unittest.TestCase):
 def test_fixed_yellow_text_clean_normal_rows_and_cycling_frame(self):
  hint='CURSOR / JOYSTICK LEFT-RIGHT: CHANGE PAGE'
  title='- VYPER HIGH SCORE TABLE -';footer='- PRESS A KEY OR JOYSTICK BUTTON TO CONTINUE -'
  for files in ({'VYHI.DAT':F.encode([])},{}):
   m=Table(files=files);m.frame()
   initial=bytes(m.memory.banks[1][c][2] for c in range(3))
   for _ in range(16):m.frame()
   self.assertNotEqual(initial,bytes(m.memory.banks[1][c][2] for c in range(3)))
   for text,y in ((title,3),(hint,18),(footer,21)):
    x=(80-len(text))//2;self.assertGreater(x,4);self.assertLess(x+len(text),75)
    self.assertEqual(bytes(m.memory.data[0x7000+y*80+x:0x7000+y*80+x+len(text)]),bytes(ord(c)-64 if 64<=ord(c)<=95 else ord(c) for c in text))
    self.assertEqual(bytes(m.memory.colour[0x2000+y*80+x:0x2000+y*80+x+len(text)]),bytes([4])*len(text))
   for y in (17,19):self.assertEqual(bytes(m.memory.data[0x7000+y*80+5:0x7000+y*80+75]),bytes([32])*70)
   self.assertEqual(bytes(m.memory.banks[1][c][4] for c in range(3)),bytes((255,255,0)))
 def test_only_real_file_errors_show_diagnostics_and_success_is_clean(self):
  p=bytearray(F.encode([]));p[100]^=1;m=Table(files={'VYHI.DAT':bytes(p)});m.frame()
  self.assertEqual(m.memory.data[N['hi_blocked']],1)
  self.assertNotEqual(bytes(m.memory.data[0x7000+17*80+6:0x7000+17*80+20]),bytes([32])*14)
  self.assertNotEqual(bytes(m.memory.data[0x7000+19*80+6:0x7000+19*80+20]),bytes([32])*14)
  m=Table(1,50);m.save('NEW');self.assertEqual(F.decode(m.files['VYHI.DAT']),[(b'NEW',50)])
  for y in (17,19):self.assertEqual(bytes(m.memory.data[0x7000+y*80+5:0x7000+y*80+75]),bytes([32])*70)

class NavigationModes(unittest.TestCase):
 def assert_hint(self,m,visible):
  row=bytes(m.memory.data[0x7000+18*80+5:0x7000+18*80+75])
  colour=bytes(m.memory.colour[0x2000+18*80+5:0x2000+18*80+75])
  expected=bytearray([32]*70);fg=bytearray([1]*70)
  if visible:
   text='CURSOR / JOYSTICK LEFT-RIGHT: CHANGE PAGE'
   expected[14:55]=bytes(ord(c)-64 if 64<=ord(c)<=95 else ord(c) for c in text)
   fg[14:55]=bytes([4])*41
  self.assertEqual(row,bytes(expected));self.assertEqual(colour,bytes(fg))
  for x in (4,75):
   self.assertEqual(m.memory.data[0x7000+18*80+x],129)
   self.assertEqual(m.memory.colour[0x2000+18*80+x],2)
 def test_initial_name_frame_and_repeated_table_name_save_cancel_transitions(self):
  m=Table(1,100)
  # Constructor stops at the first displayed frame, before any input/raster tick.
  self.assertEqual(m.memory.data[N['hi_mode']],2);self.assert_hint(m,False)
  for _ in range(16):m.frame();self.assert_hint(m,False)
  m.save('AAA');self.assert_hint(m,True)
  self.assertEqual(m.entries(),[(b'AAA',100)])
  for name,score in (('BBB',100),('CCC',200)):
   m.memory.data[0x1fe4]=1
   m.memory.data[N['hi_score']:N['hi_score']+4]=score.to_bytes(4,'little')
   m.call('hs_game_name');m.call('page_draw');self.assert_hint(m,False)
   m.save(name);self.assert_hint(m,True)
  expected=[(b'CCC',200),(b'BBB',100),(b'AAA',100)]
  self.assertEqual(F.decode(m.files['VYHI.DAT']),expected)
  before=dict(m.files);m.call('hs_game_name');m.call('page_draw');self.assert_hint(m,False)
  m.frame();m.frame(ord('Z'));m.frame(27)
  self.assertEqual(m.files,before);self.assertEqual(m.cpu.pc,0x1923)
  reopened=Table(files=m.files);self.assert_hint(reopened,True)
  reopened.frame();reopened.frame(29);reopened.frame()
  self.assertEqual(reopened.memory.data[N['page']],1);self.assert_hint(reopened,True)

if __name__=='__main__':unittest.main()
