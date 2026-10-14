"""Actual assembled6502 instructions plus explicit DMA/mixer model, NOT XEMU/audio listening."""
import sys,re,json,tempfile,unittest,hashlib,binascii
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from py65.devices.mpu6502 import MPU
import extract_stage8a1_sample as EX
ART=ROOT/'releases/stage_8a1';N={k:int(v,16) for k,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',(ART/'STAGE8A1.sym').read_text())}
class Memory:
 def __init__(self):
  self.data=bytearray(65536);self.mixer=bytearray((i*13+7)&255 for i in range(256));self.key=[];self.space=False;self.joy=255;self.frame=0;self.starts=0;self.samples=[];self.bad_init=False;self.bad_mixer=False;self.audio_writes=[]
 def __getitem__(self,a):
  if a==0xd6f5:return self.mixer[self.data[0xd6f4]]
  if a==0xd613:return 0xef if self.space and self.data[0xd614]==7 else 255
  if a==0xdc00:return self.joy
  if a==0xd610:return self.key[0] if self.key else 0
  if a==0xd7fa:return self.frame
  return self.data[a]
 def __setitem__(self,a,v):
  v&=255
  if a==0xd724 and self.bad_init:return # immutable rate register: init readback must fail
  if a==0xd6f5 and self.bad_mixer:return
  if a==0xd6f5:self.mixer[self.data[0xd6f4]]=v;return
  if a==0xd610:
   if self.key:self.key.pop(0)
   return
  if 0xd720<=a<=0xd75c:self.audio_writes.append(a)
  if a==0xd720 and v&0x88==0x80:self.starts+=1
  self.data[a]=v
 def advance(self,n):
  d=self.data
  if d[0xd711]&128 and d[0xd720]&0x88==0x80:
   for _ in range(n):
    p=d[0xd72a]|(d[0xd72b]<<8)|(d[0xd72c]<<16)
    assert 0x4000<=p<0x5a40
    b=d[p];self.samples.append(b if b<128 else b-256);p+=1
    d[0xd72a:0xd72d]=p.to_bytes(3,'little')
    if p&65535==int.from_bytes(d[0xd727:0xd729],'little'):
     d[0xd720]|=8;break
class Machine:
 def __init__(self,keymode=0x53):
  self.m=Memory();p=(ART/'STAGE8A1.PRG').read_bytes();self.m.data[0x2001:0x2001+len(p)-2]=p[2:]
  for a,v in {0xd02f:keymode,0xd030:0x30,0xd031:0x88,0xd054:5,0xd614:4,0xdc02:0xf,0xfb:0x67,0xfc:0x89,0xd711:0x10,0xd6f4:0x55}.items():self.m.data[a]=v
  for i in range(13):self.m.data[0xd720+i]=(i*11)&255
  self.m.data[0xd720]=0x0a
  self.before=bytes(self.m.data);self.mix_before=bytes(self.m.mixer);self.cpu=MPU(memory=self.m,pc=N['entry']);self.cpu.p=0x31;self.cpu.sp=0xfd;self.cpu.stPushWord(0x1ff);self.text=[]
 def run(self,targets,limit=2000000):
  for _ in range(limit):
   if self.cpu.pc in targets:return self
   if self.cpu.pc==0xffd2:self.text.append(self.cpu.a);self.cpu.pc=self.cpu.stPopWord()+1
   else:self.cpu.step()
  raise AssertionError(hex(self.cpu.pc))
 def boot(self):return self.run({N['main_loop'],0x200})
 def loop(self,n=1):
  for _ in range(n):
   if self.cpu.pc==0x200:break
   self.cpu.step();self.run({N['main_loop'],0x200})
  return self
 def key(self,c):self.m.key.append(c);return self.loop()
 def restored(self,test):
  for a in (0xd02f,0xd030,0xd031,0xd054,0xd614,0xdc02,0xfb,0xfc,0xd711,0xd6f4):test.assertEqual(self.m.data[a],self.before[a],hex(a))
  test.assertEqual(bytes(self.m.data[0xd720:0xd72d]),self.before[0xd720:0xd72d]);test.assertEqual(bytes(self.m.mixer),self.mix_before);test.assertFalse(self.cpu.p&4)
class PCMTests(unittest.TestCase):
 def test_source_extraction_rate_and_PRG_disk_bytes(self):
  with tempfile.TemporaryDirectory() as t:
   meta=EX.extract(t);blob=(Path(t)/'sound17.s8').read_bytes()
   self.assertEqual((meta['Paula_PER'],meta['rate_increment'],meta['bytes']),(356,0x101f,6720))
   self.assertEqual(meta['CRC16_CCITT_FALSE'],binascii.crc_hqx(blob,0xffff))
   prg=(ART/'STAGE8A1.PRG').read_bytes();self.assertEqual(prg[2+0x4000-0x2001:],blob)
   import build_stage3b1 as D
   D.verify_disk((ART/'VYPER_STAGE8A1.d81').read_bytes(),[('STAGE8A1',prg,0x82)])
   self.assertEqual(N['sample_data'],0x4000);self.assertLess(N['crc']+2,0x3000);self.assertEqual(0x4000+len(blob),0x5a40)
 def test_one_shot_signed8_full_length_and_held_space(self):
  m=Machine().boot();self.assertEqual(m.cpu.pc,N['main_loop']);m.loop();m.m.space=True;m.loop()
  self.assertEqual(m.m.data[0xd720],0x82);self.assertEqual(m.m.starts,1)
  self.assertEqual(int.from_bytes(m.m.data[0xd724:0xd727],'little'),0x101f)
  m.m.advance(6719);m.loop();self.assertEqual(m.m.data[N['playing']],1)
  m.m.advance(1);m.loop();self.assertEqual((m.m.data[N['playing']],m.m.data[0xd720],m.m.data[0xd729]),(0,2,0))
  blob=(ART/'STAGE8A1.PRG').read_bytes()[2+0x4000-0x2001:];self.assertEqual(m.m.samples,[b if b<128 else b-256 for b in blob])
  m.loop(200);self.assertEqual(m.m.starts,1)
  m.m.space=False;m.loop();m.m.space=True;m.loop();self.assertEqual(m.m.starts,2)
  m.key(0x78);self.assertEqual(m.cpu.pc,0x200);m.restored(self)
 def test_joystick_release_and_no_queue_mid_sample(self):
  m=Machine().boot();m.loop();m.m.joy=0xef;m.loop();self.assertEqual(m.m.starts,1)
  m.m.joy=255;m.loop();m.m.joy=239;m.loop();self.assertEqual(m.m.starts,1)
  m.m.advance(6720);m.loop(20);self.assertEqual(m.m.starts,1)
  m.m.joy=255;m.loop();m.m.joy=239;m.loop();self.assertEqual(m.m.starts,2)
  self.assertTrue(all(0xd720<=a<=0xd72c for a in m.m.audio_writes))
 def test_mixer_fixed_mono_and_all_modes_EXIT_RUN(self):
  for mode in (0,0x96,0x53,0x54):
   m=Machine(mode).boot();self.assertEqual(m.cpu.pc,N['main_loop'])
   self.assertTrue(m.m.data[0xd031]&64 and m.m.data[0xd054]&64)
   expected=bytearray(256)
   for i in (0x10,0x11,0x30,0x31,0xd0,0xd1,0xf0,0xf1,0x1e,0x1f,0x3e,0x3f,0xde,0xdf,0xfe,0xff):expected[i]=255
   self.assertEqual(m.m.mixer,expected)
   m.key(0x58);self.assertEqual(m.cpu.pc,0x200);m.restored(self)
   m.cpu.pc=N['entry'];m.cpu.sp=0xfd;m.cpu.stPushWord(0x1ff);m.boot();self.assertEqual(m.cpu.pc,N['main_loop']);m.key(0x58);m.restored(self)
 def test_CRC_busy_init_and_timeout_errors_restore(self):
  m=Machine();m.m.data[0x4100]^=1;m.boot();self.assertEqual(m.m.data[N['error']],1);self.assertEqual(m.m.starts,0);m.restored(self)
  m=Machine();m.m.data[0xd730]=0x82;m.boot();self.assertEqual(m.m.data[N['error']],2);self.assertEqual(m.m.data[0xd730],0x82);m.restored(self)
  m=Machine();m.m.bad_init=True;m.boot();self.assertEqual(m.m.data[N['error']],3);m.restored(self)
  m=Machine();m.m.bad_mixer=True;m.boot();self.assertEqual(m.m.data[N['error']],3);m.restored(self)
  m=Machine().boot();m.loop();m.m.space=True;m.loop()
  for i in range(1,101):m.m.frame=i;m.loop()
  self.assertEqual(m.cpu.pc,0x200);self.assertEqual(m.m.data[N['error']],4);m.restored(self)
if __name__=='__main__':unittest.main()
