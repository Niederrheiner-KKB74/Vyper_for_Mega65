#!/usr/bin/env python3
"""Lossless original planes -> existing bank-1 NCM indices; no invented pixels."""
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VALID_FRAME_INDICES=tuple(range(7))

def convert(source):
    blocks=re.findall(r'## Frame (\d+) – descriptor \$(\w+)\s+```text\s+([\s\S]*?)```',source)
    if len(blocks)!=8 or [int(x[0]) for x in blocks]!=list(range(8)):
        raise ValueError('Expected eight archived source records: seven explosions and the excluded player ship')
    result=[]
    for i,address,block in blocks:
        rows=[bytes.fromhex(line) for line in block.strip().splitlines()]
        if len(rows)!=4 or any(len(row)!=32 for row in rows):
            raise ValueError('Each frame requires three 32-byte planes and mask')
        if int(address,16)!=0x3819a+32*int(i): raise ValueError('Descriptor order changed')
        pixels=[]
        for y in range(16):
            for x in range(16):
                b=2*y+x//8; bit=7-x%8
                colour=sum(((rows[p][b]>>bit)&1)<<p for p in range(3))
                pixels.append(colour+1 if rows[3][b]&(1<<bit) else 0)
        result.append(bytes(pixels[x]|pixels[x+1]<<4 for x in range(0,256,2)))
    return result

def validate_animation(frames,indices=VALID_FRAME_INDICES):
    player=(ROOT/'assets/player/player_ncm.bin').read_bytes()
    def pixels(data):return tuple((v>>shift)&15 for v in data for shift in (0,4))
    reference=pixels(player)
    for i in indices:
        candidate=pixels(frames[i])
        same=sum(a==b for a,b in zip(candidate,reference))
        same_mask=all(bool(a)==bool(b) for a,b in zip(candidate,reference))
        if same_mask and same>=230:
            raise ValueError(f'Source record {i} is the player ship, not an explosion ({same}/256 pixels match)')
    return indices

def build(output=ROOT/'assets/explosions'):
    source=(ROOT/'assets/explosions/explosion_amiga_planes.txt').read_bytes()
    frames=convert(source.decode())
    validate_animation(frames)
    output.mkdir(parents=True,exist_ok=True)
    for i,data in enumerate(frames): (output/f'explosion_{i:02d}_ncm.bin').write_bytes(data)
    report={'source_sha256':hashlib.sha256(source).hexdigest(),'geometry':[16,16],
            'row_order':'linear, exactly as source specifies','transparent':'mask bit 0 -> index 0',
            'palette':'existing engine bank 1: visible 3-bit colour + 1',
            'packing':'left pixel low nibble','visual_xemu':'pending',
            'animation_source_records':list(VALID_FRAME_INDICES),
            'excluded_source_records':{'7':'Player ship: same transparency mask and 238/256 matching player pixels; user confirms exactly seven explosion frames'},
            'frames':[{'frame':i,'used_for_explosion':i in VALID_FRAME_INDICES,'sha256':hashlib.sha256(f).hexdigest(),'bytes':len(f)} for i,f in enumerate(frames)]}
    (output/'conversion.json').write_text(json.dumps(report,indent=2)+'\n')
    return frames
if __name__=='__main__':build()
