#!/usr/bin/env python3
"""Offline boundary checks for diagnostic evidence and release protection."""
import hashlib,json,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'analysis'))
from compare_stage10b1_registers import parse,compare,disk_file,load
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'releases/stage_10b1';EV=ROOT/'docs/diagnostics/stage10b1'
class DiagnosticTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.s=json.loads((ART/'registers.json').read_text());cls.data=(EV/'V10BSX.DAT').read_bytes()
 def repair(self,b):
  b=bytearray(b);b[28:30]=b'\0\0';struct.pack_into('<H',b,28,sum(b)&65535);return bytes(b)
 def test_live_dump_and_stable_geometry(self):
  a=parse(self.data,self.s)
  self.assertEqual((a['profile'],a['environment']),('S','X'))
  for r in a['phases'][1:]:self.assertEqual((r[0xd058],r[0xd059],r[0xd05e],r[0xd05a]),(192,0,96,60))
 def test_truncated_and_corrupt_export_rejected(self):
  for b in (self.data[:-1],self.data+b'\0',self.data[:100]+bytes([self.data[100]^1])+self.data[101:]):
   with self.assertRaises(ValueError):parse(b,self.s)
 def test_correct_checksum_does_not_hide_wrong_phase_or_register(self):
  b=bytearray(self.data);b[32]=4
  with self.assertRaises(ValueError):parse(self.repair(b),self.s)
  b=bytearray(self.data);b[36]^=1
  with self.assertRaises(ValueError):parse(self.repair(b),self.s)
 def test_live_raster_difference_is_retained_but_not_fault(self):
  left=parse(self.data,self.s);right=parse(self.data,self.s)
  right['phases'][2][0xd012]^=1
  c=compare(left,right,self.s)
  self.assertEqual(len(c['differences']),1);self.assertFalse(c['differences'][0]['stable_bits_differ'])
  self.assertIsNone(c['first_stable_divergence_phase'])
 def test_geometry_difference_is_flagged_in_first_phase(self):
  left=parse(self.data,self.s);right=parse(self.data,self.s)
  right['phases'][1][0xd05a]=120
  self.assertEqual(compare(left,right,self.s)['first_stable_divergence_phase'],2)
 def test_release_disk_and_hashes(self):
  d=(ART/'VYPER_STAGE10B1.d81').read_bytes()
  self.assertEqual(disk_file(d,'STAGE10B1'),(ART/'STAGE10B1.PRG').read_bytes())
  for line in (ART/'SHA256SUMS.txt').read_text().splitlines():
   sha,name=line.split('  ');self.assertEqual(hashlib.sha256((ART/name).read_bytes()).hexdigest(),sha,name)
 def test_disk_chain_cycle_is_rejected(self):
  b=bytearray((ART/'VYPER_STAGE10B1.d81').read_bytes());b[0:2]=b'\x01\x00'
  with self.assertRaisesRegex(ValueError,'cycle'):disk_file(b,'STAGE10B1')
 def test_monitor_input_roundtrip(self):
  import tempfile
  padded=self.data.ljust((len(self.data)+15)//16*16,b'\0')
  text='\n'.join(f':{0x4800+i:08X}:'+padded[i:i+16].hex() for i in range(0,len(padded),16))
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'uart.txt';p.write_text(text);self.assertEqual(load(p),self.data)
if __name__=='__main__':unittest.main()
