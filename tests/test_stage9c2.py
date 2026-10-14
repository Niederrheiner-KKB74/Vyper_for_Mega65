"""Execute actual assembled manager/KERNAL calls against a constrained persistent DOS model."""
import base64,hashlib,json,re,struct,unittest
from pathlib import Path
from py65.devices.mpu6502 import MPU
import test_stage9c1 as OLD
import highscore_format as F
import build_stage9c2 as BUILD
ART=BUILD.ROOT/'releases/stage_9c2'
N={n:int(v,16) for n,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',(ART/'STAGE9C2.sym').read_text())}
class PowerLoss(Exception):pass
class Memory(OLD.Memory):
 def __init__(self):super().__init__();self.enter=False
 def __getitem__(self,a):
  if a==0xd613:return (251 if self.right or self.left else 255)&(253 if self.enter else 255)
  return super().__getitem__(a)
class Machine:
 KERNAL={0xffba,0xff6b,0xffbd,0xffc0,0xffc6,0xffc9,0xffcf,0xffd2,0xffb7,0xffcc,0xffc3}
 def __init__(self,files=None,fault=None,irq=False,mode=0xc0):
  self.files={'VYHI.DAT':(ART/'VYHI.DAT').read_bytes()} if files is None else files
  self.fault=fault;self.channels={};self.input=None;self.output=None;self.status=0;self.dos=0;self.events=[];self.written=[];self.memory=Memory()
  self.memory.data[0xd031]=mode
  p=(ART/'STAGE9C2.PRG').read_bytes();self.memory.data[0x2001:0x2001+len(p)-2]=p[2:]
  self.cpu=MPU(memory=self.memory);self.cpu.p=0x24 if irq else 0x20
  self.before=bytes(self.memory.data);self.before_colour=bytes(self.memory.colour);self.before_banks=[[bytes(c) for c in b] for b in self.memory.banks];self.status_before=self.cpu.p
  self.cpu.pc=N['entry'];self.cpu.sp=0xfd;self.cpu.stPushWord(0x1ff);self.run_to((N['main_loop'],))
 def trap(self):
  c=self.cpu;a=c.pc;incoming_carry=bool(c.p&c.CARRY);c.p&=~c.CARRY
  assert not c.p&4,('KERNAL with IRQ disabled',hex(a))
  if a==0xffba:self.lfn=c.a;self.device=c.x;self.secondary=c.y;self.banked=False
  elif a==0xff6b:assert c.a==c.x==0;self.banked=True
  elif a==0xffbd:
   assert self.banked
   self.name=bytes(self.memory.data[c.x+256*c.y:c.x+256*c.y+c.a]).decode('ascii')
  elif a==0xffc0:
   if self.fault=='device':
    self.dos=74;c.p|=1;c.pc=c.stPopWord()+1;return
   if self.lfn==15:
    command=self.name
    if command:
     self.events.append(command)
     if self.fault=='wp':self.dos=26
     elif self.fault=='promote' and command.startswith('R0:VYHI.DAT'):self.dos=74
     elif command.startswith('S0:'):
      n=command[3:];self.dos=1 if n in self.files else 62;self.files.pop(n,None)
     elif command.startswith('R0:'):
      dst,src=command[3:].split('=')
      if dst in self.files:self.dos=63
      elif src not in self.files:self.dos=62
      else:
       self.files[dst]=self.files.pop(src);self.dos=0
       if self.fault=='power-after-backup' and dst=='VYHI.BAK':raise PowerLoss()
     else:raise AssertionError(command)
    self.channels[15]={'data':f'{self.dos:02d},STATUS,00,00\r'.encode(),'pos':0,'read':True}
   else:
    assert self.lfn==2
    name,*parts=self.name.split(',');name=name.removeprefix('0:');writing=parts[-1]=='W'
    if not writing and self.fault=='read-open':self.dos=74;c.p|=1;c.pc=c.stPopWord()+1;return
    if writing:
     if self.fault=='write-open':self.dos=74;c.p|=1
     elif self.fault=='wp':self.dos=26;c.p|=1
     elif name in self.files:self.dos=63;c.p|=1
     else:self.dos=0;self.channels[2]={'data':bytearray(),'name':name,'read':False}
    elif name not in self.files:self.dos=62;c.p|=1
    else:self.dos=0;self.channels[2]={'data':self.files[name],'pos':0,'read':True}
  elif a==0xffc6:
   if c.x not in self.channels or c.x==2 and self.fault=='read-chkin':c.p|=1
   else:self.input=c.x;self.output=None;self.status=0
  elif a==0xffc9:
   if c.x not in self.channels or self.fault=='write-chkout':c.p|=1
   else:self.output=c.x;self.input=None;self.status=0
  elif a==0xffcf:
   assert self.input in self.channels
   ch=self.channels[self.input];p=ch['pos'];data=ch['data'];c.a=data[p] if p<len(data) else 0;ch['pos']+=1;self.status=64 if ch['pos']>=len(data) else 0
   if self.input==2 and self.fault=='read-timeout':self.status=2
  elif a==0xffd2:
   assert self.output==2 and self.input is None,'unexpected screen CHROUT or open input channel'
   ch=self.channels[2]
   if self.fault=='full' and len(ch['data'])>=140:self.status=2;self.dos=72
   else:
    ch['data'].append(c.a);self.status=64 if self.fault=='output-eof' else 0
    if self.fault=='write-carry':c.p|=1
  elif a==0xffb7:c.a=self.status
  elif a==0xffcc:self.input=self.output=None
  elif a==0xffc3:
   if c.a==15:
    assert incoming_carry, 'CLOSE15 without SEC would close other DOS channels (MEGA65 KERNAL contract)'
   elif c.a==2:assert not incoming_carry, 'CLOSE2 must send normal DOS CLOSE and flush data'
   ch=self.channels.pop(c.a,None)
   if ch and not ch['read']:
    data=bytes(ch['data'])
    if self.fault=='truncate':data=data[:200]
    if self.fault=='corrupt':data=data[:-1]+bytes([data[-1]^1])
    self.files[ch['name']]=data;self.written.append(ch['name'])
    if self.dos!=72:self.dos=0
  c.pc=c.stPopWord()+1
 def step(self):
  if self.cpu.pc in self.KERNAL:self.trap()
  else:self.cpu.step()
 def run_to(self,targets,limit=5000000):
  for _ in range(limit):
   if self.cpu.pc in targets:return self
   self.step()
  raise AssertionError(('CPU timeout',hex(self.cpu.pc)))
 def call(self,name):
  self.cpu.pc=N[name];self.cpu.stPushWord(0x1ff);return self.run_to((0x200,))
 def frame(self,key=None,left=False,right=False,joy=255,enter=False):
  if key is not None:self.memory.events.append(key)
  self.memory.left=left;self.memory.right=right;self.memory.joy=joy;self.memory.enter=enter;self.memory.edges=[250,250,251]
  self.cpu.pc=N['main_loop'];clock=self.memory.data[N['band_clock']]
  for _ in range(5000000):
   if self.cpu.pc==0x200 or self.cpu.pc==N['main_loop'] and self.memory.data[N['band_clock']]!=clock:return self
   self.step()
  raise AssertionError(('Frame timeout',hex(self.cpu.pc)))
 def packet(self):return bytes(self.memory.data[N['hi_table']:N['hi_table']+592])
 def entries(self):return F.decode(self.packet())
 def set_entries(self,entries):self.memory.data[N['hi_table']:N['hi_table']+592]=F.encode(entries)
 def candidate(self,name,score):
  self.memory.data[N['hi_name']:N['hi_name']+3]=name;self.memory.data[N['hi_score']:N['hi_score']+4]=score.to_bytes(4,'little')
 def insert(self,name,score):self.candidate(name,score);self.call('hi_insert');self.call('hi_seal');return self.entries()
 def submit(self,score,name='NEW'):
  self.frame(83)
  for c in str(score):self.frame(ord(c))
  self.frame(13,enter=True);self.frame()
  for c in name:self.frame(ord(c))
  self.frame(13,enter=True)
 def restored(self,test):
  d=self.memory.data
  for r in self.before[N['title_regs']:N['title_saved_compare_bit']]:test.assertEqual(d[0xd000+r],self.before[0xd000+r],hex(r))
  test.assertEqual(bytes(self.memory.colour),self.before_colour);test.assertEqual([[bytes(c) for c in b] for b in self.memory.banks],self.before_banks)
  test.assertEqual(d[0xdc02],self.before[0xdc02]);test.assertEqual(d[0xd614],self.before[0xd614]);test.assertEqual(self.cpu.p&4,self.status_before&4);test.assertEqual(self.cpu.sp,0xfd)
  for lo,hi in ((0,0x100),(0x200,0x2000),(0x10000,0x12000),(0x1f800,0x40000)):
   test.assertEqual(bytes(d[lo:hi]),self.before[lo:hi],hex(lo))
  test.assertEqual(self.channels,{});test.assertIsNone(self.input);test.assertIsNone(self.output)
class Management(unittest.TestCase):
 def test_empty_boot_and_exact_packet(self):
  m=Machine();self.assertEqual(m.entries(),[]);self.assertEqual(m.packet(),F.encode([]));self.assertEqual(m.memory.data[N['hi_present']],1);self.assertEqual(m.channels,{})
 def test_insert_all_boundaries_ties_zeros_and_uint32(self):
  m=Machine()
  cases=[([],0),([],0xffffffff),([(b'OLD',10)],10),([(b'OLD',10)],0),([(b'OLD',10)],20),([(b'AAA',20),(b'BBB',10),(b'CCC',10),(b'DDD',1)],10),([(f'A{i:02d}'.encode(),5) for i in range(80)],5),([(b'OLD',100-i) for i in range(80)],21),([(b'OLD',100-i) for i in range(80)],20),([(f'A{i:02d}'.encode(),0) for i in range(80)],0)]
  for entries,score in cases:
   m.set_entries(entries);self.assertEqual(m.insert(b'NEW',score),F.insert(entries,b'NEW',score),(len(entries),score))
  m.set_entries([(b'AAA',50),(b'BBB',50)])
  m.insert(b'NEW',50);self.assertEqual(m.insert(b'NOW',50),[(b'NOW',50),(b'NEW',50),(b'AAA',50),(b'BBB',50)])
 def test_crc_validation_mutations_and_unused_slots(self):
  m=Machine();valid=F.encode([(b'ABC',0xffffffff),(b'Z9!',0)])
  def check(data,ok):
   m.memory.data[N['hi_io']:N['hi_io']+592]=data;m.call('hi_validate');self.assertEqual(not bool(m.cpu.p&1),ok)
  check(valid,True)
  for offset in (0,4,5,6,7,8,9,10,32,36,591):
   b=bytearray(valid);b[offset]^=0x81;check(bytes(b),False)
  for offset,value in ((4,2),(7,81),(10,1),(32,32),(591,1)):
   b=bytearray(valid);b[offset]=value;check(F.seal(b),False)
  b=bytearray(valid);b[35:39]=(0).to_bytes(4,'little');b[42:46]=(1).to_bytes(4,'little');check(F.seal(b),False)
 def test_ui_decimal_overflow_name_backspace_abort_and_no_unconfirmed_disk(self):
  m=Machine();initial=dict(m.files);m.frame(83)
  for c in '4294967295':m.frame(ord(c))
  self.assertEqual(int.from_bytes(m.memory.data[N['hi_score']:N['hi_score']+4],'little'),0xffffffff)
  m.frame(ord('9'));self.assertEqual(m.memory.data[N['hi_len']],10)
  m.frame(20);m.frame(ord('6'));self.assertEqual(m.memory.data[N['hi_len']],9) # overflow rejected
  m.frame(27);self.assertEqual(m.files,initial);self.assertEqual(m.entries(),[])
  m.frame(83);m.frame(13,enter=True);self.assertEqual(m.memory.data[N['hi_mode']],1);m.frame()
  m.frame(48);m.frame(13,enter=True);self.assertEqual(m.memory.data[N['hi_mode']],2);m.frame()
  m.frame(32);self.assertEqual(m.memory.data[N['hi_name_len']],0)
  m.frame(ord('a'));m.frame(ord('B'));m.frame(20);m.frame(ord('9'));m.frame(ord('!'))
  self.assertEqual(bytes(m.memory.data[N['hi_name']:N['hi_name']+3]),b'A9!')
  self.assertEqual(m.files,initial);m.frame(27);self.assertEqual(m.files,initial)
  m.frame(83);m.frame(48);m.frame(13,enter=True);m.frame()
  for c in (0xc1,0xc2,0xc3):m.frame(c)
  self.assertEqual(bytes(m.memory.data[N['hi_name']:N['hi_name']+3]),b'ABC');m.frame(27);self.assertEqual(m.files,initial)
  m.frame(83,joy=0xef);m.frame(27,joy=0xef);self.assertEqual(m.cpu.pc,N['main_loop'])
  m.frame();m.frame(joy=0xef);m.restored(self)
 def test_real_save_readback_restart_and_return_debounce(self):
  files={'VYHI.DAT':F.encode([(b'OLD',100)])};m=Machine(files)
  m.submit(100,'NEW');self.assertEqual(m.entries(),[(b'NEW',100),(b'OLD',100)])
  self.assertEqual(F.decode(files['VYHI.DAT']),m.entries());self.assertEqual(F.decode(files['VYHI.BAK']),[(b'OLD',100)]);self.assertNotIn('VYHI.TMP',files)
  for _ in range(5):m.frame(13,enter=True)
  self.assertEqual(len(m.entries()),2);self.assertEqual(m.cpu.pc,N['main_loop'])
  m.frame();m.submit(100,'NOW');self.assertEqual(m.entries(),[(b'NOW',100),(b'NEW',100),(b'OLD',100)])
  self.assertEqual(F.decode(files['VYHI.BAK']),[(b'NEW',100),(b'OLD',100)])
  m.frame();m.frame(88);m.restored(self)
  m.cpu.pc=N['entry'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.run_to((N['main_loop'],));self.assertEqual(m.entries(),F.decode(files['VYHI.DAT']))
  self.assertEqual(Machine(files).entries(),m.entries())
  sticky=Machine(fault='output-eof');sticky.submit(0,'ZER');self.assertEqual(sticky.entries(),[(b'ZER',0)])
 def test_missing_corrupt_version_and_backup_recovery_never_overwrite(self):
  for blob in (b'bad',F.encode([])[:-1],F.encode([])+b'x',bytes(592)):
   files={'VYHI.DAT':blob};m=Machine(files);self.assertEqual(m.entries(),[]);self.assertEqual(m.memory.data[N['hi_blocked']],1);m.frame(83);self.assertEqual(files,{'VYHI.DAT':blob})
  m=Machine({});self.assertEqual(m.memory.data[N['hi_blocked']],0);m.submit(0,'ZER');self.assertEqual(F.decode(m.files['VYHI.DAT']),[(b'ZER',0)])
  for primary in (None,b'damaged'):
   files={'VYHI.BAK':F.encode([(b'BAK',9)])}
   if primary is not None:files['VYHI.DAT']=primary
   before=dict(files);m=Machine(files);self.assertEqual(m.entries(),[(b'BAK',9)]);self.assertEqual(m.memory.data[N['hi_blocked']],1);m.frame(83);self.assertEqual(files,before)
 def test_writeprotect_diskfull_partial_corrupt_and_failed_rename(self):
  for fault in ('wp','full','truncate','corrupt','promote','write-open','write-chkout','write-carry'):
   original=F.encode([(b'OLD',500)]);files={'VYHI.DAT':original};m=Machine(files,fault=fault);m.submit(600)
   self.assertEqual(m.entries(),[(b'OLD',500)],fault);self.assertEqual(m.memory.data[N['hi_blocked']],1,fault)
   self.assertIn(original,files.values(),fault);self.assertEqual(m.channels,{},fault)
   fresh=Machine(files);self.assertEqual(fresh.entries(),[(b'OLD',500)],fault)
 def test_powerloss_after_backup_keeps_old_and_verified_new(self):
  old=F.encode([(b'OLD',4)]);files={'VYHI.DAT':old};m=Machine(files,fault='power-after-backup')
  with self.assertRaises(PowerLoss):m.submit(5)
  self.assertEqual(files['VYHI.BAK'],old);self.assertEqual(F.decode(files['VYHI.TMP']),[(b'NEW',5),(b'OLD',4)])
  fresh=Machine(files);self.assertEqual(fresh.entries(),[(b'OLD',4)]);self.assertEqual(fresh.memory.data[N['hi_blocked']],1)
 def test_pending_temp_is_preserved_and_last_resort_recovery_is_readonly(self):
  for original in (None,b'broken',F.encode([(b'OLD',99)])):
   for temp in (F.encode([(b'TMP',101)]),b'partial'):
    files={'VYHI.TMP':temp}
    if original is not None:files['VYHI.DAT']=original
    snapshot=dict(files);m=Machine(files)
    self.assertEqual(m.memory.data[N['hi_blocked']],1);self.assertEqual(files,snapshot)
    expected=[(b'OLD',99)] if original is not None and original[:4]==b'VYHI' else ([(b'TMP',101)] if temp[:4]==b'VYHI' else [])
    self.assertEqual(m.entries(),expected)
    m.frame(83);self.assertEqual(files,snapshot)
  files={'VYHI.DAT':F.encode([(b'OLD',20)])};m=Machine(files)
  files['VYHI.TMP']=F.encode([(b'TMP',25)]);before=dict(files);m.submit(30)
  self.assertEqual(files,before);self.assertEqual(m.entries(),[(b'OLD',20)])
 def test_native_open_chkin_timeout_and_device_failures_close_channels(self):
  for fault in ('device','read-open','read-chkin','read-timeout'):
   files={'VYHI.DAT':F.encode([(b'OLD',10)])};snapshot=dict(files);m=Machine(files,fault=fault)
   self.assertEqual(m.memory.data[N['hi_blocked']],1);self.assertEqual(m.channels,{});self.assertEqual(files,snapshot)
   m.frame(88);m.restored(self)
 def test_no_qualification_and_single_name_commit_on_equal_last_place(self):
  initial=[(f'A{i:02d}'.encode(),100-i) for i in range(80)]
  m=Machine({'VYHI.DAT':F.encode(initial)});m.frame(83);m.frame(50);m.frame(48);m.frame(13,enter=True);m.frame()
  self.assertEqual(m.entries(),initial);self.assertEqual(m.memory.data[N['hi_mode']],3)
  m.frame(27);m.submit(21,'NEW');self.assertEqual(m.entries(),initial[:79]+[(b'NEW',21)])
 def test_initial_disk_and_immutable_cycle_and_staged_page_budget(self):
  import build_stage3b1 as DISK
  DISK.verify_disk((ART/'VYPER_STAGE9C2.d81').read_bytes(),[('STAGE9C2',(ART/'STAGE9C2.PRG').read_bytes(),0x82),('VYHI.DAT',(ART/'VYHI.DAT').read_bytes(),0x81)])
  self.assertEqual((ART/'stage9c2_cycling.asm').read_bytes(),(BUILD.ROOT/'src/tests/stage9c1_cycling.asm').read_bytes())
  for values in ([],[(b'Q@1',0xffffffff)]*80):
   m=Machine({'VYHI.DAT':F.encode(values)});before=m.cpu.processorCycles;m.call('page_draw');cycles=m.cpu.processorCycles-before
   self.assertLess(cycles,60000);print('Prepared-page model cycles (DMA latency excluded):',len(values),cycles,flush=True)
   for i in range(48):m.frame()
   m.frame(joy=0xf7);self.assertEqual(m.memory.data[N['page']],1)
   for i in range(10):m.frame(joy=0xf7)
   self.assertEqual(m.memory.data[N['page']],1);m.frame();m.frame(joy=0xef);m.restored(self)
 def test_original_palette_sequence_survives_edit_and_disk_save(self):
  m=Machine({'VYHI.DAT':F.encode([(b'OLD',1)])});d=m.memory.data
  word=0xec;phase=2;left=1;delta=(0x20,-0x200,2,-0x20,0x200,-2)
  keys={8:83,9:50,10:13,12:78,13:69,14:87,15:13,70:29,90:157}
  for tick in range(1,127):
   key=keys.get(tick);m.frame(key,enter=key==13,right=key==29,left=key==157)
   word=(word+delta[phase])&65535;left-=1
   if left==0:phase=(phase+1)%6;left=7
   self.assertEqual(int.from_bytes(d[N['cc_word']:N['cc_word']+2],'little'),word)
   self.assertEqual([m.memory.banks[1][c][2] for c in range(3)],[((word>>s)&15)*17 for s in (8,4,0)])
  self.assertEqual(m.entries(),[(b'NEW',2),(b'OLD',1)])
  for text,y in ((BUILD.TITLE,3),(BUILD.FOOTER,21)):
   x=(80-len(text))//2;self.assertEqual(bytes(d[0x7000+80*y+x:0x7000+80*y+x+len(text)]),bytes(BUILD.screen_code(c) for c in text))
 def test_all_pages_uint32_display_and_individual_row_colours(self):
  entries=[(b'A9!',0xffffffff-i) for i in range(80)];m=Machine({'VYHI.DAT':F.encode(entries)})
  for page in range(4):
   for _ in range(32):m.frame()
   d=m.memory.data
   self.assertEqual(d[N['page']],page)
   for row in range(10):
    expected=3+(row+d[N['band_phase']])%3
    for col,x in enumerate((16,49)):
     slot=page*20+col*10+row;actual=bytes(d[0x7000+(7+row)*80+x:0x7000+(7+row)*80+x+18])
     text=f'{slot+1:02d}: A9! {0xffffffff-slot:10d}';self.assertEqual(actual,bytes(BUILD.screen_code(c) for c in text))
     self.assertEqual(bytes(m.memory.colour[0x2000+(7+row)*80+x:0x2000+(7+row)*80+x+18]),bytes([expected]*18))
   if page<3:m.frame(29,right=True);m.frame()
  m.frame(88);m.restored(self)
if __name__=='__main__':unittest.main()
