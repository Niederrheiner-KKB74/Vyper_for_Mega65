#!/usr/bin/env python3
"""Pure original-record diagnostics; no runtime raster logging or data changes."""
import json,argparse
from pathlib import Path
import analyze_stage3b2_data as DATA
from analyze_attack_descriptors import decode
import extract_stage5b_graphics as GRAPHICS
ROOT=Path(__file__).resolve().parents[1]
def transform(y,variant):return {'A':lambda:y,'B':lambda:y-16,'C':lambda:y*25//29}[variant]()
def analyze():
    raw=(ROOT/'assets/VYLV.DAT').read_bytes();rows=[];bounds=[]
    graphics=GRAPHICS.graphics_types((ROOT/'assets/stage5b/VYGR.DAT').read_bytes())
    mapping=json.loads((ROOT/'assets/stage5b/vylv_vygr_mapping.json').read_text())
    for levelnum,(_,record) in enumerate(DATA.level_records(raw),1):
        p=DATA.parse_level_record(record)
        first=0
        for gi,g in enumerate(p['groups'],1):
            indices={e['graphic_type'] for e in p['enemies'][first:first+g['enemy_count']]}
            first+=g['enemy_count']
            x,y=g['start_x'],g['start_y'];points=[(x,y)];visible=[False]
            moved=False
            for b in bytes.fromhex(g['curve_hex']):
                dx,dy=decode(b);x+=dx;y+=dy;moved|=bool(dx or dy);points.append((x,y));visible.append(moved)
            bounds.extend(y for x,y in points)
            if levelnum>3:continue
            for v in 'ABC':
                # Last byte immediately switches phase to RETURN: it is not
                # projected, exactly as the unchanged stable state machine.
                entry=points[:-1];ys=[transform(y,v) for x,y in entry]
                rendered=[(x,transform(y,v)) for (x,y),shown in zip(entry,visible[:-1]) if shown]
                onfield=[(x,y) for x,y in rendered if -16<x<240 and -16<y<200]
                deepest=max((y for x,y in onfield),default=None)
                xs=[x for x,y in onfield if y==deepest]
                gap=min((184-(y+16) for x,y in onfield),default=None)
                visible_bottom=max((min(199,y+15) for x,y in onfield),default=None)
                overlap=[(x,y) for x,y in onfield if x<120 and x+16>104]
                opaque_points=[]
                for x,y in onfield:
                    sy0=max(0,-y);sy1=min(16,200-y);sx0=max(0,-x);sx1=min(16,240-x)
                    for index in indices:
                        for frame in graphics[mapping[index]['vygr_type_1based']-1]['frames']:
                            for sy in range(sy1-1,sy0-1,-1):
                                if any((frame[sy*8+sx//2]>>(4*(sx%2)))&15 for sx in range(sx0,sx1)):
                                    opaque_points.append((x,y+sy));break
                deepest_opaque=max((y for x,y in opaque_points),default=None)
                rows.append({'variant':v,'level':levelnum,'group':gi,'enemy_count':g['enemy_count'],'entry_interval':p['entry_interval'],'original_start_y':g['start_y'],'curve_bytes':len(points)-1,'logical_entry_y_min':min(y for x,y in entry),'logical_entry_y_max':max(y for x,y in entry),'transformed_entry_y_min':min(ys),'transformed_entry_y_max':max(ys),'rendered_y_min':min((y for x,y in onfield),default=None),'rendered_y_max':deepest,'x_at_deepest_rendered_y':xs,'deepest_visible_bbox_pixel':visible_bottom,'deepest_visible_opaque_pixel_any_animation_frame':deepest_opaque,'x_at_deepest_opaque_pixel':sorted({x for x,y in opaque_points if y==deepest_opaque}),'min_vertical_gap_to_player_top':gap,'min_clipped_bbox_gap_to_player_top':min((184-min(200,y+16) for x,y in onfield),default=None),'min_gap_when_horizontal_overlap_center_player':min((184-y-16 for x,y in overlap),default=None),'return_start_original_xy':points[-1],'last_projected_xy':[entry[-1][0],ys[-1]],'entry_to_return_y_jump':points[-1][1]-ys[-1]})
    assert min(bounds)>=-32752 and max(bounds)<=32767,'B requires signed16 output'
    return {'issue':37,'player_top_y':184,'player_start_x':104,'playfield':[240,200],'source':'assets/VYLV.DAT','bbox':'16x16; bottom gap uses exclusive Y+16, visible bbox pixel inclusive Y+15 clipped to 199; opaque metric separately examines original NCM transparency over all possible animation frames; actual frame phase not pinned','last_point':'Final curve byte becomes RETURN immediately and is untransformed; original start remains invisible until first nonzero delta','all100_logical_y_bounds':[min(bounds),max(bounds)],'rows':rows,'xemu':'NOT_RUN; user comparison pending'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'releases/debut_y_geometry_test/diagnostics.json');a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(analyze(),indent=2)+'\n')
