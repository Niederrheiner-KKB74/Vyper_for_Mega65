#!/usr/bin/env python3
"""Bounded original projectile candidates; no claim of an active in-game trace."""
import argparse,hashlib,json
from pathlib import Path
import analyze_stage5d0_copper as COP
import extract_stage5b_graphics as ORIGINAL
ROOT=Path(__file__).resolve().parents[1]
def hits(data,pattern):
    result=[];start=0
    while True:
        p=data.find(pattern,start)
        if p<0:return result
        result.append(p);start=p+1
def analyze(out):
    source=ROOT/'assets/stage5b/original_sources'
    raw={n:(source/n).read_bytes() for n in ORIGINAL.SOURCE_HASHES}
    for n,sha in ORIGINAL.SOURCE_HASHES.items():
        if hashlib.sha256(raw[n]).hexdigest()!=sha:raise ValueError('Original checksum mismatch '+n)
    chunks=dict(COP.chunks(raw['Vyper_Startscreen.uss']))
    ram=chunks[b'CRAM'];custom=chunks[b'CHIP']
    if len(ram)!=524288 or len(custom)!=360:raise ValueError('Unexpected snapshot layout')
    records=[]
    for slot in range(2,8):
        state=chunks[f'SPR{slot}'.encode()]
        if len(state)!=25:raise ValueError('Unexpected saved sprite chunk')
        pointer=COP.be(state,0,4)
        if pointer+64>len(ram):raise ValueError('Sprite candidate outside ChipRAM')
        data=ram[pointer:pointer+64]
        pixels=[]
        for row in range(16):
            lo,hi=COP.be(data,4*row),COP.be(data,4*row+2)
            pixels.append([((lo>>(15-x))&1)|(((hi>>(15-x))&1)<<1) for x in range(16)])
        base=16+4*(slot//2)
        colours=[COP.be(custom,0xe4+2*(base+i)) for i in range(4)]
        records.append({'slot':slot,'saved_pointer':pointer,'saved_pos_ctl_hex':state[4:8].hex(),
            'candidate_data_hex':data.hex(),'candidate_rows_at_saved_pointer':pixels,
            'colour_register_numbers':[base+i for i in range(4)],'saved_RGB4_words':colours})
    candidate=records[0]
    if any(r['candidate_data_hex']!=candidate['candidate_data_hex'] for r in records):raise ValueError('Six candidate patterns differ')
    if any(r['saved_RGB4_words'][1:]!=[0xfff,0xe00,0x344] for r in records):raise ValueError('White/red/grey palette evidence differs')
    pattern=bytes.fromhex(candidate['candidate_data_hex'])[:28]
    report={'stage':'7b2','source_sha256':ORIGINAL.SOURCE_HASHES,
        'evidence':'Original raw snapshot chunks/pointers/bitplane words/colour registers; static, not WinUAE runtime',
        'candidate_slots':records,'nonzero_candidate_extent':[3,7],
        'visible_candidate_rows':['.1.','.1.','.1.','313','212','222','.2.'],
        'candidate_colours':{'1':'white RGB4 $FFF','2':'red RGB4 $E00','3':'dark grey RGB4 $344'},
        'exact_pattern_hits':{'USS_CRAM':hits(ram,pattern),'memory_dump':hits(raw['Vyper_Memory_Dump.dat'],pattern),'ADF_raw':hits(raw['VYPER.ADF'],pattern)},
        'limitations':['User screenshots archived in assets/stage7b2/reference; shaft/red tip visually match candidate.',
            'Snapshot is start-screen state; saved POS/CTL fields are zero, not an observed active gameplay projectile.',
            'Rows decoded at saved pointer are a strong matching candidate, not a proven active sprite descriptor/start address.',
            'Original candidate has grey flanks and extent3x7; do not silently replace1x4 gameplay geometry or hitboxes.',
            'Final rendering is documented1x4 approximation:3 white+1 red; grey flanks omitted, hitboxes unchanged.']}
    out.mkdir(parents=True,exist_ok=True)
    # Original indices1 white,2 red,3 grey -> VIC MCM01,11,10.
    rows=candidate['candidate_rows_at_saved_pointer'][:7]
    code={0:0,1:1,2:3,3:2}
    def sprite(sequence):
        payload=bytearray(64)
        for y,row in enumerate(sequence):
            packed=sum(code[v]<<(6-2*x) for x,v in enumerate(row[:3]))
            payload[y*6]=packed;payload[y*6+3]=packed
        return bytes(payload)
    player=sprite(list(reversed(rows)));enemy=sprite(rows)
    (out/'projectile_sprites.bin').write_bytes(player+enemy)
    report['implementation']={'size':[3,7],'player':'vertical reflection; red tip above',
        'original_to_VIC_MCM':code,'hardware_sprite_RGB_indices':[10,13,16],
        'binary_sha256':hashlib.sha256(player+enemy).hexdigest()}
    report['limitations']=[x for x in report['limitations'] if not x.startswith(('Original candidate has grey','Final rendering is documented'))]
    (out/'projectile_analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'assets/stage7b2');a=p.parse_args()
    r=analyze(a.output);print(json.dumps({k:r[k] for k in ('nonzero_candidate_extent','visible_candidate_rows','exact_pattern_hits')}))
