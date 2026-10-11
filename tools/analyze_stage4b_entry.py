#!/usr/bin/env python3
"""Bounded Level-1 extraction and explicitly unconfirmed curve hypotheses."""
import argparse,json
from pathlib import Path
from collections import Counter
import analyze_stage3b2_data as DATA
ROOT=Path(__file__).resolve().parents[1]
def analyze():
    data=(ROOT/'assets/VYLV.DAT').read_bytes()
    offset,raw=DATA.level_records(data)[0]
    parsed=DATA.parse_level_record(raw)
    mapping=json.loads((ROOT/'assets/vylv_vygr_mapping.json').read_text())
    groups=[];cursor=8;first=0;table=[]
    for index,g in enumerate(parsed['groups']):
        curve=bytes.fromhex(g['curve_hex']);start=[g['start_x'],g['start_y']]
        variants={}
        for mode in ('sign_magnitude','signed_4bit'):
            def decode(n):return (-(n&7) if n&8 else n) if mode=='sign_magnitude' else (n-16 if n&8 else n)
            dx=[decode(b>>4) for b in curve];dy=[decode(b&15) for b in curve]
            variants[mode]={'unconfirmed':True,'assumed_axis_order':'high nibble X, low nibble Y','assumed_scale':1,'assumed_ticks_per_byte':1,'integrated_end':[start[0]+sum(dx),start[1]+sum(dy)],'first_12_deltas':list(map(list,zip(dx[:12],dy[:12])))}
        groups.append({'group':index,'enemy_count':g['enemy_count'],'first_enemy':first,'last_enemy':first+g['enemy_count']-1,'slot_assignment_status':'contiguous order hypothesis, not interpreter-confirmed','group_record_relative':cursor,'curve_relative':cursor+8,'curve_file_offset':offset+cursor+8,'start_raw':start,'curve_length':len(curve),'curve_hex':curve.hex(),'byte_histogram':{f'{k:02x}':v for k,v in sorted(Counter(curve).items())},'hypotheses':variants})
        for i in range(first,first+g['enemy_count']):
            e=parsed['enemies'][i];typ=mapping[e['graphic_type']]
            table.append({'enemy':i,'entry_file_offset':offset+parsed['enemy_offset']+i*6,'group_contiguous_hypothesis':index,'formation':[e['formation_x'],e['formation_y']],'graphic_index':e['graphic_type'],'vygr_type':typ['vygr_type_1based'],'mapping_confirmed':typ['confirmed'],'attack_index':e['attack_index']})
        cursor+=8+len(curve);first+=g['enemy_count']
    if first!=len(parsed['enemies']) or len(table)!=22:raise ValueError('Invalid group/enemy counts')
    return {'status':'format structure verified; entry semantics BLOCKED','source':'assets/VYLV.DAT','level':1,'record_offset':offset,'record_length':len(raw),'enemy_relative_offset':parsed['enemy_offset'],'entry_interval_raw':parsed['entry_interval'],'attack_curve_count':len(parsed['attack_curves_hex']),'interval_units':'unknown; not assumed to be 50Hz ticks','groups':groups,'enemies':table,'missing':['original nibble interpreter and axis/scaling','time base and group/inter-enemy launch scheduling','curve-end transition to per-enemy formation targets','original coordinate anchor'],'notes':['Zero bytes occur inside curves: cannot invent 00 terminator.','Hypothesis sums do not establish original movement or target transition.','No ADF/dump/original JSON/interpreter present in stable branch archives or current main tree.']}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=ROOT/'docs/stage4b-entry-analysis.json');args=ap.parse_args()
    result=analyze();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('Verified Level 1 structure; original curve semantics remain unconfirmed.')
if __name__=='__main__':main()
