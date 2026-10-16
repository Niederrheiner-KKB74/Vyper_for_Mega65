#!/usr/bin/env python3
"""Machine-code control/IRQ tests plus versioned evidence-integrity boundaries.
Requires py65==1.2.0 for the short, plain-6502 configuration subroutines.
DMA behaviour and native I/O are tested separately in XEMU, never emulated here.
"""
import hashlib,json,struct,sys,unittest
from pathlib import Path
from py65.devices.mpu6502 import MPU
from check_stage10a1_xemu import labels
sys.path.insert(0,str(Path(__file__).parent/'analysis'))
from compare_stage10b1a import parse,parse_memory,compare,compare_memory,configuration,disk_file
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'releases/stage_10b1a'
class Memory(list):
 def __init__(self):super().__init__([0]*65536);self.writes=[]
 def __setitem__(self,k,v):
  if isinstance(k,int):self.writes.append((k,v))
  super().__setitem__(k,v)
def machine():
 m=Memory();prg=(ART/'STAGE10B1A.PRG').read_bytes();base=int.from_bytes(prg[:2],'little');m[base:base+len(prg)-2]=prg[2:]
 n=labels(ART/'stage10b1a.sym');return m,n
def call(m,addr):
 c=MPU(memory=m,pc=addr);c.sp=0xfd;m[0x1fe]=0xff;m[0x1ff]=0x0f;m.writes=[]
 for i in range(20000):
  if c.pc==0x1000:return c
  c.step()
 raise AssertionError('Subroutine did not return')
def repair(b):
 b=bytearray(b);b[28:30]=b'\0\0';struct.pack_into('<H',b,28,sum(b)&65535);return bytes(b)
def reg_fixture(s,variant='A'):
 h=bytearray(32+4*s['block_size']);h[:8]=b'VYDG1B1A';h[8:12]=bytes([1,ord(variant),85,4]);struct.pack_into('<HHI',h,12,len(s['registers']),s['block_size'],len(h));h[30:32]=b'\1\1'
 for p in range(4):
  start=32+p*s['block_size'];h[start:start+4]=bytes([p+1,ord(variant),123+p,0x1b])
  for i,r in enumerate(s['registers']):struct.pack_into('<HB',h,start+4+i*3,r['address'],0)
 return repair(h)
def mem_fixture(s,variant='A'):
 b=bytearray((ART/'memory_header.bin').read_bytes());b[9]=ord(variant);b+=bytes(s['memory']['size']-256);b[256+44]=ord(variant)-64;return repair(b)
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.s=json.loads((ART/'registers.json').read_text())
 def test_actual_machine_code_explicit_write_values(self):
  for variant,value in [('A',0x9f),('B',0x1f)]:
   m,n=machine();m[n['profile']]=ord(variant);m[n['initial_vic']+0x1a]=0xe1;m[0xd051]=0x6a
   call(m,n['apply_norrdel']);self.assertEqual(m[0xd051],value);self.assertEqual(m[n['d051_shadow']],value);self.assertEqual(m[0xd01a],1)
 def test_actual_video_configuration_fixed_E_except_norrdel(self):
  results=[]
  for variant in 'AB':
   m,n=machine();m[n['profile']]=ord(variant);m[0xd053]=2;m[0xd052]=32
   initial=n['initial_vic'];m[initial+0x1a]=0xe1;m[initial+0x31]=0xc0;m[initial+0x54]=0x75
   call(m,n['video_init']);self.assertEqual(m[0xd054],0x55);self.assertEqual(m[0xd051]&0x40,0);results.append(m[0xd000:0xd07c])
  diffs=[i for i,(a,b) in enumerate(zip(*results)) if a!=b];self.assertEqual(diffs,[0x51]);self.assertEqual(results[0][0x51]^results[1][0x51],0x80)
 def test_active_x_irq_rejected_before_writes(self):
  m,n=machine();m[0xd01a]=0xf1;call(m,n['entry']);self.assertFalse(any(a in (0xd051,0xd01a) for a,v in m.writes))
 def test_restore_uses_shadow_not_live_x_readback(self):
  m,n=machine();m[n['d051_restore_shadow']]=0x9f;m[0xd051]=0x03;m[n['initial_vic']+0x1a]=0xe1
  call(m,n['restore_video']);self.assertEqual(m[0xd051],0x9f);self.assertEqual(m[0xd01a],0xe1)
 def test_phase_start_context_retained_and_reported(self):
  a=parse(reg_fixture(self.s),self.s);self.assertEqual(a['phase_context'][2]['D012'],125)
  b=parse(reg_fixture(self.s),self.s);b['phase_context'][1]['D011']^=128
  r=compare(a,b,self.s);self.assertEqual(len(r['phase_context_differences']),1);self.assertEqual(r['unexpected_stable_differences'],[])
 def test_reg_corruption_and_version_rejected(self):
  b=bytearray(reg_fixture(self.s));b[100]^=1
  with self.assertRaises(ValueError):parse(b,self.s)
  b=bytearray(reg_fixture(self.s));b[:8]=b'VYDG10B1'
  with self.assertRaises(ValueError):parse(repair(b),self.s)
 def test_memory_payload_corruption_and_wrong_directory_rejected(self):
  b=bytearray(mem_fixture(self.s));b[-1]^=1
  with self.assertRaises(ValueError):parse_memory(b,self.s)
  b=bytearray(mem_fixture(self.s));b[32]^=1
  with self.assertRaises(ValueError):parse_memory(repair(b),self.s)
  with self.assertRaises(ValueError):parse_memory(mem_fixture(self.s)[:-1],self.s)
 def test_only_declared_AB_annotation_is_exempt(self):
  a=parse_memory(mem_fixture(self.s,'A'),self.s);b=parse_memory(mem_fixture(self.s,'B'),self.s)
  self.assertEqual(compare_memory(a,b)['unexpected_different_bytes'],0)
  bad=bytearray(mem_fixture(self.s,'B'));bad[256+45]=9;b=parse_memory(repair(bad),self.s)
  self.assertEqual(compare_memory(a,b)['unexpected_different_bytes'],1)
 def test_release_disk_chain_and_hashes(self):
  self.assertEqual(disk_file((ART/'VYPER_STAGE10B1A.d81').read_bytes(),'STAGE10B1A'),(ART/'STAGE10B1A.PRG').read_bytes())
  for line in (ART/'SHA256SUMS.txt').read_text().splitlines():
   sha,name=line.split('  ');self.assertEqual(hashlib.sha256((ART/name).read_bytes()).hexdigest(),sha,name)
if __name__=='__main__':unittest.main()
