#!/usr/bin/env python3
"""Lossless Stage5d0 FCM tiles -> deduplicated VYTI v2 with disjoint glyph cache."""
import argparse,hashlib,json,struct,tempfile
from pathlib import Path
import convert_stage5d0_title as ORIGINAL
ROOT=Path(__file__).resolve().parents[1]
RANGES=[(0x12800,96),(0x15b00,628),(0x5c500,176)]
def build(out=ROOT/'assets/stage5d1'):
    source=ROOT/'assets/stage5d0/original_sources'
    with tempfile.TemporaryDirectory() as t:
        tmp=Path(t);report=ORIGINAL.convert(source/'vyper_palette_candidate_9a50.png',source/'vyper_title_palette.txt',tmp)
        tiles=(tmp/'title_fcm.bin').read_bytes();pal=(tmp/'VYTI.DAT').read_bytes()[18:117]
    uniques=[];ids={};indices=[]
    for i in range(0,len(tiles),64):
        tile=tiles[i:i+64]
        if tile not in ids:ids[tile]=len(uniques);uniques.append(tile)
        indices.append(ids[tile])
    if len(uniques)!=sum(n for a,n in RANGES):raise ValueError('Original tile count/layout changed: review memory map')
    addresses=[a+i*64 for a,n in RANGES for i in range(n)]
    screen=b''.join(struct.pack('<H',addresses[k]//64) for k in indices)
    raw=b''.join(uniques)
    payload=pal+screen+raw
    header=struct.pack('<4s6H2IH',b'VYTI',2,352,240,33,len(uniques),1320,len(screen),len(raw),sum(payload)&65535)
    data=header+payload
    # Re-fetch using physical glyph addresses and match every original tile byte.
    cache={a:tile for a,tile in zip(addresses,uniques)}
    restored=b''.join(cache[g*64] for g, in struct.iter_unpack('<H',screen))
    if restored!=tiles:raise ValueError('Exact FCM byte roundtrip failed')
    tile_offset=len(header)+len(pal)+len(screen)
    copies=[];offset=tile_offset
    for dest,count in RANGES:
        copies.append({'source':0x40000+offset,'target':dest,'bytes':count*64});offset+=count*64
    out.mkdir(parents=True,exist_ok=True)
    (out/'VYTI.DAT').write_bytes(data);(out/'title_fcm_unique.bin').write_bytes(raw);(out/'title_screen.bin').write_bytes(screen)
    const={'T_FILE_BYTES':len(data),'T_FILE_SUM':sum(data)&65535,'T_PREFIX_BYTES':len(header)+len(pal),'T_TILE_OFFSET':tile_offset}
    inc=''.join(f'.const {k}=${v:x}\n' for k,v in const.items())
    inc+='.var t_data=LoadBinary("VYTI.DAT")\n'
    # F018A COPY descriptors with explicit source/destination megabyte options.
    for i,c in enumerate(copies):
        inc+=f't_tile_copy_{i}:\n    .byte $80,0,$81,0,$0a,0,0\n    .word ${c["bytes"]:x}\n    .byte '+','.join(f'${(a>>s)&255:02x}' for a in (c['source'],c['target']) for s in (0,8,16))+'\n    .word 0\n'
    (out/'title_layout.inc').write_text(inc)
    report.update({'format':'VYTI v2:26-byte header,99 palette bytes,2640 physical FCM map bytes,57600 unique FCM bytes','unique_tiles':len(uniques),'tile_bytes':len(raw),'VYTI_bytes':len(data),'VYTI_sha256':hashlib.sha256(data).hexdigest(),'cache_ranges':[{'start':hex(a),'end_inclusive':hex(a+n*64-1),'tiles':n} for a,n in RANGES],'copies':copies,'FCM_byte_roundtrip':len(restored),'screen':'$F300-$FD4F (physical RAM, not CPU ROM)','original_Stage5d0_format_preserved_in_original_assets':True})
    (out/'conversion-report.json').write_text(json.dumps(report,indent=2)+'\n')
    return data,report
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'assets/stage5d1');a=p.parse_args();_,r=build(a.output);print(json.dumps(r,indent=2))
if __name__=='__main__':main()
