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
    def test_confirmed_mapping_against_original_type_directory(self):
        types = DATA.graphics_types((ROOT/'assets/VYGR.DAT').read_bytes())
        expected = [12, 12, *range(1, 37)]
        expected[14] = 12
        actual = [DATA.vygr_type_for_level_index(i) for i in range(38)]
        self.assertEqual(actual, expected)
        for typ in actual:
            self.assertEqual(types[typ-1]['type'], typ)
            self.assertGreater(len(types[typ-1]['frames']), 0)

    def test_reject_invalid_graphics_indices(self):
        for index in (-1, 38, 256, None, True, 2.0, '2'):
            with self.subTest(index=index), self.assertRaises(ValueError):
                DATA.vygr_type_for_level_index(index)

    def test_all_original_records_and_frames(self):
        report = DATA.analyze()
        self.assertEqual(report['vylv']['records'], 100)
        self.assertEqual(report['level_1']['offset'], 0x328)
        self.assertEqual(report['level_1']['bytes'], 849)
        self.assertEqual(report['vygr']['types'], 36)
        self.assertEqual(report['vygr']['frames'], 239)
        self.assertTrue(report['vygr']['all_frames_match_original_archive'])
        self.assertEqual(report['all_levels_parsed'], 100)
        record = report['level_1']['parsed_record']
        self.assertEqual(record['enemy_offset'], 0x15b)
        self.assertEqual(len(record['enemies']), 22)
        self.assertEqual(record['required_vygr_types'], [12])
        self.assertEqual({e['graphic_type'] for e in record['enemies']}, {14})
        self.assertFalse(report['movement_changes'])

    def test_variable_enemy_offset(self):
        record = struct.pack('<HBBHH', 1, 1, 1, 16, 1)
        record += struct.pack('<HHHH', 1, 11, 20, 3)+b'abc'
        record += struct.pack('<HHBB', 98, 43, 14, 0)
        record += struct.pack('<H', 2)+b'de'
        parsed = DATA.parse_level_record(record)
        self.assertEqual(parsed['enemy_offset'], 19)
        self.assertEqual(parsed['enemies'][0]['vygr_type'], 12)

    def test_reject_out_of_bounds_variable_regions(self):
        record = bytearray(DATA.level_records((ROOT/'assets/VYLV.DAT').read_bytes())[0][1])
        for offset in (14, 0x1df):
            damaged = bytearray(record)
            struct.pack_into('<H', damaged, offset, 65535)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                DATA.parse_level_record(damaged)
        for cut in (7, 15, 0x15b+5, len(record)-1):
            with self.subTest(cut=cut), self.assertRaises(ValueError):
                DATA.parse_level_record(record[:cut])
        with self.assertRaises(ValueError):
            DATA.parse_level_record(record+b'x')

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
