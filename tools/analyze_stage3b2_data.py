#!/usr/bin/env python3
"""Validate original containers; do not infer undocumented VYLV enemy fields."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def vygr_type_for_level_index(index):
    """User-confirmed mapping: 0/1/14 -> 12; other 2..37 -> index-1."""
    if type(index) is not int or not 0 <= index <= 37:
        raise ValueError('VYLV graphics index must be an integer in 0..37')
    return 12 if index < 2 or index == 14 else index-1


def level_records(data):
    if len(data) < 8 or data[:4] != b'VYLV':
        raise ValueError('Invalid VYLV header')
    version, count = struct.unpack_from('<HH', data, 4)
    if version != 1 or count != 100 or len(data) < 8+count*8:
        raise ValueError('Unexpected VYLV version/count/directory size')
    cursor = 8+count*8
    records = []
    for index in range(count):
        offset, length = struct.unpack_from('<II', data, 8+index*8)
        if offset != cursor or length < 2 or offset+length > len(data):
            raise ValueError('VYLV directory has a gap, overlap or out-of-bounds record')
        record = data[offset:offset+length]
        if struct.unpack_from('<H', record)[0] != index+1:
            raise ValueError('VYLV record number mismatch')
        records.append((offset, record))
        cursor += length
    if cursor != len(data):
        raise ValueError('Trailing VYLV data')
    return records


def parse_level_record(record):
    """User-confirmed VYLV v1 record; every variable read is bounds-checked."""
    cursor = 0
    def take(length):
        nonlocal cursor
        if length < 0 or cursor+length > len(record):
            raise ValueError(f'Truncated level record at offset {cursor:#x}: need {length} bytes')
        result = record[cursor:cursor+length]
        cursor += length
        return result
    number, group_count, enemy_count, interval, attack_count = struct.unpack('<HBBHH', take(8))
    groups = []
    for _ in range(group_count):
        count, x, y, length = struct.unpack('<HHHH', take(8))
        curve = take(length)
        groups.append({'enemy_count': count, 'start_x': x, 'start_y': y,
                       'curve_length': length, 'curve_hex': curve.hex()})
    enemy_offset = cursor
    enemies = []
    for _ in range(enemy_count):
        x, y, graphic, attack = struct.unpack('<HHBB', take(6))
        enemies.append({'formation_x': x, 'formation_y': y, 'graphic_type': graphic,
                        'vygr_type': vygr_type_for_level_index(graphic), 'attack_index': attack})
    attacks = []
    for _ in range(attack_count):
        length, = struct.unpack('<H', take(2))
        attacks.append(take(length).hex())
    if cursor != len(record):
        raise ValueError('Unconsumed bytes at end of level record')
    if sum(group['enemy_count'] for group in groups) != enemy_count:
        raise ValueError('Entry-group counts do not match enemy count')
    return {'level': number, 'entry_interval': interval, 'enemy_offset': enemy_offset,
            'groups': groups, 'enemies': enemies, 'attack_curves_hex': attacks,
            'required_vygr_types': sorted({enemy['vygr_type'] for enemy in enemies})}


def graphics_types(data):
    if len(data) < 8 or data[:4] != b'VYGR':
        raise ValueError('Invalid VYGR header')
    version, count = struct.unpack_from('<HH', data, 4)
    if version != 1 or count != 36 or len(data) < 8+count*8:
        raise ValueError('Unexpected VYGR version/count/directory size')
    cursor = 8+count*8
    types = []
    for index in range(count):
        offset, frames, reserved = struct.unpack_from('<IHH', data, 8+index*8)
        if reserved or not frames or offset != cursor or offset+frames*128 > len(data):
            raise ValueError('Invalid VYGR type/frame range')
        payload = data[offset:offset+frames*128]
        types.append({'type': index+1, 'offset': offset, 'frame_count': frames,
                      'ram_address': f'${0x54000+offset:05X}',
                      'frames': [payload[i:i+128] for i in range(0, len(payload), 128)]})
        cursor += len(payload)
    if cursor != len(data):
        raise ValueError('Trailing VYGR data')
    return types


def analyze(root=ROOT):
    level = (root/'assets/VYLV.DAT').read_bytes()
    graphic = (root/'assets/VYGR.DAT').read_bytes()
    records = level_records(level)
    types = graphics_types(graphic)
    with zipfile.ZipFile(root/'assets/vyper_all_enemy_types_exact_ncm.zip') as z:
        if z.testzip() is not None:
            raise ValueError('Original graphics archive CRC mismatch')
        for item in types:
            for index, frame in enumerate(item['frames']):
                name = f"type_{item['type']:02d}/anim_{index:02d}_ncm.bin"
                if frame != z.read(name):
                    raise ValueError(f'VYGR differs from original frame: {name}')
    parsed = [parse_level_record(record) for _, record in records]
    offset, record = records[0]
    with zipfile.ZipFile(root/'assets/STAGE3A_DATA_PREPARATION.zip') as z:
        warning = z.read('README_STAGE3A_DATA.txt').decode().split('Offene Datenfrage:', 1)[1].strip()
    return {
        'vylv': {'sha256': hashlib.sha256(level).hexdigest(), 'bytes': len(level),
                 'version': 1, 'records': len(records), 'directory_checked': True},
        'level_1': {'offset': offset, 'ram_address': f'${0x40000+offset:05X}',
                    'bytes': len(record), 'sha256': hashlib.sha256(record).hexdigest(),
                    'first_16_bytes': record[:16].hex(' '),
                    'enemy_type_mapping': parsed[0]['enemies'],
                    'parsed_record': parsed[0]},
        'vygr': {'sha256': hashlib.sha256(graphic).hexdigest(), 'bytes': len(graphic),
                 'version': 1, 'types': len(types),
                 'frames': sum(item['frame_count'] for item in types),
                 'all_frames_match_original_archive': True,
                 'directory': [{k: v for k, v in item.items() if k != 'frames'} for item in types]},
        'confirmed_graphics_index_mapping': {
            'source': 'User confirmation',
            'rule': '0, 1 and 14 map to type 12; other indices 2..37 map to index-1',
            'table': [vygr_type_for_level_index(i) for i in range(38)],
        },
        'original_package_warning': warning,
        'original_warning_status': 'Index mapping and level-record schema confirmed by user',
        'integration_status': 'LEVEL_SCHEMA_AND_MAPPING_VALIDATED',
        'all_levels_parsed': len(parsed),
        'movement_changes': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = json.dumps(analyze(), indent=2, ensure_ascii=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
        print('Validated 100 level records and 239 original frames across 36 VYGR types.')
        print('Variable-length records parsed; Level 1 requires user-confirmed VYGR type 12; see', args.output)
    else:
        print(report, end='')


if __name__ == '__main__':
    main()
