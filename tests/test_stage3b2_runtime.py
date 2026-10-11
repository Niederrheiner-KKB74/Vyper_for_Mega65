"""Assembled 6502 parser/DMA tests with modeled KERNAL, DMA and raster (not XEMU)."""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import analyze_stage3b2_data as DATA
import build_stage3b2 as BUILD

spec = importlib.util.spec_from_file_location('stage3b2_legacy_model', ROOT/'tests/test_stage3b1.py')
LEGACY = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LEGACY)
LEGACY.ARTIFACTS = ROOT/'releases/stage_3b2'
LEGACY.SYMBOLS = BUILD.symbols((LEGACY.ARTIFACTS/'STAGE3B2.sym').read_text())
NAMES = LEGACY.SYMBOLS
# The inherited constructor deliberately reads a literal old filename.


class Machine(LEGACY.LoaderMachine):
    def __init__(self, record=None):
        # Use the stable constructor and then substitute only the new image.
        artifacts = LEGACY.ARTIFACTS
        LEGACY.ARTIFACTS = ROOT/'releases/stage_3b1'
        super().__init__()
        LEGACY.ARTIFACTS = artifacts
        prg = (artifacts/'STAGE3B2.PRG').read_bytes()
        self.memory.data[0x2001:0x2001+len(prg)-2] = prg[2:]
        if record is not None:
            self.memory.data[0x7600:0x7951] = record
            graphics = (ROOT/'assets/VYGR.DAT').read_bytes()
            self.memory.data[0x54000:0x54000+len(graphics)] = graphics
        self.before = bytes(self.memory.data)

    def execute(self, address=None, limit=15_000_000):
        if address is not None:
            self.cpu.pc = address
            self.cpu.sp = 0xfd
            self.cpu.stPushWord(0x01ff)
        count = 0
        while self.cpu.pc not in (0x2100, 0x0200):
            count += 1
            if count > limit:
                raise AssertionError('Machine code did not terminate')
            if self.cpu.pc in self.KERNAL:
                self.trap()
            else:
                self.cpu.step()
        return self


def original_record():
    return DATA.level_records((ROOT/'assets/VYLV.DAT').read_bytes())[0][1]


def moved_record():
    """Same total length, one longer entry curve and one shorter attack curve."""
    p = DATA.parse_level_record(original_record())
    b = bytearray(struct.pack('<HBBHH', 1, len(p['groups']), 22, p['entry_interval'], len(p['attack_curves_hex'])))
    for i, group in enumerate(p['groups']):
        curve = bytes.fromhex(group['curve_hex'])+(b'\x00' if i == 0 else b'')
        b += struct.pack('<HHHH', group['enemy_count'], group['start_x'], group['start_y'], len(curve))+curve
    for enemy in p['enemies']:
        b += struct.pack('<HHBB', enemy['formation_x'], enemy['formation_y'], enemy['graphic_type'], enemy['attack_index'])
    for i, text in enumerate(p['attack_curves_hex']):
        curve = bytes.fromhex(text)
        if i == 0:
            curve = curve[:-1]
        b += struct.pack('<H', len(curve))+curve
    assert len(b) == 849
    return bytes(b)


