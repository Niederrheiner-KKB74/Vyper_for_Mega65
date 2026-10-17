#!/usr/bin/env python3
"""Reproduce the user-provided Stage10b1b hardware comparisons; no builds or writes to inputs."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
import compare_stage10b1b as c

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / 'docs/diagnostics/stage10b1b/hardware_20261017'

def directory(data):
    if len(data) != 819200:
        raise ValueError('Expected a complete D81')
    t, s = 40, 3
    seen, names = set(), []
    while t:
        if not 1 <= t <= 80 or not 0 <= s < 40 or (t, s) in seen:
            raise ValueError('Invalid/cyclic D81 directory')
        seen.add((t, s))
        off = ((t - 1) * 40 + s) * 256
        b = data[off:off + 256]
        for i in range(8):
            e = b[2 + 32*i:32 + 32*i]
            if e[0]:
                names.append(e[3:19].rstrip(b'\xa0').decode('ascii'))
        t, s = b[:2]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate directory names')
    return names

def write(path, obj):
    path.write_text(json.dumps(obj, indent=2) + '\n')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inputs', type=Path, default=DEFAULT/'inputs')
    ap.add_argument('--output', type=Path, default=DEFAULT)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    schema = json.loads(c.DEFAULT.read_text())
    manifest = {'provenance': 'User: disk1 scenes A-D; disk2 A to B to A; photographs from original hardware. H labels are manual.',
                'inputs': [], 'pairs': [], 'cross_platform': [], 'limitations': [
                    'Disk2 preserves only final A sequence3 and B sequence2. Initial A sequence1 was overwritten.',
                    'Legacy *_XEMU_HARDWARE_PRE reports use supplemental local XEMU; *_USER_XEMU_HARDWARE_* use newly uploaded user data.',
                    'Images are observations, not pixel-exact measurements or a recording of renderer internal state.']}
    parsed = {}
    for ix in (1, 2):
        path = args.inputs / f'VYPER_STAGE10B1B_Mega65_{ix}.d81'
        data = path.read_bytes()
        names = directory(data)
        wanted = ['STAGE10B1B'] + [f'V1B{scene}H.{phase}' for scene in ('ABCD' if ix == 1 else 'AB') for phase in ('PRE', 'PST')]
        if sorted(names) != sorted(wanted):
            raise ValueError(f'Unexpected file set in {path.name}: {names}')
        if c.disk_file(data, 'STAGE10B1B') != (ROOT/'releases/stage_10b1b/STAGE10B1B.PRG').read_bytes():
            raise ValueError('Uploaded program differs from released program')
        manifest['inputs'].append({'file': path.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'directory': names, 'program_matches_release': True})
        for name in names[1:]:
            raw = c.disk_file(data, name)
            a = c.parse(raw, schema)
            if a['platform_label'] != 'H' or not c.configuration(a, schema)['profile_E_constant_checks_pass']:
                raise ValueError(f'Invalid hardware configuration: {name}')
            parsed[ix, a['scene'], a['phase']] = a
            (args.output/f'disk{ix}_{name}').write_bytes(raw)
            write(args.output/f'disk{ix}_{name}.json', c.summary(a, schema))
        for scene in ('ABCD' if ix == 1 else 'AB'):
            a, b = parsed[ix, scene, 'PRE'], parsed[ix, scene, 'POST']
            comp = c.compare(a, b, schema, require_pair=True)
            write(args.output/f'disk{ix}_{scene}_PRE_POST.json', comp)
            manifest['pairs'].append({'disk': ix, 'scene': scene, 'sequence': a['sequence'], 'error': b['measured_export_error'],
                'non_annotation_different_bytes': comp['non_annotation_different_bytes'],
                'stable_bucket_differences': comp['unexpected_stable_register_differences']})
            x = c.parse((ROOT/f'docs/diagnostics/stage10b1b/V1B{scene}X.PRE').read_bytes(), schema)
            comp = c.compare(x, a, schema)
            write(args.output/f'disk{ix}_{scene}_XEMU_HARDWARE_PRE.json', comp)
            manifest['cross_platform'].append({'disk': ix, 'scene': scene,
                'geometry_equal': comp['left']['geometry'] == comp['right']['geometry'],
                'memory_differences': [{'name': r['name'], 'bytes': r['different_bytes']} for r in comp['memory_comparison'] if r['different_bytes']]})
    comp = c.compare(parsed[1, 'A', 'PRE'], parsed[2, 'A', 'PRE'], schema)
    write(args.output/'A_first_vs_returned.json', comp)
    manifest['A_comparison'] = {'same_session': False, 'left_sequence': 1, 'right_sequence': 3,
        'stable_bucket_differences': comp['unexpected_stable_register_differences'],
        'memory_differences': [{'name': r['name'], 'bytes': r['different_bytes']} for r in comp['memory_comparison'] if r['different_bytes']]}
    manifest['user_xemu_pairs'] = []
    manifest['user_cross_platform'] = []
    xparsed = {}
    for ix in (1, 2):
        path = args.inputs/f'VYPER_STAGE10B1B_XEMU_{ix}.d81'
        data = path.read_bytes()
        names = directory(data)
        wanted = ['STAGE10B1B'] + [f'V1B{scene}X.{phase}' for scene in ('ABCD' if ix == 1 else 'AB') for phase in ('PRE', 'PST')]
        if sorted(names) != sorted(wanted) or c.disk_file(data, 'STAGE10B1B') != (ROOT/'releases/stage_10b1b/STAGE10B1B.PRG').read_bytes():
            raise ValueError('Unexpected XEMU disk contents/program')
        manifest['inputs'].append({'file': path.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'directory': names, 'program_matches_release': True})
        for name in names[1:]:
            raw = c.disk_file(data, name)
            a = c.parse(raw, schema)
            if a['platform_label'] != 'X' or not c.configuration(a, schema)['profile_E_constant_checks_pass']:
                raise ValueError('Invalid user XEMU snapshot')
            xparsed[ix, a['scene'], a['phase']] = a
            (args.output/f'xemu_disk{ix}_{name}').write_bytes(raw)
        for scene in ('ABCD' if ix == 1 else 'AB'):
            a, b = xparsed[ix, scene, 'PRE'], xparsed[ix, scene, 'POST']
            comp = c.compare(a, b, schema, require_pair=True)
            write(args.output/f'xemu_disk{ix}_{scene}_PRE_POST.json', comp)
            manifest['user_xemu_pairs'].append({'disk': ix, 'scene': scene, 'sequence': a['sequence'], 'non_annotation_different_bytes': comp['non_annotation_different_bytes'], 'stable_bucket_differences': comp['unexpected_stable_register_differences']})
            for phase in ('PRE', 'POST'):
                comp = c.compare(xparsed[ix, scene, phase], parsed[ix, scene, phase], schema)
                write(args.output/f'disk{ix}_{scene}_USER_XEMU_HARDWARE_{phase}.json', comp)
                manifest['user_cross_platform'].append({'disk': ix, 'scene': scene, 'phase': phase, 'geometry_equal': comp['left']['geometry'] == comp['right']['geometry'], 'stable_bucket_differences': comp['unexpected_stable_register_differences'], 'memory_differences': [{'name': r['name'], 'bytes': r['different_bytes']} for r in comp['memory_comparison'] if r['different_bytes']]})
    comp = c.compare(xparsed[1, 'A', 'PRE'], xparsed[2, 'A', 'PRE'], schema)
    write(args.output/'XEMU_A_first_vs_returned.json', comp)
    manifest['user_xemu_A_comparison'] = {'same_session': False, 'left_sequence': 1, 'right_sequence': 3, 'stable_bucket_differences': comp['unexpected_stable_register_differences'], 'memory_differences': [{'name': r['name'], 'bytes': r['different_bytes']} for r in comp['memory_comparison'] if r['different_bytes']]}
    path = args.inputs/'XEMU_A to D.zip'
    with zipfile.ZipFile(path) as z:
        if sorted(z.namelist()) != sorted(f'XEMU_{scene}_{phase}.png' for scene in 'ABCD' for phase in ('PRE', 'PST')):
            raise ValueError('Unexpected user XEMU screenshot set')
        photos = [{'file': n, 'bytes': len(z.read(n)), 'sha256': hashlib.sha256(z.read(n)).hexdigest()} for n in sorted(z.namelist())]
    manifest['inputs'].append({'file': path.name, 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'screenshots': photos})
    # All explicitly initialized scene palette entries, not all inherited palette RAM.
    x = c.region(xparsed[1, 'A', 'PRE'], 'palettes')
    h = c.region(parsed[1, 'A', 'PRE'], 'palettes')
    indices = {1: [0, 1, *range(16, 32), 48, 49, 50, 51], 2: [1]}
    manifest['explicit_palette_entries_equal'] = all(x[bank*768+channel*256+i] == h[bank*768+channel*256+i]
        for bank, entries in indices.items() for i in entries for channel in range(3))
    manifest['explicit_palette_indices'] = indices
    path = args.inputs/'MEGA65_A_to_D.zip'
    raw = path.read_bytes()
    with zipfile.ZipFile(path) as z:
        if sorted(z.namelist()) != sorted(f'MEGA65_{scene}_{phase}.jpg' for scene in 'ABCD' for phase in ('PRE', 'PST')):
            raise ValueError('Unexpected photograph set')
        photos = [{'file': n, 'bytes': len(z.read(n)), 'sha256': hashlib.sha256(z.read(n)).hexdigest()} for n in sorted(z.namelist())]
    manifest['inputs'].append({'file': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'photographs': photos})
    write(args.output/'results.json', manifest)
    print(f"Validated {len(parsed)+len(xparsed)} snapshots / {len(manifest['pairs'])+len(manifest['user_xemu_pairs'])} pairs, 16 original images; results: {args.output}")

if __name__ == '__main__':
    main()
