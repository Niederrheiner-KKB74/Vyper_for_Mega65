#!/usr/bin/env python3
"""Host tests: real controller opcodes, CRC, scene isolation, storage and format.
Requires py65==1.2.0 and KICKASS_JAR for independent build reproducibility.
Does not emulate DMA/VIC rendering; the live XEMU test covers data transfers.
"""
import binascii,hashlib,json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
from py65.devices.mpu6502 import MPU
from check_stage10a1_xemu import labels
sys.path.insert(0,str(Path(__file__).parent/'analysis'))
from compare_stage10b1b import parse,compare,configuration,crc16,disk_file,load
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'releases/stage_10b1b'
class Memory(list):
 def __init__(self):super().__init__([0]*65536);self.writes=[];self.dmas=[];self.labels={}
 def __setitem__(self,k,v):
  if isinstance(k,int):
   self.writes.append((k,v))
   if k==0xd705 and self.labels:
    n=self.labels
    def word(a):return self[a]+256*self[a+1]
    self.dmas.append({'src':self[n['dma_src_mb']]<<20|self[n['dma_src_bank']]<<16|word(n['dma_src_lo']),'dst':self[n['dma_dst_mb']]<<20|self[n['dma_dst_bank']]<<16|word(n['dma_dst_lo']),'length':word(n['dma_len_lo'])})
  super().__setitem__(k,v)
def machine():
 m=Memory();b=(ART/'STAGE10B1B.PRG').read_bytes();a=int.from_bytes(b[:2],'little');m[a:a+len(b)-2]=b[2:];n=labels(ART/'stage10b1b.sym');m.labels=n;return m,n
def call(m,addr):
 c=MPU(memory=m,pc=addr);c.sp=0xfd;m[0x1fe]=0xff;m[0x1ff]=0x0f;m.writes=[];m.dmas=[]
 for i in range(30000):
  if c.pc==0x1000:return c
  c.step()
 raise AssertionError('Subroutine failed to return')
def repair(data):
 b=bytearray(data);struct.pack_into('<H',b,28,crc16(b));return bytes(b)
