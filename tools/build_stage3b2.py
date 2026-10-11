#!/usr/bin/env python3
"""Build Level-1 graphics integration; protect every stable Stage-3b-1 artifact."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import build_stage3b1 as BASE
import analyze_stage3b2_data as DATA

ROOT = Path(__file__).resolve().parents[1]

# Exhaustive instruction sites: only the high byte of an absolute object/diagnostic
# operand changes. No code, opcode, immediate, table or exit bytes may change.
RAM_RELOCATION_SITES = (
    0xbadc, 0xbae2, 0xbae8, 0xbaf4, 0xbaf9, 0xbafe, 0xbb01,
    0xbb2a, 0xbb33, 0xbb3d, 0xbb44, 0xbb4e, 0xbb57, 0xbb61, 0xbb68,
    0xbb6e, 0xbb71, 0xbb77, 0xbb7a, 0xbb7d, 0xbb80, 0xbb83, 0xbb86,
    0xbb89, 0xbb8c, 0xbb8f, 0xbb96, 0xbb9c, 0xbb9f, 0xbba2, 0xbba5,
    0xbba8, 0xbbaf, 0xbbb2, 0xbbb5, 0xbbb8, 0xbbbb, 0xbbc2, 0xbbc5,
    0xbbc8, 0xbbcb, 0xbbce, 0xbbd4, 0xbbda, 0xbbe0, 0xbbe4, 0xbbe7,
    0xbbed, 0xbbf3, 0xbc8f, 0xbc95, 0xbcbc, 0xbcc2,
)


def symbols(text):
    return {name: int(value, 16) for name, value in re.findall(r'\.label (\w+)=\$([0-9a-f]+)', text)}


def verify_engine(prg, names):
    baseline = (ROOT/'releases/stage_3b1/STAGE3B1.PRG').read_bytes()
    if len(prg) != len(baseline):
        raise ValueError('Engine image length changed')
    expected = bytearray(baseline)
    def offset(address):
        return address-0x2001+2
    old = symbols((ROOT/'releases/stage_3b1/STAGE3B1.sym').read_text())
    for address in RAM_RELOCATION_SITES:
        at = offset(address)
        operand = int.from_bytes(expected[at+1:at+3], 'little')
        if expected[at] not in (0x8d, 0x9d, 0xad, 0xae, 0xce, 0xee) or not 0x1000 <= operand < 0x1320:
            raise ValueError('Unexpected baseline RAM relocation instruction')
        expected[at+2] += 6
    for address, original, replacement in [(0x2230, 'v014_init_objects', 'init_objects'), (0x22a5, 's2ja_animate_pixies', 'animate')]:
        at = offset(address)
        if expected[at:at+3] != b'\x20'+old[original].to_bytes(2, 'little'):
            raise ValueError('Unexpected baseline call site')
        expected[at+1:at+3] = names[replacement].to_bytes(2, 'little')
    for address, original, replacement in [(0xbcfa, 0x25, 0x61), (0xbcff, 3, 2), (0xbd04, 0x26, 0x62), (0xbd09, 3, 2), (0xbd0e, 0x27, 0x63), (0xbd13, 3, 2)]:
        at = offset(address)
        if expected[at:at+2] != bytes((0xa9, original)):
            raise ValueError('Unexpected baseline path-glyph reference')
        expected[at+1] = replacement
    for low, high in [(0x3200, 0x4000), (0x4800, 0x5000), (0x9800, 0x9900)]:
        expected[offset(low):offset(high)] = prg[offset(low):offset(high)]
    if expected != prg:
        raise ValueError('Unexpected engine change outside graphics patches and RAM relocation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kickass', default=os.environ.get('KICKASS_JAR'))
    parser.add_argument('--output', type=Path, default=ROOT/'releases/stage_3b2')
    args = parser.parse_args()
    if not args.kickass:
        parser.error('--kickass or KICKASS_JAR is required')
    jar = Path(args.kickass).resolve()
    if BASE.sha(jar.read_bytes()) != BASE.KICKASS_SHA256:
        raise ValueError('Expected pinned official KickAssembler 5.25 JAR')
    analysis = DATA.analyze()
    level = analysis['level_1']['parsed_record']
    if len(level['enemies']) != 22 or level['required_vygr_types'] != [12]:
        raise ValueError('This stage targets the confirmed 22 Level-1 enemies of VYGR type 12')
    # Preserve stable sources and binaries; all outputs go to the new release directory.
    source = ROOT/'src/engine/stage3b2.asm'
    assets = []
    for name in ('VYLV.DAT', 'VYGR.DAT'):
        payload = (ROOT/'assets'/name).read_bytes()
        if BASE.sha(payload) != BASE.DATA_SHA256[name]:
            raise ValueError('Original asset checksum mismatch')
        assets.append((name, payload, 0x81))
    with tempfile.TemporaryDirectory(prefix='vyper-stage3b2-') as directory:
        work = Path(directory)
        for name, payload in BASE.baseline_files().items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                target = work/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
        shutil.copyfile(source, work/'STAGE3B2.asm')
        result = subprocess.run(['java', '-jar', str(jar), 'STAGE3B2.asm', '-o', 'STAGE3B2.PRG', '-symbolfile', '-showmem'], cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout, end='')
        result.check_returncode()
        prg = (work/'STAGE3B2.PRG').read_bytes()
        text = (work/'STAGE3B2.sym').read_text()
        names = symbols(text)
        verify_engine(prg, names)
        if names['code_end'] > 0x4000 or names['loader_end'] > 0x5000:
            raise ValueError('Code exceeds free memory regions')
        entries = [('STAGE3B2', prg, 0x82), *assets]
        disk = bytearray(BASE.build_disk(entries))
        header = ((40-1)*40)*256
        disk[header+4:header+20] = b'VYPER STAGE 3B2'.ljust(16, b'\xa0')
        disk = bytes(disk)
        files = BASE.verify_disk(disk, entries)
        report = {'assembler': 'KickAssembler 5.25', 'assembler_sha256': BASE.KICKASS_SHA256,
                  'level': 1, 'enemy_count': 22, 'enemy_offset_computed': level['enemy_offset'],
                  'graphic_index': 14, 'vygr_type': 12, 'mapping_source': 'latest user correction',
                  'movement_bytes': 'same algorithms; two graphics calls, six glyph operands, 53 RAM operand high bytes',
                  'exit_fix': {'objects': '$1600-$18FF', 'diagnostics': '$1900-$191F',
                               'reason': 'ROM V920395 cursor state $111F-$1123 was overwritten by old object copy',
                               'changed_prg_bytes_vs_previous_stage3b2': 53,
                               'rom_sha256': '0f257ca5013e846604af6637bf44146de7500a49c54242a725aeb52cd86af5c1'},
                  'files': files, 'runtime_xemu': 'NOT RUN'}
        outputs = {'STAGE3B2.PRG': prg, 'VYPER_STAGE3B2.d81': disk,
                   'stage3b2.asm': source.read_bytes(), 'STAGE3B2.sym': text.encode(),
                   'memory-map.txt': (result.stdout[result.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode(),
                   'build-report.json': (json.dumps(report, indent=2)+'\n').encode()}
        outputs['SHA256SUMS.txt'] = ''.join(f'{BASE.sha(payload)}  {name}\n' for name, payload in sorted(outputs.items())).encode()
        args.output.mkdir(parents=True, exist_ok=True)
        for name, payload in outputs.items():
            (args.output/name).write_bytes(payload)
    print('Verified variable Level-1 parser, explicit graphics patches, original assets and D81.')


if __name__ == '__main__':
    main()
