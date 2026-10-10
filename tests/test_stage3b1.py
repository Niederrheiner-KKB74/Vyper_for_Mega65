"""6502 host tests of the assembled preload; KERNAL/DMA/raster are models, not XEMU."""
from pathlib import Path
import importlib.util
import re
import unittest

from py65.devices.mpu6502 import MPU

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT/'releases/stage_3b1'
SPEC = importlib.util.spec_from_file_location('stage3b_build', ROOT/'tools/build_stage3b1.py')
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)
SYMBOLS = {n: int(v, 16) for n, v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)', (ARTIFACTS/'STAGE3B1.sym').read_text())}
ORIGINALS = {n: (ROOT/'assets'/n).read_bytes() for n in ('VYLV.DAT', 'VYGR.DAT')}


class Memory:
    def __init__(self, corrupt_dma=False):
        self.data = bytearray([0xa5])*0x60000
        self.raster = 0
        self.transfers = []
        self.corrupt_dma = corrupt_dma

    def __getitem__(self, address):
        if address == 0xd012:
            self.raster ^= 1
            return 250 if self.raster else 0
        return self.data[address]

    def __setitem__(self, address, value):
        self.data[address] = value
        if address != 0xd705:
            return
        assert self.data[0xd702] == self.data[0xd704] == 0
        pointer = self.data[0xd701]*256 + value
        descriptor = self.data[pointer:pointer+13]
        assert descriptor[:3] == b'\x0a\x00\x00', 'F018A COPY options/command'
        assert descriptor[11:] == b'\x00\x00', 'No DMA modulo'
        count = int.from_bytes(descriptor[3:5], 'little')
        source = int.from_bytes(descriptor[5:8], 'little')
        target = int.from_bytes(descriptor[8:11], 'little')
        assert count and source+count <= len(self.data) and target+count <= len(self.data)
        self.transfers.append((source, target, count))
        self.data[target:target+count] = self.data[source:source+count]
        if self.corrupt_dma and target == 0x6900:
            self.data[target] ^= 1
            self.corrupt_dma = False


class LoaderMachine:
    KERNAL = {0xffba, 0xff6b, 0xffbd, 0xffc0, 0xffc6, 0xffcf, 0xffb7, 0xffcc, 0xffc3, 0xffd2}
    def __init__(self, files=None, fault=None):
        self.files = dict(ORIGINALS if files is None else files)
        self.fault = fault
        self.memory = Memory(corrupt_dma=fault == 'dma')
        prg = (ARTIFACTS/'STAGE3B1.PRG').read_bytes()
        self.memory.data[0x2001:0x2001+len(prg)-2] = prg[2:]
        self.before = bytes(self.memory.data)
        self.cpu = MPU(memory=self.memory, pc=0x4800)
        self.cpu.p = 0x24  # IRQ disabled at entry; wrapper must restore it.
        self.cpu.stPushWord(0x01ff)  # RTS sentinel at $0200.
        self.opened = False
        self.active = False
        self.bank_set = False
        self.name = None
        self.position = 0
        self.status = 0
        self.messages = bytearray()
        self.opened_names = []
        self.closed = 0
        self.steps = 0

    def trap(self):
        cpu = self.cpu
        call = cpu.pc
        cpu.p &= ~cpu.CARRY
        if call == 0xffba:
            assert (cpu.a, cpu.x, cpu.y) == (2, 8, 2)
            self.bank_set = False
        elif call == 0xff6b:
            assert cpu.a == cpu.x == 0, 'SETBNK filename/data bank zero'
            self.bank_set = True
        elif call == 0xffbd:
            assert self.bank_set, 'SETBNK must precede SETNAM'
            address = cpu.x + cpu.y*256
            name = bytes(self.memory.data[address:address+cpu.a]).decode()
            assert name.endswith(',S,R')
            self.name = name[:-4]
        elif call == 0xffc0:
            if self.fault == 'open' or self.name not in self.files:
                cpu.p |= cpu.CARRY
            else:
                self.opened = True
                self.opened_names.append(self.name)
                self.position = 0
        elif call == 0xffc6:
            assert cpu.x == 2 and self.opened
            if self.fault == 'chkin':
                cpu.p |= cpu.CARRY
            else:
                self.active = True
        elif call == 0xffcf:
            assert self.active
            data = self.files[self.name]
            cpu.a = data[self.position] if self.position < len(data) else 0
            self.position += 1
            self.status = 0x40 if self.position >= len(data) else 0
            if self.fault == 'timeout':
                self.status = 2
            elif self.fault == 'read-error':
                self.status = 0x80
        elif call == 0xffb7:
            cpu.a = self.status
        elif call == 0xffcc:
            self.active = False
        elif call == 0xffc3:
            assert not self.active and cpu.a == 2
            self.opened = False
            self.closed += 1
        elif call == 0xffd2:
            assert not self.active, 'CHROUT while input channel active'
            self.messages.append(cpu.a)
        cpu.pc = (cpu.stPopWord()+1) & 0xffff

    def run(self):
        while self.cpu.pc not in (0x2100, 0x0200):
            self.steps += 1
            if self.steps > 15_000_000:
                raise AssertionError('Preloader did not terminate')
            if self.cpu.pc in self.KERNAL:
                self.trap()
            else:
                self.cpu.step()
        assert not self.active and not self.opened
        assert self.cpu.p & self.cpu.INTERRUPT, 'Entry IRQ mask not restored'
        # Loader must not modify any engine image byte, template, glyph or backup.
        for low, high in ((0x2100, 0x4800), (0x5000, 0x6800), (0x7000, 0x7600), (0x8000, 0xca00)):
            assert self.memory.data[low:high] == self.before[low:high], f'Engine overwritten at ${low:04x}'
        return self

    @property
    def error(self):
        return self.memory.data[SYMBOLS['error']]