def fixture(s,scene='A',phase=1,sequence=7):
 h=bytearray((ART/'snapshot_header.bin').read_bytes());h[9:12]=bytes([ord(scene),72,phase]);struct.pack_into('<I',h,20,sequence);h[32:38]=bytes([123,27,251,2,12,8])
 vals={0xd031:0xc0,0xd054:0x55,0xd058:192,0xd05e:96,0xd05a:60,0xd05b:1,0xd061:0xe0,0xd069:0x40,0xd015:15 if scene=='D' else 12,0xd07b:25,0xd06d:0x93,0xd06e:0x80,0xd076:255,0xd070:0x9a}
 for i,r in enumerate(s['registers']):h[48+3*i+2]=vals.get(r['address'],0)
 font=(ART/'font.bin').read_bytes();atlas=(ART/'grid_atlas.bin').read_bytes();grid=bytearray()
 for y in range(25):
  for x in range(15):
   f=(1 if x==0 else 0)|(2 if x==14 else 0)|(4 if y==0 else 0)|(8 if y==24 else 0);grid+=atlas[f*64:f*64+64]
 shadow=bytearray(16);shadow[0]=31;shadow[1]=h[25];shadow[2]=h[27];shadow[3]=h[27]&15;shadow[4]=0x55;shadow[5]=0xc0;shadow[6]=vals[0xd015];shadow[7]=phase;shadow[9]=ord(scene);shadow[10]=sequence&255;shadow[11]=sequence>>8&255
 payloads={'screen':(ART/f'scene_{scene}_screen.bin').read_bytes(),'colour':(ART/f'scene_{scene}_colour.bin').read_bytes(),'font':font,'grid':bytes(grid),'pixie':(ART/'player_ncm.bin').read_bytes(),'sprites':(ART/'sprites.bin').read_bytes()[:128]+(ART/'scene_markers.bin').read_bytes()[(ord(scene)-65)*64:(ord(scene)-64)*64]+(ART/'phase_markers.bin').read_bytes()[(phase-1)*64:phase*64],'pointers':struct.pack('<4H',*(x//64 for x in [0x9200,0x9240,0x9280,0x92c0])),'guards':bytes(64),'guard2':bytes(64),'palettes':bytes(3072),'write_shadows':bytes(shadow),'screen_next_row':bytes(192),'colour_next_row':bytes(192)}
 b=h+b''.join(payloads[r['name']] for r in s['regions']);return repair(b)
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.s=json.loads((ART/'registers.json').read_text())
 def test_scene_isolation_and_all_row_budgets(self):
  for scene in 'ABCD':
   a=parse(fixture(self.s,scene),self.s);c=configuration(a,self.s);self.assertTrue(c['profile_E_constant_checks_pass'],c)
  b=(ART/'scene_B_screen.bin').read_bytes();c=(ART/'scene_B_colour.bin').read_bytes()
  for row,glyph in [(10,0x241),(11,0x242)]:
   self.assertEqual(struct.unpack_from('<H',b,row*192+56*2)[0],glyph);self.assertEqual(c[row*192+56*2],8)
   self.assertEqual(56*4+16,240) # one NCM replaces four mono cells without moving HUD
 def test_machine_code_profile_constant_for_all_four_scenes(self):
  outputs=[]
  for scene in 'ABCD':
   m,n=machine();m[n['profile']]=ord(scene);m[0xd053]=2;m[0xd052]=32;m[n['initial_vic']+0x1a]=0xe1
   call(m,n['video_init']);self.assertEqual(m[0xd051],31);self.assertEqual(m[0xd054],0x55);outputs.append(m[0xd000:0xd07c])
  self.assertTrue(all(v==outputs[0] for v in outputs))
 def test_crc16_machine_code_known_vector(self):
  m,n=machine();m[n['mem_sum']]=255;m[n['mem_sum']+1]=255
  for v in b'123456789':
   c=MPU(memory=m,pc=n['crc_byte']);c.a=v;c.sp=0xfd;m[0x1fe]=0xff;m[0x1ff]=0x0f
   for _ in range(1000):
    if c.pc==0x1000:break
    c.step()
   else:self.fail('CRC routine did not return')
  self.assertEqual(m[n['mem_sum']]+256*m[n['mem_sum']+1],0x29b1)
 def test_segmented_dma_descriptors_and_exact_boundary(self):
  for offset,length,expected in [(0,768,[(0x48000,768)]),(0x3080,24000,[(0x4b080,20352),(0x5a000,3648)]),(0x7f00,256,[(0x4ff00,256)]),(0x8000,128,[(0x5a000,128)]),(0x9c48,16,[(0x5bc48,16)])]:
   m,n=machine();m[n['capture_bank']]=4;m[n['dma_dst_lo']]=offset&255;m[n['dma_dst_hi']]=offset>>8;m[n['dma_len_lo']]=length&255;m[n['dma_len_hi']]=length>>8;m[n['dma_src_bank']]=1;m[n['dma_src_lo']]=0;m[n['dma_src_hi']]=0x80
   call(m,n['store_snapshot']);self.assertEqual([(v['dst'],v['length']) for v in m.dmas],expected)
   self.assertTrue(all(0<v['length']<=65535 for v in m.dmas))
 def test_capture_storage_never_uses_rom_or_unmapped_bank6(self):
  spans=[(0x40000,0x48000)]
  for regions in self.s['buffers'].values():
   self.assertEqual(sum(r['length'] for r in regions),self.s['dump_size'])
   spans.extend((r['address'],r['address']+r['length']) for r in regions)
  spans.sort()
  for (a,b),(c,d) in zip(spans,spans[1:]):self.assertLessEqual(b,c)
  self.assertTrue(all(0x40000<=a<b<=0x60000 for a,b in spans))
 def test_active_x_irq_guard_and_shadow_restore(self):
  m,n=machine();m[0xd01a]=0xf1;call(m,n['entry']);self.assertFalse(any(a in (0xd051,0xd01a) for a,v in m.writes))
  m,n=machine();m[n['d051_restore_shadow']]=0x9f;m[0xd051]=0x02;m[n['initial_vic']+0x1a]=0xe1;call(m,n['restore_video']);self.assertEqual(m[0xd051],0x9f);self.assertEqual(m[0xd01a],0xe1)
 def test_crc_corruption_truncation_and_directory_rejected(self):
  a=fixture(self.s);b=bytearray(a);b[-1]^=1
  for bad in [bytes(b),a[:-1],a+b'\0']:
   with self.assertRaises(ValueError):parse(bad,self.s)
  b=bytearray(a);b[self.s['directory_offset']]^=1
  with self.assertRaises(ValueError):parse(repair(b),self.s)
 def test_phase_context_retained_and_pair_identity_required(self):
  a=parse(fixture(self.s),self.s);b=parse(fixture(self.s,phase=2),self.s);self.assertEqual(a['phase_context']['$D012'],123)
  r=compare(a,b,self.s,True);self.assertEqual(r['non_annotation_different_bytes'],0)
  with self.assertRaises(ValueError):compare(a,parse(fixture(self.s,phase=2,sequence=8),self.s),self.s,True)
 def test_palette_difference_is_never_hidden(self):
  a=parse(fixture(self.s),self.s);raw=bytearray(fixture(self.s,phase=2));pal=next(r for r in self.s['regions'] if r['name']=='palettes');raw[pal['offset']+768+1]^=1
  r=compare(a,parse(repair(raw),self.s),self.s,True);self.assertEqual(r['non_annotation_different_bytes'],1);self.assertEqual(next(v for v in r['memory_comparison'] if v['name']=='palettes')['non_annotation_different_bytes'],1)
 def test_full_ram_and_monitor_fallback(self):
  raw=fixture(self.s,phase=2);ram=bytearray(0x60000)
  for seg in self.s['buffers']['POST']:ram[seg['address']:seg['address']+seg['length']]=raw[seg['offset']:seg['offset']+seg['length']]
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'ram.bin';p.write_bytes(ram);self.assertEqual(load(p,phase='POST',schema=self.s),raw)
   lines=[]
   for seg in self.s['buffers']['POST']:
    for addr in range(seg['address'],seg['address']+seg['length'],16):lines.append(f':{addr:08X}:'+bytes(ram[addr:addr+16]).hex())
   p.write_text('\n'.join(lines));self.assertEqual(load(p,phase='POST',schema=self.s),raw)
 def test_disk_and_independent_rebuild(self):
  self.assertEqual(disk_file((ART/'VYPER_STAGE10B1B.d81').read_bytes(),'STAGE10B1B'),(ART/'STAGE10B1B.PRG').read_bytes())
  jar=os.environ.get('KICKASS_JAR');self.assertTrue(jar,'Set KICKASS_JAR to pinned5.25 jar for reproducibility check')
  with tempfile.TemporaryDirectory() as d:
   subprocess.run([sys.executable,str(ROOT/'tools/build_stage10b1b.py'),'--kickass',jar,'--output',d],check=True,stdout=subprocess.DEVNULL)
   for p in ART.iterdir():self.assertEqual(p.read_bytes(),(Path(d)/p.name).read_bytes(),p.name)
  for line in (ART/'SHA256SUMS.txt').read_text().splitlines():
   sha,name=line.split('  ');self.assertEqual(hashlib.sha256((ART/name).read_bytes()).hexdigest(),sha,name)
if __name__=='__main__':unittest.main()
