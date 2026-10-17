#!/usr/bin/env python3
"""Stage10a1-HW: MEGA65 hardware fixes as verified binary patches of the released Stage10a1.

KickAssembler 5.25 was not available when this was produced, so the release files of
releases/stage_10a/stage10a1 are patched byte-exactly (every original byte is checked).
The matching source changes are in src/engine/stage10a1_{audio_core,hud,templates,get_ready,game}.asm.
1. Audio DMA: write $D72A/$D72B before $D72C (hardware latches the current address on $D72C).
2. Audio init: test only $D711 bit 7.
3. RRB double buffering ($D051 bit 7 clear) so pixies on the left are completely painted.
4. Game screen: H320 + CHRXSCL 120 instead of H640 + CHRXSCL 60; GOTOX X in logical 320 units
   (hardware scales the whole RRB line buffer incl. GOTOX by CHRXSCL, XEMU only the glyphs).
"""
import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
R=ROOT/'releases/stage_10a/stage10a1'
import d81_highscore as DISK
order=['VYLV.DAT','VYGR.DAT','VYCL.DAT','VYTI.DAT','VYMN.DAT','VYSH.DAT','VYSO.DAT','VYHS.DAT','VYHI.DAT']
def make(prg,files,title=b'VYPER STAGE10A1'):
    entries=[('STAGE10A1',prg,0x82)]+[(n,files[n],0x81) for n in order]
    d=bytearray(DISK.build_disk(entries));head=39*40*256
    d[head+4:head+20]=title.ljust(16,b'\xa0');d=bytes(d)
    DISK.verify_disk(d,entries);return d
import binascii, hashlib
OUT = str(ROOT/'releases/stage_10a/stage10a1_hw')+'/'
prg = bytearray((R/'STAGE10A1.PRG').read_bytes()); BASE = 0x2001
core = bytearray((R/'AUDIO_CORE.PRG').read_bytes())
vyso = bytearray((R/'VYSO.DAT').read_bytes())
log = []
def patch(buf, off, old, new, what):
    old, new = bytes.fromhex(old), bytes.fromhex(new)
    assert len(old) == len(new), what
    if buf[off:off+len(old)] != old:
        raise SystemExit(f'MISMATCH {what}: {buf[off:off+len(old)].hex()} != {old.hex()}')
    buf[off:off+len(new)] = new; log.append(what)
P = lambda addr, old, new, what: patch(prg, addr - BASE + 2, old, new, what)

# ---- Audio core (AUDIO_CORE.PRG, $A000 based) ----
C = lambda addr, old, new, what: patch(core, addr - 0xa000 + 2, old, new, what)
# start_source: write current-address LOW/HIGH before BANK ($D72C latches the address on hardware)
C(0xa181, 'b9f9a49d23d79d2cd7b958a69d2ad7b95aa69d2bd7',
          'b958a69d2ad7b95aa69d2bd7b9f9a49d23d79d2cd7', 'audio: $D72A/$D72B before $D72C')
# audio_init: test only AUDEN (bit7) of $D711, status bits 6/0-2 are read-only on hardware
C(0xa088, 'a9808d11d7cd11d7d019', 'a9808d11d72c11d71019', 'audio: $D711 AUDEN test via BIT/BPL')
vyso[512:512+len(core)-2] = core[2:]
assert (R/'VYSO.DAT').read_bytes()[:512] == vyso[:512]
old_crc = binascii.crc_hqx((R/'VYSO.DAT').read_bytes(), 0xffff); new_crc = binascii.crc_hqx(bytes(vyso), 0xffff)
assert old_crc == 0x9d0f
for lo, hi in ((0x525c, 0x5263), (0x530d, 0x5314)):  # loader CRC compares (pseudopc $A000 code at $5000)
    P(lo, 'c90f', f'c9{new_crc & 255:02x}', 'loader: AUDIO_FILE_CRC low')
    P(hi, 'c99d', f'c9{new_crc >> 8:02x}', 'loader: AUDIO_FILE_CRC high')

# ---- Graphics: H320 + CHRXSCL $78 instead of H640 + 60; all GOTOX X values in 320-pixel units ----
P(0x382e, '09c08d31d0a93c8d5ad0', '09408d31d0a9788d5ad0', 'hud_init: H320 and $D05A=120')
P(0x38ae, '0a20', '1820', 'hud_write_x: GOTOX = logical X (CLC instead of ASL)')
P(0x3b8b, 'a9e0a201', 'a9f0a200', 'lives prefix: GOTOX 480 -> 240')
P(0x3b99, 'a978a202', 'a93ca201', 'lives prefix: GOTOX 632 -> 316')
P(0x3eaf, 'ea0c2e5001020202', 'f506172800010101', 'life icon X 490/524/558/592 -> 245/262/279/296')
for i in range(25):
    P(0x7a00 + 42*i, 'e001', 'f000', f'HUD template row {i}: GOTOX 480 -> 240')
# RRB timing: enable raster-rewrite double buffering ($D051.7 NORRDEL=0). Without it the line
# buffer is read while still being painted; late-painted pixies on the left show black lines.
P(0xbde1, 'eaeaeaeaeaeaeaeaeaea', 'a9008d51d0eaeaeaeaea', 'v014_write_slot: $D051=0 (RRB double buffering)')
P(0x9dfb, 'a9a84c', 'a9544c', 'GAME OVER: GOTOX 168 -> 84')
P(0xaf5f, 'a9cc20', 'a96620', 'GET READY: GOTOX 204 -> 102')
P(0xaf86, 'a9d020', 'a96820', 'PLAYER n: GOTOX 208 -> 104')

files = {n: (R/n).read_bytes() for n in order}; files['VYSO.DAT'] = bytes(vyso)
disk = make(bytes(prg), files, b'VYPER 10A1 HW2')
os.makedirs(OUT, exist_ok=True)
out = {'STAGE10A1.PRG': bytes(prg), 'AUDIO_CORE.PRG': bytes(core), 'VYSO.DAT': bytes(vyso), 'VYPER_STAGE10A1_HW2.d81': disk}
for n, b in out.items(): open(OUT+n, 'wb').write(b)
open(OUT+'SHA256SUMS.txt', 'w').write(''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n, b in sorted(out.items())))
print(f'{len(log)} patches; VYSO CRC ${old_crc:04x} -> ${new_crc:04x}')
for l in log: print(' -', l)
