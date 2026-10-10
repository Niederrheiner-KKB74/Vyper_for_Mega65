#!/usr/bin/env python3
"""Build original player integration from stage3b2-stable, without changing it."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import build_stage3b1 as BASE
from build_stage3b2 import symbols

ROOT = Path(__file__).resolve().parents[1]
STABLE_PRG_SHA = '5f49f2cc05765f894aab6034ff3755a2680d15ea53c3790bb663deb7fcaa1dc8'
PLAYER_FILES = ('player_ncm.bin', 'player_palette_r.bin', 'player_palette_g.bin', 'player_palette_b.bin')


def verify_player_assets():
    folder = ROOT/'assets/player'
    rows = (folder/'player_pixels.txt').read_text().splitlines()
    if len(rows) != 16 or any(len(row) != 16 for row in rows):
        raise ValueError('Expected 16x16 original pixel indices')
    pixels = [int(c, 16) for row in rows for c in row]
    if any(p > 8 for p in pixels):
        raise ValueError('Player index outside approved palette')
    packed = bytes(pixels[i] | pixels[i+1] << 4 for i in range(0, 256, 2))
    if (folder/'player_ncm.bin').read_bytes() != packed:
        raise ValueError('Player NCM nibble order or pixels changed')
    sprite = bytes(pixels[i] << 4 | pixels[i+1] for i in range(0, 256, 2))
    if (folder/'player_sprite.bin').read_bytes() != sprite:
        raise ValueError('Player hardware-sprite nibble order changed')
    entries = re.findall(r'Index (\d+): \$([0-9A-Fa-f]{3}) RGB #([0-9A-Fa-f]{6})', (folder/'player_palette.txt').read_text())
    if [int(e[0]) for e in entries] != list(range(9)):
        raise ValueError('Expected approved palette indices 0..8')
    rgb = [bytes.fromhex(e[2]) for e in entries]
    for e, colour in zip(entries, rgb):
        if bytes(int(c, 16)*17 for c in e[1]) != colour:
            raise ValueError('Approved Amiga/RGB palette mismatch')
    for channel, name in enumerate('rgb'):
        if (folder/f'player_palette_{name}.bin').read_bytes() != bytes(c[channel] for c in rgb)+bytes(7):
            raise ValueError('Generated palette differs from approved palette text')


def verify_engine(prg, names):
    old = (ROOT/'releases/stage_3b2/STAGE3B2.PRG').read_bytes()
    if BASE.sha(old) != STABLE_PRG_SHA or len(prg) != len(old):
        raise ValueError('Stable Stage-3b-2 baseline mismatch')
    expected = bytearray(old)
    def offset(address):
        return address-0x2001+2
    for address, original, name in ((0x2224, 0x2c7b, 'player_palette_init'),
                                    (0x2230, 0x34dc, 'player_init'),
                                    (0xbdc5, 0xbdd0, 'player_write_slot')):
        at = offset(address)
        if expected[at:at+3] != b'\x20'+original.to_bytes(2, 'little'):
            raise ValueError('Unexpected baseline call site')
        expected[at+1:at+3] = names[name].to_bytes(2, 'little')
    for address, original in ((0xb8f3, b'\x20\xe7\xb9'), (0xbc59, b'\x9d\x40\xc8'), (0xbc62, b'\x9d\x80\xc8')):
        at = offset(address)
        if expected[at:at+3] != original:
            raise ValueError('Unexpected player animation store')
        expected[at:at+3] = b'\xea'*3
    for low, high in ((0x3600, 0x3800),):
        if any(old[offset(low):offset(high)]):
            raise ValueError('Player region not free in stable baseline')
        expected[offset(low):offset(high)] = prg[offset(low):offset(high)]
    if expected != prg:
        raise ValueError('Unexpected change to loader, movement, enemy graphics, renderer or exit')
    return {'calls': ['$2224', '$2230', '$BDC5'], 'removed_player_animation_writes': ['$B8F3', '$BC59', '$BC62'],
            'new_region': '$3600-$37FF', 'baseline_prg_sha256': STABLE_PRG_SHA,
            'changed_prg_bytes': sum(a != b for a, b in zip(old, prg))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kickass', default=os.environ.get('KICKASS_JAR'))
    parser.add_argument('--output', type=Path, default=ROOT/'releases/stage_3b3')
    args = parser.parse_args()
    if not args.kickass:
        parser.error('--kickass or KICKASS_JAR is required')
    jar = Path(args.kickass).resolve()
    if BASE.sha(jar.read_bytes()) != BASE.KICKASS_SHA256:
        raise ValueError('Expected pinned official KickAssembler 5.25')
    subprocess.run([sys.executable, str(ROOT/'tools/build_player_assets.py')], check=True)
    verify_player_assets()
    source = ROOT/'src/engine/stage3b3.asm'
    assets = []
    for name in ('VYLV.DAT', 'VYGR.DAT'):
        payload = (ROOT/'assets'/name).read_bytes()
        if BASE.sha(payload) != BASE.DATA_SHA256[name]:
            raise ValueError('Original asset mismatch')
        assets.append((name, payload, 0x81))
    with tempfile.TemporaryDirectory(prefix='vyper-stage3b3-') as directory:
        work = Path(directory)
        for name, payload in BASE.baseline_files().items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                target = work/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
        (work/'player_assets').mkdir()
        for name in PLAYER_FILES:
            shutil.copyfile(ROOT/'assets/player'/name, work/'player_assets'/name)
        shutil.copyfile(source, work/'STAGE3B3.asm')
        result = subprocess.run(['java', '-jar', str(jar), 'STAGE3B3.asm', '-o', 'STAGE3B3.PRG', '-symbolfile', '-showmem'], cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout, end='')
        result.check_returncode()
        prg = (work/'STAGE3B3.PRG').read_bytes()
        text = (work/'STAGE3B3.sym').read_text()
        names = symbols(text)
        comparison = verify_engine(prg, names)
        if names['player_source_end'] > 0x3700 or names['player_code_end'] > 0x3800:
            raise ValueError('Player data/code exceeds reserved regions')
        entries = [('STAGE3B3', prg, 0x82), *assets]
        disk = bytearray(BASE.build_disk(entries))
        header = (40-1)*40*256
        disk[header+4:header+20] = b'VYPER STAGE 3B3'.ljust(16, b'\xa0')
        disk = bytes(disk)
        files = BASE.verify_disk(disk, entries)
        report = {'assembler': 'KickAssembler 5.25', 'baseline': 'stage3b2-stable',
                  'comparison': comparison, 'player': {'format': 'NCM, left pixel low nibble',
                  'size': '16x16, 128 bytes', 'palette_bank': 2, 'gotox_colour_byte_1': '$60',
                  'generated_assets': {name: BASE.sha((ROOT/'assets/player'/name).read_bytes()) for name in PLAYER_FILES}},
                  'files': files, 'runtime_xemu': 'NOT RUN; user confirmation required'}
        outputs = {'STAGE3B3.PRG': prg, 'VYPER_STAGE3B3.d81': disk,
                   'stage3b3.asm': source.read_bytes(), 'STAGE3B3.sym': text.encode(),
                   'memory-map.txt': (result.stdout[result.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode(),
                   'build-report.json': (json.dumps(report, indent=2)+'\n').encode()}
        outputs['SHA256SUMS.txt'] = ''.join(f'{BASE.sha(payload)}  {name}\n' for name, payload in sorted(outputs.items())).encode()
        args.output.mkdir(parents=True, exist_ok=True)
        for name, payload in outputs.items():
            (args.output/name).write_bytes(payload)
    print('Verified approved player assets, exact engine patches and D81.')


if __name__ == '__main__':
    main()
