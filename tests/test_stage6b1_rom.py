"""User-provided V920413 ROM address evidence; no emulator execution claims."""
import hashlib,os,unittest
from pathlib import Path
ROM_SHA='af3c447f791a2fdc48cb21e1bd3fab015e32641228d9d30d21259b9e878c6fa0'
class ROMAddressEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths=[Path(os.environ['MEGA65_ROM_V920413'])] if os.getenv('MEGA65_ROM_V920413') else list(Path('/workspace/attachments').glob('*/MEGA65.ROM'))
        for p in paths:
            if hashlib.sha256(p.read_bytes()).hexdigest()==ROM_SHA:cls.rom=p.read_bytes();return
        raise unittest.SkipTest('Original user ROM V920413 required; supply MEGA65_ROM_V920413')
    def test_FA29_is_IRQ_BRK_entry_not_disk_wait(self):
        r=self.rom
        self.assertEqual(r[0x1fffe:0x20000],bytes.fromhex('23fa'))
        self.assertEqual(r[0x1fa29:0x1fa2c],bytes.fromhex('a9005b'))
        self.assertEqual(r[0x1fa36:0x1fa41],bytes.fromhex('2910d0036c1403386c1603'))
    def test_CE26_is_original_BRK_vector_ROM_code(self):
        r=self.rom
        self.assertEqual(r[0x1fe08:0x1fe0e],bytes.fromhex('ecf926ceb6f9'))
        self.assertEqual(r[0xce26:0xce2d],bytes.fromhex('084242ad1c0148'))
    def test_actual_CPU_mapping_model_distinguishes_ROMC_and_RAM_BRK(self):
        import test_stage6b1 as T
        m=T.Machine();m.memory.data[0x20000:0x40000]=self.rom
        m.memory.data[0xce26]=0 # Explicit blank-RAM model, not a claimed XEMU dump.
        m.memory.data[0xd030]=32
        self.assertEqual(m.memory[0xce26],8) # PHP in ROM, physical$2CE26.
        m.memory.data[0xd030]=0
        self.assertEqual(m.memory[0xce26],0) # BRK in model RAM, physical$0CE26.
if __name__=='__main__':unittest.main()
