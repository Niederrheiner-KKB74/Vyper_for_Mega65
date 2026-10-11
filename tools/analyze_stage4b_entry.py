#!/usr/bin/env python3
"""Bounded Level-1 extraction and historical sign-magnitude reference model."""
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
        for mode in ('sign_magnitude',):
            def decode(n):return (-(n&7) if n&8 else n) if mode=='sign_magnitude' else (n-16 if n&8 else n)
            dx=[decode(b>>4) for b in curve];dy=[decode(b&15) for b in curve]
            points=[];x,y=start
            for a,b in zip(dx,dy):
                x+=a;y+=b;points.append([x,y])
            variants[mode]={'first_10_points':points[:10],'last_10_points':points[-10:],'bounds':[min(v[0] for v in [start]+points),max(v[0] for v in [start]+points),min(v[1] for v in [start]+points),max(v[1] for v in [start]+points)],'historical_reference':'docs/amiga_debut_curve_interpreter.md','axis_order':'high nibble X, low nibble Y','scale':1,'parameter_ticks_per_byte':1,'integrated_end':[start[0]+sum(dx),start[1]+sum(dy)],'first_12_deltas':list(map(list,zip(dx[:12],dy[:12])))}
        groups.append({'group':index,'enemy_count':g['enemy_count'],'first_enemy':first,'last_enemy':first+g['enemy_count']-1,'slot_assignment_status':'contiguous order from historical interpreter analysis','group_record_relative':cursor,'curve_relative':cursor+8,'curve_file_offset':offset+cursor+8,'start_raw':start,'curve_length':len(curve),'curve_hex':curve.hex(),'byte_histogram':{f'{k:02x}':v for k,v in sorted(Counter(curve).items())},'reference_model':variants})
        for i in range(first,first+g['enemy_count']):
            e=parsed['enemies'][i];typ=mapping[e['graphic_type']]
            table.append({'enemy':i,'entry_file_offset':offset+parsed['enemy_offset']+i*6,'group':index,'formation':[e['formation_x'],e['formation_y']],'graphic_index':e['graphic_type'],'vygr_type':typ['vygr_type_1based'],'mapping_confirmed':typ['confirmed'],'attack_index':e['attack_index']})
        cursor+=8+len(curve);first+=g['enemy_count']
    if first!=len(parsed['enemies']) or len(table)!=22:raise ValueError('Invalid group/enemy counts')
    return {'status':'VYLV structure verified; historical interpreter implemented; exact original timing remains open','source':'assets/VYLV.DAT','level':1,'record_offset':offset,'record_length':len(raw),'enemy_relative_offset':parsed['enemy_offset'],'entry_interval_raw':parsed['entry_interval'],'attack_curve_count':len(parsed['attack_curves_hex']),'interval_units':'historical 50 Hz reference; 16 ticks per enemy; exact original scheduling remains open','groups':groups,'enemies':table,'parameters':{'point_ticks':1,'start_point_tick':1,'group_delay':0,'return_step':1},'open_details':['original coordinate anchor','exact original point/tick and start-point accounting','relative group timing','Debut-specific State-2 transition verification','end-marker interpretation versus record-length termination'],'notes':['All curve bytes including 00 are consumed, bounded by record length.','Original Amiga Debut offsets 0/158 are not VYLV offsets.','No independent original binary verification: reconstruction supplied by user from stage4b-entry-analysis.','Return uses historical State-2 axis stepping; no teleport or substitute curve.']}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=ROOT/'docs/stage4b-entry-analysis.json');args=ap.parse_args()
    result=analyze();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('Verified Level 1 bytes and decoded historical reference model; exact original timing remains open.')
if __name__=='__main__':main()
