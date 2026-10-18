#!/usr/bin/env python3
"""Real6502 tests against explicit direct-byte and bank-latched CURRENT models; not FPGA emulation."""
import hashlib,json,os,struct,sys,tempfile,unittest
from pathlib import Path
from py65.devices.mpu6502 import MPU
from check_stage10a1_xemu import labels
import build_stage10b1d as B
sys.path.insert(0,str(Path(__file__).parent/'analysis'))
from inspect_stage10b1d import parse,load
from compare_stage10b1_registers import disk_file
ROOT=Path(__file__).resolve().parents[1];ART=Path(os.getenv('DIAGNOSTIC_BUILD_ROOT',str(ROOT/'build/diagnostics')))/'stage10b1d'
class Memory(list):
 def __init__(self,latch=False):super().__init__([0]*65536);self.latch=latch;self.stage=[0,0,0];self.current=[0,0,0];self.mix=[0]*256;self.selector=0;self.writes=[];self.dmas=[];self.labels={};self.debug=0
 def __getitem__(self,k):
  if isinstance(k,int):
   if 0xd72a<=k<=0xd72c:return self.current[k-0xd72a]
   if k==0xd6f5:return self.mix[self.selector]
   if k==0xd711:return super().__getitem__(k)|self.debug
  return super().__getitem__(k)
 def __setitem__(self,k,v):
  if isinstance(k,int):
   self.writes.append((k,v))
   if 0xd72a<=k<=0xd72c:
    self.stage[k-0xd72a]=v
    if not self.latch:self.current[k-0xd72a]=v
    elif k==0xd72c:self.current=self.stage.copy()
   if k==0xd6f4:self.selector=v
   if k==0xd6f5:self.mix[self.selector]=v
   if k==0xd705 and self.labels:
    n=self.labels
    def word(a):return self[a]+256*self[a+1]
    self.dmas.append((self[n['dma_command']],self[n['dma_src_mb']]<<20|self[n['dma_src_bank']]<<16|word(n['dma_src_lo']),self[n['dma_dst_mb']]<<20|self[n['dma_dst_bank']]<<16|word(n['dma_dst_lo']),word(n['dma_len_lo'])))
  super().__setitem__(k,v)
def machine(latch=False):
 m=Memory(latch);p=(ART/'STAGE10B1D.PRG').read_bytes();a=int.from_bytes(p[:2],'little');m[a:a+len(p)-2]=p[2:];n=labels(ART/'stage10b1d.sym');m.labels=n;m[0xd711]=0x80;return m,n
def call(m,pc):
 c=MPU(memory=m,pc=pc);c.sp=0xfd;m[0x1fe]=0xff;m[0x1ff]=0x0f;m.writes=[];m.dmas=[]
 for _ in range(1500000):
  if c.pc==0x1000:return c
  c.step()
 raise AssertionError('Controller failed to return')
