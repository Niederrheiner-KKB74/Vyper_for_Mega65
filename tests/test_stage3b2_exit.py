"""RAM/exit regression and optional execution of the user's real ROM cursor routine.

MEGA65_ROM=/path/to/MEGA65.ROM enables the ROM checks; ROM bytes are never
included in this repository. The narrow 65CE02 adapter models LDZ/EOM and
32-bit indirect accesses used by this routine, not the full MEGA65 or display.
"""
import hashlib
import os
from pathlib import Path
import unittest

from test_stage3b2_runtime import Machine, NAMES, ROOT, original_record

ROM_SHA = '0f257ca5013e846604af6637bf44146de7500a49c54242a725aeb52cd86af5c1'


class CursorMemory:
    def __init__(self, memory, rom):
        self.memory = memory
        self.rom = rom

    def __getitem__(self, address):
        if 0xe000 <= address <= 0xffff:
            return self.rom[address+0x10000]
        if 0x0ff80000 <= address < 0x0ff80800:
            address = 0xd800+address-0x0ff80000
        return self.memory[address]

    def __setitem__(self, address, value):
        if 0x0ff80000 <= address < 0x0ff80800:
            address = 0xd800+address-0x0ff80000
        self.memory[address] = value


def blink(machine, rom):
    """Execute unmodified V920395 $E513-$E55C with its $E4FC helper."""
    cpu = machine.cpu
    memory = CursorMemory(machine.memory, rom)
    cpu.memory = memory
    cpu.pc = 0xe513
    cpu.sp = 0xfd
    cpu.stPushWord(0x01ff)
    z = 0
    long_access = False
    for _ in range(200):
        if cpu.pc == 0x0200:
            cpu.memory = machine.memory
            return
        opcode = memory[cpu.pc]
        if opcode == 0xab:  # LDZ absolute
            address = memory[cpu.pc+1] | memory[cpu.pc+2] << 8
            z = memory[address]
            cpu.FlagsNZ(z)
            cpu.pc += 3
        elif opcode == 0xea:  # EOM: next indirect access uses 32-bit pointer
            long_access = True
            cpu.pc += 1
        elif opcode in (0xb2, 0x92):  # LDA/STA (base),Z
            if not long_access:
                raise AssertionError('Expected EOM before long indirect access')
            base = memory[cpu.pc+1]
            address = sum(memory[base+i] << (8*i) for i in range(4))+z
            if opcode == 0xb2:
                cpu.a = memory[address]
                cpu.FlagsNZ(cpu.a)
            else:
                memory[address] = cpu.a
            long_access = False
            cpu.pc += 2
        else:
            cpu.step()
    raise AssertionError('ROM cursor routine did not return')