class RuntimeTests(unittest.TestCase):
    def test_full_preload_and_parsed_type(self):
        machine = Machine().execute()
        self.assertEqual(machine.error, 0)
        self.assertEqual(machine.cpu.pc, 0x2100)
        self.assertEqual(machine.memory.data[NAMES['selected_type']], 12)
        self.assertEqual(int.from_bytes(machine.memory.data[NAMES['enemy_start']:NAMES['enemy_start']+2], 'little'), 0x775b)
        self.assertEqual(machine.memory.data[0x7000:0x7500], machine.before[0x7000:0x7500])
        self.assertEqual(machine.memory.data[0x6000:0x6800], machine.before[0x6000:0x6800])
        self.assertIn(b'LOADED AND VERIFIED', machine.messages)

    def test_variable_curve_lengths_move_runtime_enemy_cursor(self):
        machine = Machine(moved_record()).execute(NAMES['prepare'])
        self.assertEqual(machine.error, 0)
        self.assertEqual(int.from_bytes(machine.memory.data[NAMES['enemy_start']:NAMES['enemy_start']+2], 'little'), 0x775c)
        self.assertEqual(machine.memory.data[NAMES['selected_type']], 12)

    def test_runtime_bounds_and_invalid_graphic(self):
        for offset in (14, 0x1df):
            record = bytearray(original_record())
            struct.pack_into('<H', record, offset, 65535)
            with self.subTest(offset=offset):
                machine = Machine(record).execute(NAMES['prepare'])
                self.assertEqual(machine.error, 7)
        record = bytearray(original_record())
        record[0x15b+4] = 38
        machine = Machine(record).execute(NAMES['prepare'])
        self.assertEqual(machine.error, 7)

    def test_loaded_type12_frame_and_guards(self):
        machine = Machine(original_record()).execute(NAMES['prepare'])
        machine.execute(NAMES['init_objects'])
        types = DATA.graphics_types((ROOT/'assets/VYGR.DAT').read_bytes())
        self.assertEqual(machine.memory.data[0x9840:0x98c0], types[11]['frames'][0])
        self.assertEqual(machine.memory.data[0x9800:0x9840], bytes(64))
        self.assertEqual(machine.memory.data[0x98c0:0x9900], bytes(64))
        self.assertEqual(machine.memory.data[NAMES['frame_count']], len(types[11]['frames']))
        for _ in range(8):
            machine.execute(NAMES['animate'])
            self.assertEqual(machine.error, 0)
            self.assertEqual(machine.memory.data[0x9840:0x98c0], types[11]['frames'][0])
        self.assertEqual(machine.memory.data[NAMES['s2ja_frame']], 1)  # 8 calls, original modulo 7

    def test_multiframe_loaded_type_animation(self):
        record = bytearray(original_record())
        for i in range(22):
            record[0x15b+i*6+4] = 3  # confirmed general rule -> original VYGR type 2
        machine = Machine(record).execute(NAMES['prepare'])
        machine.execute(NAMES['init_objects'])
        frames = DATA.graphics_types((ROOT/'assets/VYGR.DAT').read_bytes())[1]['frames']
        for i in range(1, 9):
            machine.execute(NAMES['animate'])
            self.assertEqual(machine.memory.data[0x9840:0x98c0], frames[i % len(frames)])

    def test_dma_corruption_and_invalid_directory(self):
        machine = Machine(original_record()).execute(NAMES['prepare'])
        machine.memory.corrupt_dma = True
        machine.execute(NAMES['draw_frame'])
        self.assertEqual(machine.error, 4)
        for relative in (2, 4, 6):
            machine = Machine(original_record())
            base = 0x54000+12*8
            machine.memory.data[base+relative] = 0 if relative == 4 else 255
            machine.execute(NAMES['prepare'])
            self.assertEqual(machine.error, 8)

    def test_runtime_dma_failure_returns_to_basic_without_text(self):
        machine = Machine(original_record()).execute(NAMES['prepare'])
        machine.memory.corrupt_dma = True
        machine.cpu.pc = NAMES['animate']
        machine.cpu.sp = 0xfd
        machine.cpu.stPushWord(0x01ff)   # BASIC caller
        machine.cpu.stPushWord(0x22a7)   # wrapper return within main loop
        machine.execute()
        self.assertEqual(machine.error, 4)
        self.assertEqual(machine.cpu.pc, 0x0200)
        self.assertEqual(machine.messages, b'')

    def test_exact_engine_patches_and_disk(self):
        prg = (LEGACY.ARTIFACTS/'STAGE3B2.PRG').read_bytes()
        BUILD.verify_engine(prg, NAMES)
        entries = [('STAGE3B2', prg, 0x82), *[(name, (ROOT/'assets'/name).read_bytes(), 0x81) for name in ('VYLV.DAT', 'VYGR.DAT')]]
        BUILD.BASE.verify_disk((LEGACY.ARTIFACTS/'VYPER_STAGE3B2.d81').read_bytes(), entries)


if __name__ == '__main__':
    unittest.main(verbosity=2)