class Tests(unittest.TestCase):
 def test_exact_actual_write_orders(self):
  for mode,want in [(0,[(0xd72c,1),(0xd72a,0x80),(0xd72b,0x64)]),(1,[(0xd72a,0x80),(0xd72b,0x64),(0xd72c,1)])]:
   m,n=machine();m[n['variant']]=mode;call(m,n['write_target']);self.assertEqual([(a,v) for a,v in m.writes if 0xd720<=a<=0xd72f],want)
 def test_A_B_A_replay_does_not_reuse_good_pointer(self):
  for latch in [False,True]:
   m,n=machine(latch)
   for mode in [0,1,0,1,1]:
    m[n['variant']]=mode;call(m,n['start_source']);error=4 if latch and mode==0 else 0
    self.assertEqual(m[0x1fd3],error);self.assertEqual(m[n['playing']],not error)
    self.assertEqual(m[0xd720],2 if error else 0x82)
    self.assertEqual(int.from_bytes(bytes(m.current),'little'),0x18020 if error else 0x16480)
   r=parse(bytes(m[0x5000:0x5820]));before=[e for e in r['events'] if e['phase']==0]
   self.assertEqual(len(before),5);self.assertTrue(all(e['current']==0x18020 and e['software_1FD3']==0 for e in before))
 def test_disabled_readback_before_enable_and_other_parameters_constant(self):
  states=[]
  for mode in [0,1]:
   m,n=machine();m[n['variant']]=mode;call(m,n['start_source']);r=parse(bytes(m[0x5000:0x5820]));latched=r['events'][1]
   self.assertEqual(latched['control'],2);self.assertEqual(latched['current'],0x16480);self.assertEqual(r['events'][2]['control'],0x82)
   states.append([(e['base'],e['rate'],e['end16'],e['volume']) for e in r['events']])
  self.assertEqual(states[0],states[1]);self.assertEqual(states[0][-1],(0x16480,4127,0x7ec0,64))
 def test_D711_debug_bit_is_separate_not_pointer_error(self):
  m,n=machine();m.debug=0x40;call(m,n['start_source']);r=parse(bytes(m[0x5000:0x5820]));self.assertEqual(m[0x1fd3],0)
  self.assertTrue(all(not e['D711_strict_eq80'] and e['D711_masked_eq80'] and e['D711_raw']==0xc0 for e in r['events']))
  # Existing strict global-init policy stays separate: debug bit is init03, not pointer04.
  m,n=machine();m.debug=0x40;call(m,n['mixer_init']);self.assertEqual(m[n['init_error']],3)
  self.assertEqual(m[0x501e],0xc0)
 def test_natural_stop_and_watchdog_keep_test_responsive(self):
  m,n=machine();call(m,n['start_source']);m[0xd720]=0x8a;call(m,n['poll_audio']);self.assertEqual(m[n['playing']],0);self.assertEqual(m[0x1fd3],0);self.assertEqual(m[n['phase']],3)
  call(m,n['start_source']);m[n['watchdog']]=1;m[0xd7fa]=m[n['last_frame']]+1;call(m,n['poll_audio']);self.assertEqual(m[0x1fd3],5);self.assertEqual(m[0xd720],2)
 def test_original_sample_crc_dma_and_bounds(self):
  m,n=machine();pcm=(ART/'sound17.s8').read_bytes();m[0x6000:0x7a40]=pcm;call(m,n['checksum']);self.assertEqual(m[n['crc']]+256*m[n['crc']+1],32623)
  m[0x6000]^=1;call(m,n['checksum']);self.assertNotEqual(m[n['crc']]+256*m[n['crc']+1],32623)
  call(m,n['copy_sample']);self.assertEqual(m.dmas,[(0,0xa000,0x16480,6720),(0,0x16480,0x6000,6720),(3,0,0x18000,256)])
  self.assertEqual(hashlib.sha256(pcm).hexdigest(),'392d6aa00a7097e5539722a4cbb0cb4b0f909815ed751c3b96b0a92020f573e9')
 def test_restore_latches_saved_pointer_and_all_mixer_bytes(self):
  m,n=machine(True);m[n['old_channel']:n['old_channel']+13]=[2,0,0x70,1,1,2,0,0x80,0x75,12,0x23,0x71,1];m[n['old_audio_irq']]=0x90;m[n['old_global']]=0xc8;m[n['old_swap']]=2;m[n['old_selector']]=19
  original=[i^0x5a for i in range(256)];m[n['old_mixer']:n['old_mixer']+256]=original;call(m,n['audio_restore'])
  self.assertEqual(m.mix,original);self.assertEqual(m.current,[0x23,0x71,1]);self.assertEqual(m.selector,19);self.assertEqual(m[0xd711],0x88);self.assertEqual(m[0xd712],2);self.assertEqual(m[0xd713],0x90);self.assertEqual(m[0xd720],2)
 def test_log_overwrite_and_invalid_input(self):
  m,n=machine();call(m,n['start_source'])
  for _ in range(70):m[n['phase']]=5;call(m,n['log_event'])
  r=parse(bytes(m[0x5000:0x5820]));self.assertEqual(r['records'],64);self.assertEqual(r['total_records_mod65536'],73);self.assertTrue(all(e['phase']==5 for e in r['events']))
  with self.assertRaises(ValueError):parse(bytes(2080))
  raw=bytes(m[0x5000:0x5820]);self.assertEqual(load(b'\x00\x50'+raw),raw)
  text=b'\n'.join(f':{0x5000+i:08X}:'.encode()+raw[i:i+16].hex().encode() for i in range(0,len(raw),16))
  self.assertEqual(load(text),raw)
  with self.assertRaises(ValueError):load(text.split(b'\n',1)[1])
  # New RUN must not retain a previous init error or global-status observation.
  m,n=machine();m[0x5013]=3;m[0x501e]=0xc0;m[0x1fd3]=4
  cpu=MPU(memory=m,pc=n['entry'])
  for _ in range(1000):
   if cpu.pc==n['initial_text']:break
   cpu.step()
  else:self.fail('Entry prefix did not reach initial_text')
  self.assertEqual(m[0x5013],0);self.assertEqual(m[0x501e],0);self.assertEqual(m[0x1fd3],0);self.assertEqual(m[0x5012],4)
 def test_reproducible_release_and_D81(self):
  self.assertEqual(disk_file((ART/'VYPER_STAGE10B1D.d81').read_bytes(),'STAGE10B1D'),(ART/'STAGE10B1D.PRG').read_bytes())
  with tempfile.TemporaryDirectory() as d:
   B.build(Path(os.environ['KICKASS_JAR']),Path(d));self.assertEqual({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(d).iterdir()},{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ART.iterdir()})
if __name__=='__main__':unittest.main()
