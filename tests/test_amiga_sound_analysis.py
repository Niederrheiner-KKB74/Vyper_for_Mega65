"""Original-byte/effect-map checks; no game assembly, no XEMU claim."""
import sys,tempfile,unittest,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools/analysis'));sys.path.insert(0,str(ROOT/'tools'))
import analyze_amiga_sound as A
class OriginalSoundAnalysisTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='vyper-sound-proof-');cls.out=Path(cls.temp.name)
  cls.report=A.analyze(ROOT/'assets/stage5b/original_sources',cls.out/'evidence',cls.out/'samples',True)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_sound_file_boundaries_runtime_identity_and_signed_wav(self):
  r=self.report;self.assertEqual((r['sample_file']['bytes'],r['sample_file']['described_bytes'],r['sample_file']['unconsumed_tail_bytes']),(164849,164836,13))
  self.assertEqual(r['sample_file']['loaded_sample_bytes'],154304)
  self.assertEqual([s['sound_id'] for s in r['samples'] if not s['loaded']],[4,13,14,23])
  for s in r['samples']:
   raw=(self.out/'samples'/f'sound_{s["sound_id"]:02d}.s8').read_bytes()
   self.assertEqual(len(raw),2*s['Paula_LEN_words']);self.assertEqual(A.BASE.sha(raw),s['sample_sha256'])
   with wave.open(str(self.out/'samples'/f'sound_{s["sound_id"]:02d}_PER{s["Paula_PER"]}.wav'),'rb') as w:
    self.assertEqual((w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()),(1,1,round(3546895/s['Paula_PER']),len(raw)))
    self.assertEqual(w.readframes(len(raw)),bytes(b^128 for b in raw))
 def test_code_proof_and_call_graph(self):
  r=self.report;self.assertEqual(len(r['verified_spans']),22)
  self.assertEqual(sum(len(s['instructions']) for s in r['verified_spans']),1121)
  self.assertEqual([(c['routine'],c['USS']) for c in r['direct_callers']],[('reset',0xc08f1a),('init',0xc09b00),('cleanup',0xc0c430),('tick',0xc0d01a),('tick',0xc0d094)])
  for s in r['verified_spans']:self.assertTrue(s['both_runtime_copies_match_relocated_ADF'])
 def test_38_sound_mappings_correct_record_origin_and_player_distinction(self):
  types=self.report['enemy_types'];self.assertEqual(len(types),38)
  # C0AA24 uses DATA2BB4, which is record+10, not the old graphics helper's prefix.
  self.assertEqual(types[0]['DATA_offset'],0x2baa)
  self.assertEqual([types[0][n] for n in ('destruction_sound','shot_sound','entry_sound','attack_sound')],[1,10,6,6])
  self.assertEqual([types[14][n] for n in ('destruction_sound','shot_sound','entry_sound','attack_sound')],[3,2,6,7])
  self.assertEqual([types[37][n] for n in ('destruction_sound','shot_sound','entry_sound','attack_sound')],[8,5,11,7])
  self.assertEqual(set(t['destruction_sound'] for t in types),{1,3,8,9,18,20})
  self.assertNotIn(19,{t['destruction_sound'] for t in types})
  self.assertEqual(len(self.report['events']),156)
  self.assertEqual({e['sound_id'] for e in self.report['events']},{s['sound_id'] for s in self.report['samples'] if s['loaded']})
 def test_100_level_types_original_Forme_and_bounded_Copper(self):
  r=self.report;self.assertEqual(len(r['level_Forme_audit']),100)
  self.assertEqual(sum(l['enemies'] for l in r['level_Forme_audit']),2194)
  self.assertEqual(r['types_not_in_100_levels'],[6,11])
  self.assertFalse(any(l['audio_moves'] for l in r['copper_lists']))
  self.assertEqual(r['copper_lists'][1]['dma_interrupt_moves'],[{'address':'0x18572','register':'0x9c','value':'0x8010'}])
 def test_original_hash_gate_and_OFS_checksum_gate(self):
  source=ROOT/'assets/stage5b/original_sources';adf=(source/'VYPER.ADF').read_bytes();inventory,read=A.ofs_inventory(adf)
  header=inventory['/Vyper/sonquasar']['header_block'];bad=bytearray(adf);bad[header*512+100]^=1
  with self.assertRaisesRegex(ValueError,'checksum'):A.ofs_inventory(bytes(bad))
  bad=bytearray(adf);bad[inventory['/Vyper/sonquasar']['first_data']*512+40]^=1;_,badread=A.ofs_inventory(bytes(bad))
  with self.assertRaisesRegex(ValueError,'checksum'):badread('/Vyper/sonquasar')
  clone=self.out/'bad-input';clone.mkdir()
  for n in A.BASE.HASHES:(clone/n).symlink_to(source/n)
  (clone/'VYPER.ADF').unlink();(clone/'VYPER.ADF').write_bytes(bytes(bad))
  with self.assertRaisesRegex(ValueError,'Original source changed'):A.analyze(clone,self.out/'must-not-exist')
  self.assertFalse((self.out/'must-not-exist').exists())
 def test_exports_guard_and_metadata_reproducible(self):
  with self.assertRaisesRegex(ValueError,'outside repository'):A.analyze(ROOT/'assets/stage5b/original_sources',self.out/'unused',ROOT/'assets/forbidden')
  A.analyze(ROOT/'assets/stage5b/original_sources',self.out/'second')
  for p in (self.out/'evidence').iterdir():self.assertEqual(p.read_bytes(),(self.out/'second'/p.name).read_bytes(),p.name)
if __name__=='__main__':unittest.main()
