#!/usr/bin/env python3
"""Real6502 control/data tests, not an emulation of VIC rendering or DMA memory copies."""
import hashlib,json,os,struct,sys,tempfile,unittest
from pathlib import Path
from py65.devices.mpu6502 import MPU
from check_stage10a1_xemu import labels
import build_stage10b1c as B
sys.path.insert(0,str(Path(__file__).parent/'analysis'))
from compare_stage10b1_registers import disk_file
from inspect_stage10b1c import parse
ROOT=Path(__file__).resolve().parents[1];ART=Path(os.getenv('DIAGNOSTIC_BUILD_ROOT',str(ROOT/'build/diagnostics')))/'stage10b1c'
class Memory(list):
 def __init__(self):super().__init__([0]*65536);self.writes=[];self.dmas=[];self.labels={}
 def __setitem__(self,k,v):
  if isinstance(k,int):
   self.writes.append((k,v))
   if k==0xd705 and self.labels:
    n=self.labels
    def w(a):return self[a]+256*self[a+1]
    self.dmas.append((self[n['dma_src_mb']]<<20|self[n['dma_src_bank']]<<16|w(n['dma_src_lo']),self[n['dma_dst_mb']]<<20|self[n['dma_dst_bank']]<<16|w(n['dma_dst_lo']),w(n['dma_len_lo'])))
  super().__setitem__(k,v)
def machine():
 m=Memory();p=(ART/'STAGE10B1C.PRG').read_bytes();a=int.from_bytes(p[:2],'little');m[a:a+len(p)-2]=p[2:];n=labels(ART/'stage10b1c.sym');m.labels=n;return m,n
def call(m,pc):
 c=MPU(memory=m,pc=pc);c.sp=0xfd;m[0x1fe]=0xff;m[0x1ff]=0x0f;m.writes=[];m.dmas=[]
 for _ in range(200000):
  if c.pc==0x1000:return c
  c.step()
 raise AssertionError('Subroutine failed to return')