class Stage3bTests(unittest.TestCase):
    def test_original_engine_and_disk(self):
        prg = (ARTIFACTS/'STAGE3B1.PRG').read_bytes()
        BUILD.verify_engine(prg, BUILD.baseline_files()['vyper_rrb_v014_stage2ja.prg'])
        report = BUILD.verify_disk((ARTIFACTS/'VYPER_STAGE3B1.d81').read_bytes(), [('STAGE3B1', prg, 0x82), *[(n, d, 0x81) for n, d in ORIGINALS.items()]])
        self.assertEqual([f['blocks'] for f in report], [172, 323, 122])

    def test_full_preload_handoff(self):
        machine = LoaderMachine().run()
        self.assertEqual(machine.cpu.pc, 0x2100)
        self.assertEqual(machine.error, 0)
        self.assertEqual(machine.opened_names, ['VYLV.DAT', 'VYGR.DAT'])
        self.assertEqual(machine.closed, 2)
        for address, name in ((0x40000, 'VYLV.DAT'), (0x54000, 'VYGR.DAT')):
            payload = ORIGINALS[name]
            self.assertEqual(machine.memory.data[address:address+len(payload)], payload)
            self.assertEqual(machine.memory.data[address+len(payload)], 0xa5)
        self.assertEqual(machine.memory.data[0x7600:0x7951], ORIGINALS['VYLV.DAT'][0x328:0x679])
        self.assertIn(b'VYLV + VYGR LOADED AND VERIFIED', machine.messages)
        self.assertEqual(len(machine.memory.transfers), 883)  # 319+120 full pages, two partial chunks, and Level 1.

    def assert_failure(self, machine, error):
        machine.run()
        self.assertEqual(machine.error, error)
        self.assertEqual(machine.cpu.pc, 0x0200)
        self.assertIn(b'LOAD ERROR $', machine.messages)
        self.assertNotIn(b'LOADED AND VERIFIED', machine.messages)

    def test_open_failure(self):
        self.assert_failure(LoaderMachine(fault='open'), 1)

    def test_missing_graphics(self):
        self.assert_failure(LoaderMachine(files={'VYLV.DAT': ORIGINALS['VYLV.DAT']}), 1)

    def test_chkin_failure(self):
        self.assert_failure(LoaderMachine(fault='chkin'), 2)

    def test_timeout(self):
        self.assert_failure(LoaderMachine(fault='timeout'), 3)

    def test_other_readst_error(self):
        self.assert_failure(LoaderMachine(fault='read-error'), 3)

    def test_truncated_file(self):
        files = dict(ORIGINALS)
        files['VYLV.DAT'] = files['VYLV.DAT'][:511]
        self.assert_failure(LoaderMachine(files=files), 3)

    def test_dma_readback_mismatch(self):
        self.assert_failure(LoaderMachine(fault='dma'), 4)

    def test_level_signature(self):
        files = dict(ORIGINALS)
        data = bytearray(files['VYLV.DAT'])
        data[0x328], data[0x329] = data[0x329], data[0x328]  # same sum, wrong signature
        files['VYLV.DAT'] = bytes(data)
        self.assert_failure(LoaderMachine(files=files), 5)

    def test_level_checksum(self):
        files = dict(ORIGINALS)
        data = bytearray(files['VYLV.DAT'])
        data[-1] ^= 1
        files['VYLV.DAT'] = bytes(data)
        self.assert_failure(LoaderMachine(files=files), 6)

    def test_graphics_checksum(self):
        files = dict(ORIGINALS)
        data = bytearray(files['VYGR.DAT'])
        data[-1] ^= 1
        files['VYGR.DAT'] = bytes(data)
        self.assert_failure(LoaderMachine(files=files), 6)


if __name__ == '__main__':
    unittest.main(verbosity=2)
