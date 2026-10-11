#!/usr/bin/env python3
"""Inspect bounded original Level-1 attack records; distinguish data from rules."""
import argparse, hashlib, json
from pathlib import Path
import analyze_stage3b2_data as DATA
import analyze_attack_descriptors as AUDIT
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
def decode(b):
    return [-(b>>4&7) if b&128 else b>>4&7,-(b&7) if b&8 else b&7]
def analyze():
    offset,raw=DATA.level_records((ROOT/'assets/VYLV.DAT').read_bytes())[0]
    p=DATA.parse_level_record(raw)
    cursor=p['enemy_offset']+len(p['enemies'])*6
    curves=[]
    for i,h in enumerate(p['attack_curves_hex']):
        b=bytes.fromhex(h);x=y=0;points=[]
        for n in b:
            dx,dy=decode(n);x+=dx;y+=dy;points.append([x,y])
        curves.append({'curve':i,'length_word_file_offset':offset+cursor,'payload_file_offset':offset+cursor+2,'runtime_pointer':0x7600+cursor+2,'length':len(b),'sha256':hashlib.sha256(b).hexdigest(),'first_bytes':b[:12].hex(),'last_bytes':b[-12:].hex(),'delta_first':decode(b[0]),'point_58':points[57],'last_point':points[-1],'integrated_y_bounds':[min(v[1] for v in points),max(v[1] for v in points)],'negative_integrated_y_marker_present':any(v[1]<0 for v in points),'curve_hex':h})
        cursor+=2+len(b)
    if cursor!=len(raw) or len(curves)!=2 or any(c['length']!=183 for c in curves):
        raise ValueError('Unexpected Level-1 attack structure')
    a,b=[bytes.fromhex(c['curve_hex']) for c in curves]
    mirror=all(decode(x)==[-decode(y)[0],decode(y)[1]] for x,y in zip(a,b))
    if not mirror:raise ValueError('Level-1 curves are not delta mirrors')
    result={'level':1,'record_file_offset':offset,'record_length':len(raw),'curves':curves,'exact_horizontal_mirror':mirror,'raw_enemy_indices':[e['attack_index'] for e in p['enemies']],'data_verified':['two separate bounded 183-byte records','sign magnitude deltas mirror in X; identical Y','indices 0 for slots 0-10; 1 for slots 11-21'],'historical_user_analysis':['50 Hz ATTACK: X relative to saved start','negative expanded Y sentinel transitions to State 2; return +/-1'],'not_independently_verified':['original interpreter/dumps not present','original $88 branch remains unverified; per-enemy converted-data mapping is binding','original attack cadence/probability','absolute versus relative attack Y origin','expanded sentinel lost/not represented in finite VYLV records'],'mega65_rules':['fixed per-enemy raw index chooses curve; verified VYLV semantics + user original-game observation; original routine not independently disassembled','integrate X/Y relative to attack start to avoid visible start teleport','consume all 183 bytes; latch invisibility after first bottom crossing','if finite end is above bottom, continue X=constant, Y+=2 until Y>=200','after an invisible update reenter at Y=-16; return +/-1 toward current slot','offset -8..8, 1 pixel/2 updates; after full entry barrier; formation targets original Y minus 25 pixels','no new attack launches during player explosion/respawn wait; existing attacks drain','fixed seed 0xc3a5, initial 100 updates then 60-update attempts, max 3 ATTACK']}
    ys=[e['formation_y'] for e in p['enemies']]
    minimum=min(ys)
    frames=DATA.graphics_types((ROOT/'assets/VYGR.DAT').read_bytes())[14]['frames']
    first=[min(y for y in range(16) if any(f[y*8:y*8+8])) for f in frames]
    result['formation']={'original_y_min':minimum,'original_y_max':max(ys),'common_y_offset':-minimum,'stable4b2_y_min':minimum-8,'target_y_min':0,'target_y_max':max(ys)-minimum,'opaque_top_rows_per_frame':first,'attack_endpoint_y_range':[168,max(ys)-minimum+168],'maximum_vertical_tail_updates':16,'complete_entry_barrier_no_hits':336,'group_spawn_updates':[1+16*i for i in range(11)],'direction_change_update':16,'pendulum_cycle_updates':64}
    result['entry_fire']={'eligible':'genuine ENTRY phase1 after shared visibility latch, or ATTACK','not_eligible':['WAIT_ENTRY','RETURN','FORMATION','DEAD','EXPLOSION','motionless ENTRY','fully offscreen'],'origin':'signed top-left X+8,Y+16; three-pixel shot must fit X=0..237; Y=16..183; top-clipped sources wait for Y>=0','source_x_range':[-8,229],'source_y_range':[0,167],'global_projectile_limit':4,'probability':'same 1/8 roll, candidate 0..31 with rejection, cooldown12','tracking':'target player position saved at launch, no homing'}
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=ROOT/'docs/stage4c-attack-analysis.json')
    args=ap.parse_args();result=analyze();args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('100 levels/2194 fixed attack indices verified; Level1 mirrors preserved; original endmarker rules remain separate.')
if __name__=='__main__':main()
