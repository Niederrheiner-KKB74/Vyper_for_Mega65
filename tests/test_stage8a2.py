"""Execute the assembled6502 controller. Explicit DMA/audio model, NOT XEMU."""
import binascii,json,re,sys,tempfile,unittest
from pathlib import Path
from py65.devices.mpu6502 import MPU
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import extract_stage8a2_samples as EX
ART=ROOT/'releases/stage_8a2'
N={k:int(v,16) for k,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',(ART/'STAGE8A2.sym').read_text())}
META=json.loads((ART/'samples.json').read_text());SAMPLES=META['samples']
with tempfile.TemporaryDirectory() as t:
 EX.extract(t);ARCHIVE=(Path(t)/'VYAU.DAT').read_bytes()

class Memory:
 def __init__(self):
  self.data=bytearray(65536);self.attic=bytearray(0x30000);self.mixer=bytearray((i*13+7)&255 for i in range(256));self.key=[];self.joy=255;self.frame=0;self.fetch=[bytearray(),bytearray()];self.dma_jobs=[];self.bad_attic=False;self.bad_mix=False;self.bad_rate=False;self.alias_attic=False;self.finish_on_ctrl_read=None
 def __getitem__(self,a):
  if self.finish_on_ctrl_read is not None and a==0xd720+self.finish_on_ctrl_read*32:
   source=self.finish_on_ctrl_read;self.finish_on_ctrl_read=None
   previous=self.data[a];self.advance(source,1)
   return previous # DMA completes immediately AFTER the CPU's first status read
  if a==0xd6f5:return self.mixer[self.data[0xd6f4]]
  if a==0xd610:return self.key[0] if self.key else 0
  if a==0xdc00:return self.joy
  if a==0xd7fa:return self.frame
  return self.data[a]
 def __setitem__(self,a,v):
  v&=255
  if a==0xd724 and self.bad_rate:return
  if a==0xd6f5:
   if not self.bad_mix:self.mixer[self.data[0xd6f4]]=v
   return
  if a==0xd610:
   if self.key:self.key.pop(0)
   return
  self.data[a]=v
  if a==0xd705:self.dma()
 def dma(self):
  d=self.data;p=d[0xd705]|d[0xd701]<<8|d[0xd702]<<16
  assert p<65536 and d[p:p+6:2]==bytes([0x80,0x81,0x0a]) and d[p+6] in (0,3)
  count=int.from_bytes(d[p+7:p+9],'little') or 65536
  src=(d[p+1]<<20)|int.from_bytes(d[p+9:p+12],'little');dst=(d[p+3]<<20)|int.from_bytes(d[p+12:p+15],'little')
  assert src+count<=0x08030000 and dst+count<=0x08030000
  def read(a):
   if 0x08000000<=a<0x08030000:return self.attic[(a-0x08000000)&(0x1ffff if self.alias_attic else 0x3ffff)] if not self.bad_attic else 255
   assert a<65536,hex(a);return d[a]
  def write(a,v):
   if 0x08000000<=a<0x08030000:self.attic[(a-0x08000000)&(0x1ffff if self.alias_attic else 0x3ffff)]=v;return
   assert a<65536,hex(a);d[a]=v
  for i in range(count):write(dst+i,(src&255) if d[p+6]==3 else read(src+i))
  self.dma_jobs.append((src,dst,count))
 def advance(self,source,n):
  d=self.data;r=0xd720+source*32
  for _ in range(n):
   if d[r]&0x88!=0x80:break
   p=int.from_bytes(d[r+10:r+13],'little');base=0x4000+source*0x1000
   assert base<=p<base+4096,hex(p)
   self.fetch[source].append(d[p]);p+=1
   if p&65535==int.from_bytes(d[r+7:r+9],'little'):
    if d[r]&64:p=int.from_bytes(d[r+1:r+4],'little')
    else:d[r]|=8
   d[r+10:r+13]=p.to_bytes(3,'little')

class Machine:
 def __init__(self):
  self.m=Memory();prg=(ART/'STAGE8A2.PRG').read_bytes();self.m.data[0x2001:0x2001+len(prg)-2]=prg[2:]
  for a,v in {0xd02f:0x53,0xd030:0x30,0xd031:0x88,0xd054:5,0xd614:4,0xdc02:15,0xd711:0x10,0xd6f4:0x55,0xd701:0x67,0xd702:0x12,0xd704:0x34,0xba:8,0xd061:8,0xd058:80}.items():self.m.data[a]=v
  for r in range(4):
   for i in range(13):self.m.data[0xd720+16*r+i]=(i*11)&255
   self.m.data[0xd720+16*r]=0xa
  self.before=bytes(self.m.data);self.mix_before=bytes(self.m.mixer);self.cpu=MPU(memory=self.m,pc=N['entry']);self.cpu.p=0x31;self.cpu.sp=0xfd;self.cpu.stPushWord(0x1ff);self.filepos=0;self.calls=[];self.text=[];self.channel=False;self.bad_status=False;self.missing_eof=False
 def run(self,targets,limit=30000000):
  for _ in range(limit):
   if self.cpu.pc in targets:return
   if self.cpu.pc in (0xffd2,0xffba,0xff6b,0xffbd,0xffc0,0xffc6,0xffcf,0xffb7,0xffcc,0xffc3):
    f=self.cpu.pc;self.calls.append(f)
    if f==0xffd2:
     assert not self.channel,'CHROUT while CHKIN active'
     self.text.append(self.cpu.a)
    if f==0xffc6:self.channel=True
    if f==0xffcc:self.channel=False
    if f==0xff6b:assert self.cpu.a==self.cpu.x==0
    if f==0xffbd:assert self.calls[-2]==0xff6b
    if f in (0xffc0,0xffc6):self.cpu.p&=~1
    if f==0xffcf:self.cpu.a=ARCHIVE[self.filepos];self.filepos+=1
    if f==0xffb7:self.cpu.a=2 if self.bad_status else (0x40 if self.filepos==len(ARCHIVE) and not self.missing_eof else 0)
    self.cpu.pc=self.cpu.stPopWord()+1
   else:self.cpu.step()
  raise AssertionError(hex(self.cpu.pc))
 def call(self,label):
  saved=self.cpu.pc;self.cpu.stPushWord(0x1ef);self.cpu.pc=N[label];before=self.cpu.processorCycles;self.run({0x1f0});self.cpu.pc=saved;return self.cpu.processorCycles-before
 def fastboot(self):
  # Loader tested separately. Execute entry until load_archive, inject the validated
  # archive only at that boundary, then execute ALL audio setup and main code.
  self.run({N['load_archive']});self.m.attic[:len(ARCHIVE)]=ARCHIVE;self.cpu.pc=self.cpu.stPopWord()+1;self.run({N['main_loop'],0x200});return self
 def boot(self):self.run({N['main_loop'],0x200});return self
 def loop(self):
  if self.cpu.pc==0x200:return
  self.cpu.step();self.run({N['main_loop'],0x200})
 def key(self,k):self.m.key.append(ord(k));self.loop()
 def start(self,source,index):
  self.m.data[N['s']]=source;self.m.data[N['choices']+source]=index;self.call('start_source')
 def restored(self,t):
  for a in (0xd02f,0xd030,0xd031,0xd054,0xd614,0xdc02,0xd701,0xd702,0xd704,0xd711,0xd6f4):t.assertEqual(self.m.data[a],self.before[a],hex(a))
  for r in range(4):t.assertEqual(self.m.data[0xd720+16*r:0xd72d+16*r],self.before[0xd720+16*r:0xd72d+16*r])
  t.assertEqual(bytes(self.m.mixer),self.mix_before)

class Tests(unittest.TestCase):
 def test_full_SEQ_loader_attic_roundtrip_crc(self):
  m=Machine().boot();self.assertEqual(m.cpu.pc,N['main_loop']);self.assertEqual(m.m.attic[:len(ARCHIVE)],ARCHIVE);self.assertEqual(m.filepos,154304);self.assertEqual(m.m.data[N['error']],0)
  self.assertEqual(int.from_bytes(m.m.data[N['crc']:N['crc']+2],'little'),META['archive_crc'])
  self.assertEqual(len(m.m.dma_jobs),1809);m.key('x');m.restored(self)
 def test_all_twenty_samples_exact_bytes_tail_and_restart(self):
  for index,sample in enumerate(SAMPLES):
   m=Machine().fastboot();m.start(0,index)
   for tick in range(2000):
    m.m.advance(0,97);m.call('service_all')
    if not m.m.data[N['active']]:break
   else:self.fail('Never ended '+str(sample['id']))
   expected=ARCHIVE[sample['offset']:sample['offset']+sample['length']]
   self.assertEqual(bytes(m.m.fetch[0]),expected,str(sample['id']));self.assertEqual(m.m.data[N['error']],0)
   m.start(0,index);m.m.advance(0,31);self.assertEqual(m.m.fetch[0][-31:],expected[:31]);m.key('x');m.restored(self)
 def test_dual_long_sample_stream_and_bounded_DMA_load(self):
  m=Machine().fastboot();m.start(0,15);m.start(1,18) # ID19 and ID22, both longest originals
  expected=[ARCHIVE[s['offset']:s['offset']+s['length']] for s in (SAMPLES[15],SAMPLES[18])]
  m.m.data[N['load_enabled']]=1
  costs=[]
  for tick in range(400):
   for source in (0,1):m.m.advance(source,113)
   m.m.frame=(tick//2)&255
   costs.append(m.call('service_all'));m.loop()
   if not any(m.m.data[N['active']:N['active']+2]):break
  self.assertEqual([bytes(b) for b in m.m.fetch],expected);self.assertEqual(m.m.data[N['underruns']],0)
  self.assertTrue(any(src==0x7000 and dst==0x7100 for src,dst,n in m.m.dma_jobs))
  print('Measured assembled service max6502 cycles:',max(costs),'DMA jobs:',len(m.m.dma_jobs))
 def test_panning_all_original_divisors_and_stereo_isolation(self):
  m=Machine().fastboot()
  for source in (0,1):
   for div in (4,6,8):
    for x in (0,120,240,255):
     m.m.data[N['s']]=source;m.m.data[N['divs']+source]=div;m.m.data[N['positions']+source]=x;m.call('pan');x=min(x,240)
     right=x//div;left=240//div-right
     for out in (0,0xc0):
      for off,v in ((0,left),(0x20,right)):
       i=out+0x10+source*2+off;gain=(v*255+32)//64
       self.assertEqual(m.m.mixer[i:i+2],bytes([gain,gain]))
  self.assertEqual(m.m.data[N['error']],0)
 def test_inputs_busy_pending_preemption_and_repeated_RUN(self):
  m=Machine().fastboot();m.key('a');self.assertEqual(m.m.data[N['active']],1)
  m.key('n');m.key('a');self.assertEqual(m.m.data[N['requested']],0)
  for frame in range(1,7):
   m.m.advance(0,100);m.m.frame=frame;m.call('service_all');m.call('requests')
  self.assertEqual(m.m.data[N['requested']],0)
  m.key('a')
  self.assertEqual(m.m.data[N['divs']],SAMPLES[14]['divisor'])
  self.assertEqual(int.from_bytes(m.m.data[0xd724:0xd727],'little'),SAMPLES[14]['rate'])
  m.m.advance(0,33);m.key('t');self.assertEqual(m.m.data[N['busy']],SAMPLES[14]['busy'])
  # Explicit injected stall; must stop rather than continue reading a stale ring.
  m.m.frame+=3;m.call('service_all')
  self.assertEqual(m.m.data[N['error']],6);self.assertEqual(m.m.data[N['active']],0)
  m.key('x');m.restored(self)
  m.cpu.pc=N['entry'];m.cpu.stPushWord(0x1ff);m.fastboot();self.assertEqual(m.m.data[N['quit']],0);self.assertEqual(m.m.data[N['error']],0)
 def test_single_pending_id_last_admitted_writer_and_busy_rejection(self):
  m=Machine().fastboot();d=m.m.data;d[N['s']]=0;d[N['choices']]=13;m.call('request_s')
  d[N['choices']]=14;m.call('request_s');d[N['choices']]=15
  m.call('requests');self.assertEqual(int.from_bytes(d[0xd724:0xd727],'little'),SAMPLES[14]['rate']);self.assertEqual(d[N['choices']],15)
  m.call('request_s');self.assertEqual(d[N['requested']],0) # Busy rejects, no hidden queued replay
 def test_invalid_id_pointer_and_attic_failure(self):
  m=Machine().fastboot();m.m.data[N['s']]=0;m.m.data[N['choices']]=255;m.call('start_source');self.assertEqual(m.m.data[N['error']],5)
  m=Machine().fastboot();m.start(0,15);m.m.data[0xd72c]=1;m.call('service_all');self.assertEqual(m.m.data[N['error']],5)
  m=Machine().fastboot();m.m.data[N['s']]=0;m.m.data[N['left_hi']]=8;m.m.data[N['cursor_bank']]=2;m.m.data[N['cursor_hi']]=0x5a;m.m.data[N['cursor_lo']]=0xc0;m.call('fill_half');self.assertEqual(m.m.data[N['error']],5)
  m=Machine();m.m.bad_attic=True;m.boot();self.assertEqual(m.cpu.pc,0x200);self.assertEqual(m.m.data[N['error']],3)
 def test_fastest_pair_live_pan_pause_stop_and_load_budget(self):
  m=Machine().fastboot();m.start(0,6);m.start(1,6) # fastest used ID8, PER312
  m.key('g');max_service_cycles=0;max_load_iteration_cycles=0
  remainder=[0,0]
  for tick in range(300):
   for source in (0,1):
    # Exact 40.5MHz accumulator over a 5ms synthetic wall-clock slice.
    total=remainder[source]+SAMPLES[6]['rate']*202500
    count,remainder[source]=divmod(total,1<<24);m.m.advance(source,count)
   m.m.frame=(tick//4)&255
   if tick%20==0:m.key('j' if tick%40==0 else 'l')
   max_service_cycles=max(max_service_cycles,m.call('service_all'))
   before=m.cpu.processorCycles;m.loop();max_load_iteration_cycles=max(max_load_iteration_cycles,m.cpu.processorCycles-before)
   if not any(m.m.data[N['active']:N['active']+2]):break
  expected=ARCHIVE[SAMPLES[6]['offset']:SAMPLES[6]['offset']+SAMPLES[6]['length']]
  self.assertEqual([bytes(b) for b in m.m.fetch],[expected,expected]);self.assertEqual(m.m.data[N['underruns']],0)
  # Model instruction counts only, excluding DMA stalls: no hardware timing claim.
  self.assertLess(max_service_cycles,10000);self.assertLess(max_load_iteration_cycles,150000)
  print('Fastest pair max service/load-iteration6502 cycles:',max_service_cycles,max_load_iteration_cycles)
  m.key('a');m.key('p');self.assertFalse(any(m.m.data[N['active']:N['active']+2]));m.key('p');m.key('s');m.key('x');m.restored(self)
 def test_raster_snapshot_and_screen_status(self):
  m=Machine().fastboot();m.call('status');d=m.m.data;base=0x0800+480
  self.assertEqual(bytes(d[base+12:base+15]),b'017');self.assertEqual(bytes(d[base+80+12:base+80+15]),b'019')
  d[0xd012]=100;m.call('measure_gap');d[0xd012]=110;m.call('measure_gap')
  self.assertEqual(int.from_bytes(d[N['max_lines']:N['max_lines']+2],'little'),10)
  m.m.frame=1;d[0xd012]=5;m.call('measure_gap')
  self.assertEqual(int.from_bytes(d[N['max_lines']:N['max_lines']+2],'little'),207)
  # Relocated BASIC screen: writes must follow SCRNPTR rather than assumed0800.
  d[0xd061]=0x10;m.call('status');self.assertEqual(bytes(d[0x1000+480+12:0x1000+480+15]),b'017')
 def test_failure_restore_foreign_DMA_mixer_rate_and_KERNAL_status(self):
  m=Machine();m.m.data[0xd740]=0x82;m.boot();self.assertEqual(m.m.data[N['error']],2);self.assertEqual(m.filepos,0);self.assertEqual(m.m.data[0xd740],0x82)
  m=Machine();m.m.bad_mix=True;m.fastboot();m.loop();self.assertEqual(m.m.data[N['error']],4);m.restored(self)
  m=Machine().fastboot();m.m.bad_rate=True;m.start(0,13);self.assertEqual(m.m.data[N['error']],4);self.assertFalse(m.m.data[0xd720]&128);m.key('x');m.restored(self)
  for missing in (False,True):
   m=Machine();m.missing_eof=missing;m.bad_status=not missing;m.boot();self.assertEqual(m.m.data[N['error']],1);self.assertEqual(m.cpu.pc,0x200);self.assertFalse(m.channel);m.restored(self)
 def test_attic_capacity_alias_detected_after_whole_archive_load(self):
  m=Machine();m.m.alias_attic=True;m.boot();self.assertEqual(m.cpu.pc,0x200);self.assertEqual(m.m.data[N['error']],3);self.assertEqual(m.m.data[N['configured']],0)
 def test_hardware_end_watchdog(self):
  m=Machine().fastboot();m.start(0,13);m.m.frame=200;m.m.data[N['service_frame']]=199;m.call('service_all');self.assertEqual(m.m.data[N['error']],7);self.assertFalse(m.m.data[N['active']])
 def test_DMA_completion_between_status_read_and_pointer_snapshot(self):
  for source in (0,1):
   for index in (1,13): # final half0 and final half1 respectively
    with self.subTest(source=source,id=SAMPLES[index]['id']):
     m=Machine().fastboot();m.start(source,index);sample=SAMPLES[index]
     left=sample['length']-1
     while left:
      n=min(left,97);m.m.advance(source,n);m.call('service_all');left-=n
     self.assertEqual(m.m.data[0xd720+32*source]&0x88,0x80)
     m.m.finish_on_ctrl_read=source;m.call('service_all')
     self.assertEqual(m.m.data[N['error']],0)
     self.assertEqual(m.m.data[N['active']+source],0)
     self.assertEqual(m.m.data[N['completed']],1)
     m.call('service_all');self.assertEqual(m.m.data[N['completed']],1)
 def test_archive_bounds_rates_disk_and_extraction(self):
  self.assertEqual([s['id'] for s in SAMPLES],[1,2,3,5,6,7,8,9,10,11,12,15,16,17,18,19,20,21,22,24]);self.assertEqual(len(ARCHIVE),154304)
  for s in SAMPLES:
   self.assertLessEqual(s['offset']+s['length'],154304);self.assertEqual(s['rate'],round(3546895*(1<<24)/(s['per']*40500000)))
  import build_stage3b1 as D
  D.verify_disk((ART/'VYPER_STAGE8A2.d81').read_bytes(),[('STAGE8A2',(ART/'STAGE8A2.PRG').read_bytes(),0x82),('VYAU.DAT',ARCHIVE,0x81)])
if __name__=='__main__':unittest.main()
