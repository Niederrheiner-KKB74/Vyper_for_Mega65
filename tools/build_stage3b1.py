#!/usr/bin/env python3
"""Build Stage 3b-1 without changing either archived baseline (Python 3 + Java)."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
KICKASS_SHA256 = '9592a39336e73a1db8b4a7749256d62d29b113b1c7f0f6c86ea43870ebd9ae1f'
BASELINE_ZIP_SHA256 = '89380c289e5b706278a6c70fffd85de64350739db99031504d255540f252f23a'
DATA_SHA256 = {
    'VYLV.DAT': 'c99bc1262a10babc84f0ae7eb6ff019faccdeb0382711f99ffe6c23023d7d283',
    'VYGR.DAT': 'cbad5d717a4890276a9408c6784500f8449d45ae90f0f4d4251d596b8a2563eb',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def baseline_files():
    archive = ROOT / 'releases/stage_2ja_stable/Stage_2ja_STABLE_ARCHIVE.zip'
    with zipfile.ZipFile(archive) as z:
        packed = z.read('Stage_2ja_STABLE_ARCHIVE/vyper_rrb_v014_stage2ja_build.zip')
    if sha(packed) != BASELINE_ZIP_SHA256:
        raise ValueError('Stage-2ja archive checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(packed)) as z:
        if z.testzip() is not None:
            raise ValueError('Stage-2ja archive CRC mismatch')
        return {i.filename: z.read(i) for i in z.infolist() if not i.is_dir()}


def verify_engine(prg, baseline):
    """Only the BASIC SYS target and the formerly unused preload area may differ."""
    if len(prg) != len(baseline) or prg[:2] != b'\x01\x20':
        raise ValueError('PRG load address/size changed')
    for address in range(0x2100, 0xca00):
        if not 0x4800 <= address < 0x5000:
            offset = 2 + address - 0x2001
            if prg[offset] != baseline[offset]:
                raise ValueError(f'Stage-2ja engine changed at ${address:04x}')
    expected = bytes.fromhex('0c200a009e3138343332000000')
    if prg[2:2+len(expected)] != expected:
        raise ValueError('BASIC SYS 18432 header mismatch')


def build_disk(entries):
    """1581 D81: track 40 header/BAM/directory, 254 payload bytes per sector."""
    image = bytearray(80 * 40 * 256)
    used = {(40, s) for s in range(4)}
    free_sectors = [(t, s) for t in range(1, 81) if t != 40 for s in range(40)]

    def put(t, s, data):
        offset = ((t-1)*40+s)*256
        image[offset:offset+256] = data

    def pet(text, size):
        return text.upper().encode('ascii').ljust(size, b'\xa0')

    directory = bytearray(256)
    directory[:2] = bytes((0, 255))
    for i, (name, payload, kind) in enumerate(entries):
        count = (len(payload)+253)//254
        chain, free_sectors = free_sectors[:count], free_sectors[count:]
        if len(chain) != count or not chain:
            raise ValueError('Disk full or empty file')
        used.update(chain)
        for j, (t, s) in enumerate(chain):
            part = payload[j*254:(j+1)*254]
            block = bytearray(256)
            block[:2] = bytes(chain[j+1]) if j+1 < count else bytes((0, len(part)+1))
            block[2:2+len(part)] = part
            put(t, s, block)
        offset = 2+i*32
        directory[offset] = kind
        directory[offset+1:offset+3] = bytes(chain[0])
        directory[offset+3:offset+19] = pet(name, 16)
        directory[offset+28:offset+30] = struct.pack('<H', count)
    put(40, 3, directory)
    header = bytearray(256)
    header[:4] = bytes((40, 3, 0x44, 0))
    header[4:20] = pet('VYPER STAGE 3B1', 16)
    header[20:29] = b'\xa0\xa03B\xa03D\xa0\xa0'
    put(40, 0, header)
    for index in range(2):
        bam = bytearray(256)
        bam[:8] = bytes((40, 2, 0x44, 0xbb, 0x33, 0x42, 0xc0, 0)) if index == 0 else bytes((0, 255, 0x44, 0xbb, 0x33, 0x42, 0xc0, 0))
        for j in range(40):
            t = index*40+j+1
            free = [s for s in range(40) if (t, s) not in used]
            offset = 16+j*6
            bam[offset] = len(free)
            for s in free:
                bam[offset+1+s//8] |= 1 << (s%8)
        put(40, index+1, bam)
    return bytes(image)


def verify_disk(image, entries):
    if len(image) != 819200:
        raise ValueError('D81 size mismatch')
    def get(t, s):
        if not 1 <= t <= 80 or not 0 <= s < 40:
            raise ValueError('Invalid sector pointer')
        offset = ((t-1)*40+s)*256
        return image[offset:offset+256]
    if get(40, 0)[:4] != bytes((40, 3, 0x44, 0)):
        raise ValueError('D81 header mismatch')
    directory = get(40, 3)
    if directory[:2] != bytes((0, 255)):
        raise ValueError('Directory termination mismatch')
    occupied = {(40, s) for s in range(4)}
    report = []
    for i, (name, data, kind) in enumerate(entries):
        offset = 2+i*32
        if directory[offset] != kind or directory[offset+3:offset+19] != name.encode().ljust(16, b'\xa0'):
            raise ValueError('Directory name/type mismatch')
        t, s = directory[offset+1:offset+3]
        collected = bytearray()
        blocks = 0
        while t:
            if (t, s) in occupied:
                raise ValueError('Cross-linked/cyclic file chain')
            occupied.add((t, s))
            blocks += 1
            block = get(t, s)
            nt, ns = block[:2]
            if not nt and not 1 <= ns <= 255:
                raise ValueError('Invalid last-sector length')
            collected += block[2:256 if nt else ns+1]
            t, s = nt, ns
        if bytes(collected) != data or blocks != int.from_bytes(directory[offset+28:offset+30], 'little'):
            raise ValueError(f'Disk file verification failed: {name}')
        report.append({'name': name, 'bytes': len(data), 'blocks': blocks, 'sha256': sha(data)})
    for t in range(1, 81):
        bam = get(40, 1 if t <= 40 else 2)
        if bam[2:6] != b'\x44\xbb3B':
            raise ValueError('BAM version/ID mismatch')
        offset = 16+((t-1)%40)*6
        free = 0
        for s in range(40):
            is_free = bool(bam[offset+1+s//8] & (1 << (s%8)))
            if is_free == ((t, s) in occupied):
                raise ValueError('BAM allocation mismatch')
            free += is_free
        if bam[offset] != free:
            raise ValueError('BAM free-sector count mismatch')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kickass', default=os.environ.get('KICKASS_JAR'), help='Official KickAssembler 5.25 JAR')
    parser.add_argument('--output', type=Path, default=ROOT/'releases/stage_3b1')
    args = parser.parse_args()
    if not args.kickass:
        parser.error('--kickass or KICKASS_JAR is required')
    jar = Path(args.kickass).resolve()
    if sha(jar.read_bytes()) != KICKASS_SHA256:
        raise ValueError('Expected pinned official KickAssembler 5.25 JAR; see docs/stage3b1.md')
    baseline = baseline_files()
    source = ROOT/'src/engine/stage3b1.asm'
    # Only the SYS target changes in the archived engine source itself.
    archived_source = baseline['vyper_rrb_v014_stage2ja.asm'].decode()
    if archived_source.replace('.text "8448"', '.text "18432"', 1) not in source.read_text():
        raise ValueError('Archived Stage-2ja source modified beyond SYS target')
    assets = []
    for name, length, checksum in [('VYLV.DAT', 81793, 0x5ca2), ('VYGR.DAT', 30888, 0x1fe9)]:
        data = (ROOT/'assets'/name).read_bytes()
        if len(data) != length or sha(data) != DATA_SHA256[name] or sum(data) & 0xffff != checksum:
            raise ValueError(f'Original data mismatch: {name}')
        assets.append((name, data, 0x81))
    with tempfile.TemporaryDirectory(prefix='vyper-stage3b1-') as temporary:
        work = Path(temporary)
        for name, data in baseline.items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                target = work/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        shutil.copyfile(source, work/'STAGE3B1.asm')
        command = ['java', '-jar', str(jar), 'STAGE3B1.asm', '-o', 'STAGE3B1.PRG', '-symbolfile', '-showmem']
        result = subprocess.run(command, cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout, end='')
        result.check_returncode()
        prg = (work/'STAGE3B1.PRG').read_bytes()
        verify_engine(prg, baseline['vyper_rrb_v014_stage2ja.prg'])
        entries = [('STAGE3B1', prg, 0x82), *assets]
        disk = build_disk(entries)
        files = verify_disk(disk, entries)
        symbols = (work/'STAGE3B1.sym').read_text()
        end = re.search(r'\.label loader_end=\$([0-9a-f]+)', symbols)
        if not end or int(end[1], 16) > 0x5000:
            raise ValueError('Preloader memory bound missing/exceeded')
        report = {
            'assembler': 'KickAssembler 5.25', 'assembler_sha256': KICKASS_SHA256,
            'engine_bytes': 'unchanged at $2100-$C9FF outside preload gap $4800-$4FFF',
            'loader_end_exclusive': f'${int(end[1],16):04X}',
            'files': files, 'runtime_xemu': 'NOT RUN',
        }
        outputs = {
            'STAGE3B1.PRG': prg, 'VYPER_STAGE3B1.d81': disk,
            'stage3b1.asm': source.read_bytes(), 'STAGE3B1.sym': symbols.encode(),
            'memory-map.txt': result.stdout[result.stdout.index('Memory Map'):].split('Writing Symbol file')[0].encode(),
            'build-report.json': (json.dumps(report, indent=2)+'\n').encode(),
        }
        outputs['SHA256SUMS.txt'] = ''.join(f'{sha(data)}  {name}\n' for name, data in sorted(outputs.items())).encode()
        args.output.mkdir(parents=True, exist_ok=True)
        for name, data in outputs.items():
            (args.output/name).write_bytes(data)
    print('Verified: unchanged engine bytes, original assets, D81 chains/block counts/BAM.')
    print(f'Artifacts: {args.output.resolve()}')


if __name__ == '__main__':
    main()
