"""Original-player regression: assembled CPU/DMA/palette/RRB models, not XEMU."""
import os
from pathlib import Path
import sys
import unittest

import test_stage3b2_runtime as R
import test_stage3b2_exit as EXIT

sys.path.insert(0, str(R.ROOT/'tools'))
import build_stage3b3 as BUILD

ARTIFACTS = R.ROOT/'releases/stage_3b3'
NAMES = BUILD.symbols((ARTIFACTS/'STAGE3B3.sym').read_text())
PLAYER = R.ROOT/'assets/player'


class PaletteMemory:
    def __init__(self, base):
        self.base = base
        self.banks = [[bytearray([bank*41+c]*256) for c in range(3)] for bank in range(4)]

    @property
    def data(self):
        return self.base.data

    def __getitem__(self, address):
        if 0xd100 <= address < 0xd400:
            return self.banks[self.data[0xd070] >> 6][(address-0xd100)//256][address & 255]
        return self.base[address]

    def __setitem__(self, address, value):
        if 0xd100 <= address < 0xd400:
            self.banks[self.data[0xd070] >> 6][(address-0xd100)//256][address & 255] = value
        self.base[address] = value


class Machine(R.Machine):
    def __init__(self, record=None):
        super().__init__(record)
        prg = (ARTIFACTS/'STAGE3B3.PRG').read_bytes()
        self.memory.data[0x2001:0x2001+len(prg)-2] = prg[2:]
        if record is not None:
            self.memory.data[0x7600:0x7951] = record
        self.memory = PaletteMemory(self.memory)
        self.cpu.memory = self.memory
        self.before = bytes(self.memory.data)


def begin(machine):
    machine.cpu.pc = 0x2100
    machine.cpu.sp = 0xfd
    machine.cpu.stPushWord(0x01ff)
    for _ in range(100_000):
        if machine.cpu.pc == NAMES['main_loop']:
            return
        machine.cpu.step()
    raise AssertionError('Engine did not start')


def frame(machine, key=0, buttons=255):
    machine.memory.data[0xdc00] = buttons
    for i in range(100_000):
        if machine.cpu.pc in (NAMES['main_loop'], 0x0200) and i:
            return
        if machine.cpu.pc == 0xffe4:
            machine.cpu.a = key
            machine.cpu.pc = machine.cpu.stPopWord()+1
        else:
            machine.cpu.step()
    raise AssertionError('Engine frame did not terminate')


class PlayerTests(unittest.TestCase):
    def test_approved_pixels_nibbles_and_palette(self):
        BUILD.verify_player_assets()
        sprite = (PLAYER/'player_sprite.bin').read_bytes()
        ncm = (PLAYER/'player_ncm.bin').read_bytes()
        self.assertEqual(ncm, bytes((b >> 4) | ((b & 15) << 4) for b in sprite))
        self.assertEqual((ARTIFACTS/'STAGE3B3.PRG').read_bytes()[0x3600-0x2001+2:0x3680-0x2001+2], ncm)

    def test_loader_original_data_and_disk(self):
        machine = Machine().execute()
        self.assertEqual(machine.error, 0)
        for name, address in (('VYLV.DAT', 0x40000), ('VYGR.DAT', 0x54000)):
            payload = (R.ROOT/'assets'/name).read_bytes()
            self.assertEqual(machine.memory.data[address:address+len(payload)], payload)
        self.assertIn(b'LOADED AND VERIFIED', machine.messages)
        prg = (ARTIFACTS/'STAGE3B3.PRG').read_bytes()
        BUILD.verify_engine(prg, NAMES)
        entries = [('STAGE3B3', prg, 0x82), *[(name, (R.ROOT/'assets'/name).read_bytes(), 0x81) for name in ('VYLV.DAT', 'VYGR.DAT')]]
        BUILD.BASE.verify_disk((ARTIFACTS/'VYPER_STAGE3B3.d81').read_bytes(), entries)

    def test_own_palette_bank_survives_enemy_palette_changes(self):
        machine = Machine()
        bank0 = [bytes(channel) for channel in machine.memory.banks[0]]
        machine.execute(NAMES['player_palette_init'])
        approved = [(PLAYER/f'player_palette_{c}.bin').read_bytes() for c in 'rgb']
        self.assertEqual(machine.memory.data[0xd070], 0xdb)
        for c in range(3):
            self.assertEqual(machine.memory.banks[3][c][:16], approved[c])
            self.assertEqual(bytes(machine.memory.banks[0][c]), bank0[c])
        # A future enemy palette update touches its own mapped bank only.
        machine.memory[0xd070] = 0x5b  # map bank 1, preserve primary/alternate selection
        for c in range(3):
            for i in range(256):
                machine.memory[0xd100+c*256+i] = i ^ 255
        for c in range(3):
            self.assertEqual(machine.memory.banks[3][c][:16], approved[c])

    def test_player_static_orbit_and_enemy_animation_retained(self):
        machine = Machine(R.original_record()).execute(NAMES['prepare'])
        self.assertEqual(machine.error, 0)
        machine.execute(NAMES['player_init'])
        expected = (PLAYER/'player_ncm.bin').read_bytes()
        initial_orbit = bytes(machine.memory.data[0xc940:0xc9c0])
        for _ in range(16):
            for name in ('advance_animation', 'v012a_capture_animation', 'animate'):
                machine.execute(NAMES[name])
            self.assertEqual(machine.memory.data[0xc840:0xc8c0], expected)
            self.assertEqual(machine.memory.data[0xc800:0xc840], bytes(64))
            self.assertEqual(machine.memory.data[0xc8c0:0xc900], bytes(64))
        self.assertNotEqual(machine.memory.data[0xc940:0xc9c0], initial_orbit)
        types = R.DATA.graphics_types((R.ROOT/'assets/VYGR.DAT').read_bytes())
        self.assertEqual(machine.memory.data[0x9840:0x98c0], types[11]['frames'][0])

    def test_all_motion_controls_and_rrb_clearing_match_stable_engine(self):
        old = R.Machine().execute()
        new = Machine().execute()
        begin(old)
        begin(new)
        expected = (PLAYER/'player_ncm.bin').read_bytes()
        for i in range(56):
            key = {5: 0x2b, 9: 0x20, 15: 0x20, 23: 0x2d}.get(i, 0)
            buttons = (0xfb, 0xf7, 0xfe, 0xfd, 0xff)[i % 5]
            frame(old, key, buttons)
            frame(new, key, buttons)
            for low, high in ((0x1600, 0x1920), (0x5000, 0x57d0), (0xc900, 0xca00), (0x9800, 0x9900)):
                self.assertEqual(new.memory.data[low:high], old.memory.data[low:high], (i, hex(low)))
            self.assertEqual(new.memory.data[0xc840:0xc8c0], expected)
            for name in ('s2ja_frame', 'anim_tick', 'anim_speed', 'anim_paused'):
                self.assertEqual(new.memory.data[NAMES[name]], old.memory.data[NAMES[name]])
            player_fragments = 0
            for row in range(2, 23):
                for slot in range(8):
                    pos = row*80+42+slot*4
                    glyph = int.from_bytes(new.memory.data[0x5000+pos+2:0x5000+pos+4], 'little')
                    if new.memory.data[0xd800+pos] != 0x90:
                        continue  # unused slot/terminator
                    player = 0x321 <= glyph <= 0x323
                    self.assertEqual(new.memory.data[0xd800+pos+1], 0x60 if player else 0)
                    if player:
                        player_fragments += 1
            self.assertIn(player_fragments, (2, 3))

    def test_exit_preserves_kernal_video_colours_and_restart(self):
        machine = Machine().execute()
        # Model the SYS cursor-disable state, without overwriting it on exit.
        machine.memory.data[0x111f:0x1124] = b'\x00\x10\x01\x20\x01'
        kernel = bytes(machine.memory.data[0x1000:0x1600])
        registers = (0xd020, 0xd021, 0xd030, 0xd031, 0xd054, 0xd05d,
                     0xd058, 0xd059, 0xd05e, 0xd060, 0xd061, 0xd062, 0xd063,
                     0xd064, 0xd065, 0xd068, 0xd069, 0xd06a, 0xd07b,
                     0xd06b, 0xd057, 0xd06c, 0xd06d, 0xd06e, 0xd070)
        before = {r: machine.memory.data[r] for r in registers}
        colour = bytes(machine.memory.data[0xd800:0xe000])
        for _ in range(2):
            begin(machine)
            for _ in range(4):
                frame(machine)
            if os.environ.get('MEGA65_ROM'):
                import hashlib
                rom = Path(os.environ['MEGA65_ROM']).read_bytes()
                self.assertEqual(hashlib.sha256(rom).hexdigest(), EXIT.ROM_SHA)
                pc = machine.cpu.pc
                EXIT.blink(machine, rom)
                machine.cpu.pc = pc
                machine.cpu.sp = 0xfd
                machine.cpu.stPushWord(0x01ff)
            frame(machine, 0x58)
            self.assertEqual(machine.cpu.pc, 0x0200)
            self.assertEqual({r: machine.memory.data[r] for r in registers}, before)
            self.assertEqual(machine.memory.data[0xd800:0xe000], colour)
            self.assertEqual(machine.memory.data[0x1000:0x1600], kernel)
            self.assertEqual(machine.memory.data[0xc840:0xc8c0], (PLAYER/'player_ncm.bin').read_bytes())

    def test_runtime_dma_failure_uses_original_exit(self):
        machine = Machine(R.original_record()).execute(NAMES['prepare'])
        self.assertEqual(machine.error, 0)
        machine.memory.base.corrupt_dma = True
        machine.cpu.pc = NAMES['animate']
        machine.cpu.sp = 0xfd
        machine.cpu.stPushWord(0x01ff)
        machine.cpu.stPushWord(0x22a7)
        machine.execute()
        self.assertEqual(machine.error, 4)
        self.assertEqual(machine.cpu.pc, 0x0200)
        self.assertEqual(machine.messages, b'')


if __name__ == '__main__':
    unittest.main(verbosity=2)
