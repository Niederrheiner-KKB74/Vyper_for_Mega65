#!/usr/bin/env python3
"""Deterministic test parameters; no claim of reconstructed Amiga star constants."""
import json,random
from pathlib import Path
COUNT=48
SEED=0x7441
BUFFER=0x18000
WIDTH=240;HEIGHT=200
DIVIDERS=(8,4,2) # blue, red, yellow: test parameters only
RGB=((0,0,255),(255,0,0),(255,255,0))
def convert(out):
    if not 3<=COUNT<=48 or COUNT%3:raise ValueError('Star count must be a multiple of 3, <=48 (current table/state budget)')
    if any(d<1 or d>128 or d&(d-1) for d in DIVIDERS):raise ValueError('Use power-of-two frame dividers')
    if len(RGB)!=3 or any(len(c)!=3 or any(not 0<=v<=255 for v in c) for c in RGB):raise ValueError('Three RGB8 colours required')
    rng=random.Random(SEED);xs=[(i*37+11)%WIDTH for i in range(COUNT)];ys=[rng.randrange(HEIGHT) for _ in xs]
    assert len(set(xs))==COUNT # Independent X prevents same-pixel star collisions.
    bases=[(x//16)*64+(x%16)//2 for x in xs]
    ybases=[BUFFER+(y//8)*960+(y%8)*8 for y in range(HEIGHT)]
    colours=[(1+i//(COUNT//3))<<(4*(x%2)) for i,x in enumerate(xs)]
    s=f'.const STAR_COUNT={COUNT}\n.const STAR_GROUP={COUNT//3}\n.const STAR_BYTES=24000\n.const STAR_BASE=$18000\n'
    for i,rgb in enumerate(((0,0,0),*RGB)):
        for channel,v in zip('RGB',rgb):s+=f'.const STAR_{channel}{i}={v}\n'
    s+='*=$cd80 "Starfield address tables, separate from engine bridge"\n.namespace stars {\n'
    for label,vals in [('ybase_lo',[a&255 for a in ybases]),('ybase_hi',[(a>>8)&255 for a in ybases]),('xbase_lo',[a&255 for a in bases]),('xbase_hi',[a>>8 for a in bases]),('draw_bits',colours),('initial_y',ys),('period_masks',[d-1 for d in DIVIDERS])]:s+=label+': .byte '+','.join(str(v) for v in vals)+'\n'
    s+='star_tables_end:\n.if (*>$cfd8) { .error "Starfield tables collide with state" }\n}\n'
    p=Path(out);p.mkdir(parents=True,exist_ok=True);(p/'stars_layout.inc').write_text(s)
    report={'seed':SEED,'count':COUNT,'colours_RGB':RGB,'dividers_frames':DIVIDERS,'pixels_per_second':[50/d for d in DIVIDERS],'x':xs,'initial_y':ys,'buffer':[BUFFER,BUFFER+24000-1],'layout':'15x25 NCM tiles, 16x8 logical pixels; one low/high nibble per star','origin':'All star parameters are isolated test choices, not original Amiga constants','overlap_policy':'Unique fixed X coordinates; adjacent nibbles preserved by read-modify-write','palette_bank':1,'palette_indices':[48,49,50,51],'sprites_consumed':0,'additional_RRB_pixie_slots':0,'background_cells':375}
    return report
