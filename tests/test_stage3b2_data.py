"""Original-container checks; no guessed level-to-enemy mapping."""
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('stage3b2_data', ROOT/'tools/analyze_stage3b2_data.py')
DATA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DATA)


class OriginalDataTests(unittest.TestCase):
    def test_all_original_records_and_frames(self):
        report = DATA.analyze()
        self.assertEqual(report['vylv']['records'], 100)
        self.assertEqual(report['level_1']['offset'], 0x328)
        self.assertEqual(report['level_1']['bytes'], 849)
        self.assertEqual(report['vygr']['types'], 36)
        self.assertEqual(report['vygr']['frames'], 239)
        self.assertTrue(report['vygr']['all_frames_match_original_archive'])
        self.assertIsNone(report['level_1']['enemy_type_mapping'])
        self.assertFalse(report['movement_changes'])

    def test_reject_overlapping_level_records(self):
        level = bytearray((ROOT/'assets/VYLV.DAT').read_bytes())
        struct.pack_into('<I', level, 16, 0x328)
        with self.assertRaises(ValueError):
            DATA.level_records(level)

    def test_reject_wrong_level_number(self):
        level = bytearray((ROOT/'assets/VYLV.DAT').read_bytes())
        struct.pack_into('<H', level, 0x328, 99)
        with self.assertRaises(ValueError):
            DATA.level_records(level)

    def test_reject_invalid_graphics_offset(self):
        graphics = bytearray((ROOT/'assets/VYGR.DAT').read_bytes())
        struct.pack_into('<I', graphics, 8, 0x10000)
        with self.assertRaises(ValueError):
            DATA.graphics_types(graphics)

    def test_reject_truncated_graphics(self):
        graphics = (ROOT/'assets/VYGR.DAT').read_bytes()[:-1]
        with self.assertRaises(ValueError):
            DATA.graphics_types(graphics)

    def test_reject_frame_not_matching_original(self):
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT/'assets', root/'assets')
            path = root/'assets/VYGR.DAT'
            graphics = bytearray(path.read_bytes())
            graphics[0x128] ^= 1
            path.write_bytes(graphics)
            with self.assertRaises(ValueError):
                DATA.analyze(root)


if __name__ == '__main__':
    unittest.main(verbosity=2)