class ExitTests(unittest.TestCase):
    def test_full_preload_engine_x_exit_and_restart_restore_video_and_colour(self):
        machine = Machine().execute()
        restored_registers = (0xd020, 0xd021, 0xd030, 0xd031, 0xd054, 0xd05d,
                              0xd058, 0xd059, 0xd05e, 0xd060, 0xd061, 0xd062,
                              0xd063, 0xd064, 0xd065, 0xd068, 0xd069, 0xd06a,
                              0xd07b, 0xd06b, 0xd057, 0xd06c, 0xd06d, 0xd06e, 0xd070)
        for i, address in enumerate(restored_registers):
            machine.memory.data[address] = i+1
        before_registers = {a: machine.memory.data[a] for a in restored_registers}
        before_colour = bytes(machine.memory.data[0xd800:0xe000])
        before_kernal = bytes(machine.memory.data[0x1000:0x1600])
        for _ in range(2):
            machine.cpu.pc = 0x2100
            machine.cpu.sp = 0xfd
            machine.cpu.stPushWord(0x01ff)
            for _ in range(100_000):
                if machine.cpu.pc == NAMES['main_loop']:
                    break
                machine.cpu.step()
            else:
                self.fail('Engine initialization did not reach main_loop')
            for _ in range(100_000):
                if machine.cpu.pc == 0x0200:
                    break
                if machine.cpu.pc == 0xffe4:
                    machine.cpu.a = 0x58  # X from modeled GETIN
                    machine.cpu.pc = machine.cpu.stPopWord()+1
                else:
                    machine.cpu.step()
            else:
                self.fail('X did not return to BASIC')
            self.assertEqual({a: machine.memory.data[a] for a in restored_registers}, before_registers)
            self.assertEqual(machine.memory.data[0xd800:0xe000], before_colour)
            self.assertEqual(machine.memory.data[0x1000:0x1600], before_kernal)

    def test_engine_work_preserves_entire_kernal_region(self):
        machine = Machine(original_record()).execute(NAMES['prepare'])
        # Different nonzero bytes reveal writes including zero initialization.
        machine.memory.data[0x1000:0x1600] = bytes((i*37+19) & 255 for i in range(0x600))
        before = bytes(machine.memory.data[0x1000:0x1600])
        machine.execute(NAMES['init_objects'])
        self.assertEqual(machine.memory.data[0x1600:0x1660], machine.memory.data[0x7000:0x7060])
        self.assertEqual(machine.memory.data[0x1662], 64)
        self.assertEqual(machine.memory.data[0x1664], 32)
        for _ in range(24):
            for name in ('v014_diag_before', 'v014_move_record', 'v014_diag_after_move',
                         'v014_update_objects', 'v014_diag_before_render',
                         'v014_render_all', 'v014_diag_after_render', 'animate'):
                machine.execute(NAMES[name])
        self.assertEqual(machine.memory.data[0x1000:0x1600], before)
        self.assertEqual(machine.memory.data[0x1900], 0x5f)
        machine.execute(NAMES['exit_to_basic'])
        self.assertEqual(machine.memory.data[0x1000:0x1600], before)

    def test_only_53_operand_high_bytes_change(self):
        # Restore the old addresses in the new image and compare its digest to
        # the previous shipped PRG. The prior binary need not be duplicated.
        from build_stage3b2 import RAM_RELOCATION_SITES
        prg = bytearray((ROOT/'releases/stage_3b2/STAGE3B2.PRG').read_bytes())
        for address in RAM_RELOCATION_SITES:
            prg[address-0x2001+4] -= 6
        self.assertEqual(hashlib.sha256(prg).hexdigest(), PREVIOUS_PRG_SHA)

    @unittest.skipUnless(os.environ.get('MEGA65_ROM'), 'Set MEGA65_ROM for real V920395 cursor checks')
    def test_actual_rom_cursor_disabled_state_survives_engine_init(self):
        rom = Path(os.environ['MEGA65_ROM']).read_bytes()
        self.assertEqual(hashlib.sha256(rom).hexdigest(), ROM_SHA)
        machine = Machine(original_record()).execute(NAMES['prepare'])
        machine.memory.data[0x111f:0x1124] = b'\x00\x10\x01\x20\x01'
        machine.memory.data[0x0800] = 0x20
        machine.memory.data[0xd800] = 1
        machine.execute(NAMES['init_objects'])
        blink(machine, rom)
        self.assertEqual(machine.memory.data[0x111f:0x1124], b'\x00\x10\x01\x20\x01')
        self.assertEqual(machine.memory.data[0x0800], 0x20)
        # Replay the old assembled object-copy instructions to demonstrate the
        # bug using the same machine and the actual ROM code.
        for address in (0xbadc, 0xbae2, 0xbae8):
            machine.memory.data[address+2] -= 6
        machine.execute(NAMES['v014_copy_records'])
        blink(machine, rom)
        self.assertEqual(machine.memory.data[0x1120], 0)  # enabled accidentally
        self.assertEqual(machine.memory.data[0x1121], 255)  # long invisible interval

    @unittest.skipUnless(os.environ.get('MEGA65_ROM'), 'Set MEGA65_ROM for real V920395 cursor checks')
    def test_actual_rom_blink_saves_rrb_colour_when_old_copy_enables_cursor(self):
        rom = Path(os.environ['MEGA65_ROM']).read_bytes()
        self.assertEqual(hashlib.sha256(rom).hexdigest(), ROM_SHA)
        machine = Machine(original_record()).execute(NAMES['prepare'])
        for address in (0xbadc, 0xbae2, 0xbae8):
            machine.memory.data[address+2] -= 6
        machine.execute(NAMES['v014_copy_records'])
        machine.memory.data[0xc4:0xc8] = b'\x00\x08\x00\x00'
        machine.memory.data[0xd061] = 8
        machine.memory.data[0xec] = 0
        machine.memory.data[0xf1] = 1
        machine.memory.data[0x0800] = 0x20
        machine.memory.data[0xd800] = 2  # red byte while RRB colour RAM is active
        machine.memory.data[0x1121] = 1
        blink(machine, rom)
        self.assertEqual(machine.memory.data[0x1123], 2)
        self.assertEqual(machine.memory.data[0x0800], 0xa0)
        machine.memory.data[0xd800] = 1  # exit's BASIC colour restoration
        machine.memory.data[0x1121] = 1
        blink(machine, rom)
        self.assertEqual(machine.memory.data[0xd800], 2)  # stale RRB colour restored
        self.assertEqual(machine.memory.data[0x0800], 0x20)


# SHA256 of releases/stage_3b2/STAGE3B2.PRG at commit 778b7d4.
PREVIOUS_PRG_SHA = '9669f87d80f5fa5d768294fb429a4ca295aca3b3e9627ef8b6064edb2627ea05'
