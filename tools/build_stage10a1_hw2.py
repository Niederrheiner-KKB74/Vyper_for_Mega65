#!/usr/bin/env python3
"""Assemble HW2 from source and verify against the hardware-confirmed release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import build_stage10a1 as BASE
import d81_highscore as DISK

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'releases/stage_10a/stage10a1_hw'
ORDER = ['VYLV.DAT', 'VYGR.DAT', 'VYCL.DAT', 'VYTI.DAT', 'VYMN.DAT',
         'VYSH.DAT', 'VYSO.DAT', 'VYHS.DAT', 'VYHI.DAT']

def build(jar, output):
    output = Path(output).resolve()
    if output.is_relative_to(ROOT / 'releases'):
        raise ValueError('Use a separate build directory; archived releases are read-only')
    report = BASE.build(jar, output)
    # The ordinary builder uses a different directory order and disk title.
    # Repack its assembled files in exactly the confirmed HW2 disk layout.
    entries = [('STAGE10A1', (output / 'STAGE10A1.PRG').read_bytes(), 0x82)]
    entries += [(n, (output / n).read_bytes(), 0x81) for n in ORDER]
    disk = bytearray(DISK.build_disk(entries))
    head = 39 * 40 * 256
    disk[head+4:head+20] = b'VYPER 10A1 HW2'.ljust(16, b'\xa0')
    DISK.verify_disk(bytes(disk), entries)
    (output / 'VYPER_STAGE10A1_HW2.d81').write_bytes(disk)
    verified = {}
    for line in (REFERENCE / 'SHA256SUMS.txt').read_text().splitlines():
        expected, name = line.split()
        actual = hashlib.sha256((output / name).read_bytes()).hexdigest()
        if hashlib.sha256((REFERENCE / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Reference checksum mismatch: ' + name)
        if actual != expected or (output / name).read_bytes() != (REFERENCE / name).read_bytes():
            raise ValueError('Source build differs from confirmed HW2: ' + name)
        verified[name] = actual
    report['revision'] = '10a1-hw2-source'
    report['hardware_reference'] = {
        'commit': '0b1c083f46dc41e7c6b8fb743b3f39b5a9af09cf',
        'user_confirmation': '2026-10-17; Core 0.97 aaf4542; ROM 920413; PAL',
        'new_runtime_test': False, 'byte_identical_files': verified}
    report['stage10a1']['hud']['geometry'] = {'mode': 'H320', 'CHRXSCL': 120,
        'GOTOX_units': 'logical pixels', 'hud_x': 240, 'NORRDEL': 0}
    ready = report['stage10a1']['get_ready']
    ready.pop('native_X', None)
    ready['logical_X'] = [102, 104]
    (output / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n')
    files = sorted(p for p in output.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.txt')
    (output / 'SHA256SUMS.txt').write_text(''.join(
        f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(output).as_posix()}\n'
        for p in files))
    print('HW2: all four reference artifacts reproduced byte-for-byte from source.')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kickass', default=os.getenv('KICKASS_JAR'))
    parser.add_argument('--output', type=Path, default=ROOT / 'build/stage10a1-hw2')
    args = parser.parse_args()
    if not args.kickass:
        parser.error('--kickass required')
    build(args.kickass, args.output)
