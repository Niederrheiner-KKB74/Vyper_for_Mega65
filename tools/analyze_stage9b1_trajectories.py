#!/usr/bin/env python3
"""Stage9b1 signed-delta reference trajectories; not an emulator or timing measurement."""
import argparse,csv
from pathlib import Path
import analyze_attack_descriptors as P
ROOT=Path(__file__).resolve().parents[1]

def trajectories(data):
    for level,interval,groups,enemies,attacks in P.parse(data):
        shift=min(e[1] for e in enemies)
        for slot,(x,y,gfx,index) in enumerate(enemies):
            startx=x;starty=y-shift;y=starty;packed=attacks[index]
            for count in range(1,2001):
                dx,dy=P.decode(packed[(count-1)%len(packed)])
                x=(x+dx+32768)%65536-32768
                y=(y+dy+32768)%65536-32768
                if y>=200:break
            else:raise ValueError(f'No bottom exit: level{level} slot{slot}')
            yield (level,slot,index,len(packed),startx,starty,count,x,y,count//len(packed),int(level not in (25,50,99,100)))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'docs/stage9b1_attack_trajectories.csv')
    args=p.parse_args();rows=list(trajectories((ROOT/'assets/VYLV.DAT').read_bytes()))
    with args.output.open('w',newline='') as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(('level','slot','curve','bytes','start_x','start_y','points_to_port_bottom','terminal_x','terminal_y','complete_passes','gameplay_attack_allowed'));w.writerows(rows)
    print(f'{len(rows)} actors; maximum {max(r[6] for r in rows)} points; special-level bans unchanged')
