#!/usr/bin/env python3
"""Bounded audit of original level records against Stage 4c and proposed Stage 5a.
No original level bytes or unconfirmed mappings are changed.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
import analyze_stage3b2_data as DATA
from analyze_attack_descriptors import decode
ROOT = Path(__file__).resolve().parents[1]

def audit(root=ROOT):
    raw = (root/'assets/VYLV.DAT').read_bytes()
    graphics = (root/'assets/VYGR.DAT').read_bytes()
    records = DATA.level_records(raw)
    types = DATA.graphics_types(graphics)
    with zipfile.ZipFile(root/'assets/vyper_all_enemy_types_exact_ncm.zip') as archive:
        if archive.testzip() is not None: raise ValueError('Original graphics archive CRC failed')
        for item in types:
            for i, frame in enumerate(item['frames']):
                if archive.read(f"type_{item['type']:02d}/anim_{i:02d}_ncm.bin") != frame:
                    raise ValueError('Original frame mismatch')
    mapping = json.loads((root/'assets/vylv_vygr_mapping.json').read_text())
    assert len(mapping) == 38 and mapping[14]['vygr_type_1based'] == 15
    rows = []
    for offset, record in records:
        level = DATA.parse_level_record(record)
        enemies = level['enemies']
        groups = level['groups']
        attacks = [bytes.fromhex(h) for h in level['attack_curves_hex']]
        if not 1 <= len(enemies) <= 22 or not 1 <= len(groups) <= 4 or not 1 <= len(attacks) <= 4:
            raise ValueError('Unsupported record cardinality')
        if not 1 <= level['entry_interval'] <= 65535:
            raise ValueError('Invalid entry interval')
        ymin = min(e['formation_y'] for e in enemies)
        required = sorted({e['graphic_type'] for e in enemies})
        frames = []
        for index in required:
            if not 0 <= index < len(mapping): raise ValueError('Graphic index out of bounds')
            m = mapping[index]
            g = types[m['vygr_type_1based']-1]
            frames.append({'vylv_index':index,'vygr_type':g['type'],
                           'mapping_confirmed':m['confirmed'],'frames':g['frame_count'],
                           'all_frame_bytes':128*g['frame_count']})
        group_bounds = []
        for group in groups:
            x,y=group['start_x'],group['start_y']; xs=[x];ys=[y]
            payload=bytes.fromhex(group['curve_hex'])
            if not payload: raise ValueError('Empty entry curve')
            for byte in payload:
                dx,dy=decode(byte);x+=dx;y+=dy;xs.append(x);ys.append(y)
            if min(xs+ys)<-32768 or max(xs+ys)>32767:raise ValueError('Signed coordinate overflow')
            group_bounds.append({'length':len(payload),'x_range':[min(xs),max(xs)],
                                 'y_range':[min(ys),max(ys)],
                                 'last_spawn_delay':(group['enemy_count']-1)*level['entry_interval']})
        if any(e['attack_index']>=len(attacks) for e in enemies):raise ValueError('Attack index out of bounds')
        for enemy in enemies:
            x,y=enemy['formation_x'],enemy['formation_y']-ymin
            for byte in attacks[enemy['attack_index']]:
                dx,dy=decode(byte);x+=dx;y+=dy
                if not -32768<=x<=32767 or not -32768<=y<=32767:
                    raise ValueError('Attack coordinate overflow')
        unused=sorted(set(range(len(attacks)))-{e['attack_index'] for e in enemies})
        fits=all(8<=e['formation_x']<=216 and 0<=e['formation_y']-ymin<=184 for e in enemies)
        if not fits:raise ValueError('Formation and full drift exceed playfield')
        issues=[]
        if len(record)>849:issues.append('record_exceeds_old_849_byte_copy')
        if len(groups)>2:issues.append('more_than_two_entry_groups')
        if len(enemies)!=22:issues.append('variable_enemy_count')
        if any(g['length']>255 for g in group_bounds):issues.append('entry_cursor_requires_word')
        if any(g['last_spawn_delay']>255 for g in group_bounds):issues.append('spawn_delay_requires_word')
        if len(required)>1:issues.append('per_enemy_graphic_source_required')
        short=[i for i,a in enumerate(attacks) if len(a)==1]
        if short:issues.append('unverified_one_byte_attack_semantics')
        rows.append({'level':level['level'],'file_offset':offset,'record_bytes':len(record),
                     'enemy_count':len(enemies),'group_count':len(groups),
                     'entry_interval':level['entry_interval'],'entry_groups':group_bounds,
                     'formation_y_offset':-ymin,'formation_drift_fits':fits,
                     'rrb_peak_bound':len(enemies)+1,'rrb_limit':24,
                     'graphics':frames,'all_frames_bytes':sum(f['all_frame_bytes'] for f in frames),
                     'per_enemy_private_buffer_bytes':len(enemies)*256,
                     'attack_lengths':[len(a) for a in attacks],
                     'attack_indices':[e['attack_index'] for e in enemies],
                     'unused_attack_indices':unused,'short_attack_indices':short,
                     'stage4c_constraints':issues})
    return {'baseline':'stage4c-stable','stage':'5a','implementation_status':'CAPACITY_ANALYSIS',
            'original_data_sha256':{'VYLV.DAT':hashlib.sha256(raw).hexdigest(),
                                    'VYGR.DAT':hashlib.sha256(graphics).hexdigest()},
            'levels':rows,'summary':{'levels':len(rows),'enemies':sum(r['enemy_count'] for r in rows),
            'max_record_bytes':max(r['record_bytes'] for r in rows),
            'max_entry_curve_bytes':max(g['length'] for r in rows for g in r['entry_groups']),
            'max_spawn_delay':max(g['last_spawn_delay'] for r in rows for g in r['entry_groups']),
            'max_graphic_indices':max(len(r['graphics']) for r in rows),
            'max_all_frames_bytes':max(r['all_frames_bytes'] for r in rows),
            'max_rrb_slots':max(r['rrb_peak_bound'] for r in rows),
            'short_attack_levels':[r['level'] for r in rows if r['short_attack_indices']],
            'all_formations_and_drift_fit':all(r['formation_drift_fits'] for r in rows)}}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=ROOT/'docs/stage5a-capacity-analysis.json')
    args=ap.parse_args();result=audit();args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['summary'],indent=2))
if __name__=='__main__':main()