class Tests(unittest.TestCase):
 def test_coordinate_models_and_boundaries(self):
  for x in [0,1,32,112,224,239,240,256,304,319,320]:
   self.assertEqual(B.gotox(x,'A'),x*2);self.assertEqual(B.gotox(x,'B'),x)
   self.assertEqual(B.predict(x,'B','XEMU'),x*2);self.assertEqual(B.predict(x,'B','FPGA_SOURCE_MODEL'),x*2)
  self.assertEqual(B.gotox(240,'B'),240);self.assertEqual(B.gotox(320,'B'),320)
  with self.assertRaises(ValueError):B.gotox(321,'B')
  self.assertEqual(240+10*8,320)
 def test_actual_patching_both_modes_and_repeat(self):
  m,n=machine()
  for mode in [0,1,0,1]:
   m[n['mode']]=mode;call(m,n['build_screen'])
   self.assertEqual(bytes(m[0xa000:0xa960]),(ART/f'scene_{"AB"[mode]}_screen.bin').read_bytes())
   self.assertEqual(m.dmas,[(0xa000,0xe000,2400),(0xb300,0xff80000,2400),(n['zero_row'],0xff80960,96),(n['zero_row'],0xe960,96)])
  source=(ROOT/'src/tests/stage10b1c.asm').read_text().split('build_screen:')[1].split('variant_marker:')[0]
  self.assertNotIn('\n    asl',source)
 def test_constant_registers_except_two_mode_parameters(self):
  values=[]
  for mode in [0,1]:
   m,n=machine();m[n['mode']]=mode;m[0xd053]=2;m[0xd052]=32;call(m,n['video_init'])
   self.assertEqual(m[0xd031],0xc0 if mode==0 else 0x40);self.assertEqual(m[0xd05a],60 if mode==0 else 120)
   for addr,v in [(0xd051,31),(0xd054,0x55),(0xd07a,0),(0xd079,0),(0xd01a,0),(0xd058,96),(0xd05e,48),(0xd04c,80),(0xd04e,104)]:self.assertEqual(m[addr],v)
   values.append({k:v for k,v in m.writes if 0xd000<=k<0xd400 and k not in (0xd031,0xd05a)})
  self.assertEqual(values[0],values[1])
 def test_bounded_rows_commands_and_original_assets(self):
  col=(ART/'scene_colour.bin').read_bytes();self.assertEqual(len(col),2400)
  for mode in 'AB':
   scr=(ART/f'scene_{mode}_screen.bin').read_bytes();self.assertEqual(len(scr),2400)
   for row in range(25):
    words=[(int.from_bytes(scr[i:i+2],'little'),col[i],col[i+1]) for i in range(row*96,(row+1)*96,2)]
    self.assertEqual(len(words),48);self.assertEqual(words[16],(B.gotox(240,mode),0x10,0))
    self.assertTrue(all(0<=v<=640 for v,f,c in words if f&16))
    self.assertEqual(sum(not(f&24) for v,f,c in words),10)
  for f in ['player_ncm.bin','player_palette_r.bin','player_palette_g.bin','player_palette_b.bin']:self.assertEqual((ART/f).read_bytes(),(ROOT/'assets/player'/f).read_bytes())
 def test_sprite_xy_independent_of_H640(self):
  # sprite setup shares the grid builder; descriptor writes are observed, not applied.
  outputs=[]
  for mode in [0,1]:
   m,n=machine();m[n['mode']]=mode;m[0xd04c]=80;m[0xd04e]=104;call(m,n['scene_grid'])
   self.assertEqual(m[0xd015],15);self.assertEqual(m[0xd000]+256*(m[0xd010]&1)+512*(m[0xd05f]&1),301)
   self.assertEqual(m[0xd001]+256*(m[0xd077]&1)+512*(m[0xd078]&1),424)
   self.assertEqual(m[0xd002]+256*bool(m[0xd010]&2)+512*bool(m[0xd05f]&2),525)
   outputs.append(m[0xd000:0xd010]+m[0xd077:0xd079])
  self.assertEqual(*outputs)
 def test_register_sample_and_readbacks(self):
  m,n=machine();m[n['mode']]=1;m[n['sequence']]=7;m[0xd031]=0x40;call(m,n['capture'])
  d=bytes(m[0x4800:0x4a06]);self.assertEqual(d[:10],b'VYDG1B1C\1B');self.assertEqual(d[10],7)
  for i,a in enumerate(B.P.REGS):self.assertEqual(struct.unpack_from('<HB',d,32+i*3),(a,m[a]))
  # A real controller-generated sample must pass the independent decoder.
  m,n=machine();m[n['mode']]=1;m[0xd053]=2;m[0xd052]=32
  call(m,n['video_init']);call(m,n['scene_grid']);call(m,n['capture'])
  raw=bytes(m[0x4800:0x4a06]);schema=json.loads((ART/'scene.json').read_text())
  self.assertTrue(parse(raw,schema)['configuration_valid'])
  with self.assertRaises(ValueError):parse(raw[:-1],schema)
  bad=bytearray(raw);bad[32]^=1
  with self.assertRaises(ValueError):parse(bad,schema)
 def test_safe_XIRQ_refusal_and_shadow_restore(self):
  m,n=machine();m[0xd01a]=0x10;call(m,n['entry']);self.assertFalse(any(a==0xd051 for a,v in m.writes))
  m,n=machine();m[n['d051_restore_shadow']]=0x9f;m[n['initial_vic']+0x1a]=0xe1;m[n['initial_vic']+0x53]=0xe5
  call(m,n['restore_all']);self.assertEqual(m[0xd051],0x9f);self.assertEqual(m[0xd053],0x60);self.assertEqual(m[0xd01a],0xe1)
  self.assertIn((0x40000,0xff80000,32768),m.dmas)
 def test_disk_and_independent_release_reproduction(self):
  self.assertEqual(disk_file((ART/'VYPER_STAGE10B1C.d81').read_bytes(),'STAGE10B1C'),(ART/'STAGE10B1C.PRG').read_bytes())
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);B.build(Path(os.environ['KICKASS_JAR']),out)
   self.assertEqual({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ART.iterdir()})
if __name__=='__main__':unittest.main()
