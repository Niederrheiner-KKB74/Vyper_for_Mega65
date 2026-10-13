#!/usr/bin/env python3
"""Bounded original Amiga COLOR02 algorithm and Copper interrupt evidence."""
import argparse,hashlib,json,struct
from pathlib import Path
import analyze_stage5d0_copper as COP
import extract_stage5b_graphics as GRAPHICS
ROOT=Path(__file__).resolve().parents[1]
def step(state,deltas,segment=7):
    word,phase,left=state;word=(word+deltas[phase])&65535;left-=1
    if left==0:left=segment;phase=(phase+1)%len(deltas)
    return word,phase,left

def analyze(out):
    src=ROOT/'assets/stage5b/original_sources/Vyper_Startscreen.uss';data=src.read_bytes()
    if hashlib.sha256(data).hexdigest()!=GRAPHICS.SOURCE_HASHES[src.name]:raise ValueError('Original USS changed')
    ch=dict(COP.chunks(data));ram=ch[b'CRAM'];code=ch[b'BRAM'];a4=0x2013e
    # Exact opcode checks: word add, COLOR02 write, countdown, 7, byte-offset
    # phase increment +2, terminal offset12. No guessed table/cadence.
    checks={0xd042:'302c2c4841ec80d6322c2c4cd070100039402c4833c000dff184536c2c4a6614397c00072c4a5441b27c000c6602424139412c4c',0x9d10:'41fa32e029482d32486c2d20487800044eac8020504f',0x1180e:'4cef020100042c7900022d044eeeff58',0xa1e4:'397c0e002c48397c00072c4a426c2c4c'}
    for p,h in checks.items():
        if code[p:p+len(bytes.fromhex(h))]!=bytes.fromhex(h):raise ValueError('Original cycling opcode changed at '+hex(p))
    if ram[a4-0x7fe0:a4-0x7fe0+6]!=bytes.fromhex('4ef900c1180e'):raise ValueError('AddIntServer stub differs')
    if COP.be(ram,a4+0x2d32,4)!=0xc0cff2:raise ValueError('Saved interrupt callback differs')
    if COP.be(ram,COP.be(ram,a4+0x2d2e,4),4)!=a4:raise ValueError('ISR userdata/A4 mismatch')
    deltas=list(struct.unpack_from('>6h',ram,a4-0x7f2a));saved=[COP.be(ram,a4+0x2c48),COP.be(ram,a4+0x2c4c)//2,COP.be(ram,a4+0x2c4a)]
    if deltas!=[32,-512,2,-32,512,-2] or saved!=[0xec,2,1]:raise ValueError('Unexpected original state/table')
    if COP.be(ch[b'CHIP'],0xe4+4)!=saved[0]:raise ValueError('Saved COLOR02 differs from cycle word')
    copper=COP.copper(ram,COP.be(ch[b'CHIP'],0x88,4))['instructions']
    irq=[e for e in copper if e.get('register')=='0x9c' and e.get('value')=='0x8010']
    if len(irq)!=1:raise ValueError('Exactly one Copper interrupt request per list required')
    records=[];state=tuple(saved)
    for tick in range(169):
        word,phase,left=state
        if not 0<=word<=0xfff:raise ValueError('RGB4 overflow')
        records.append({'tick':tick,'RGB4':f'${word:03X}','rgb':[17*((word>>s)&15) for s in (8,4,0)],'phase':phase,'remaining':left})
        state=step(state,deltas)
    if records[0]['RGB4']!=records[42]['RGB4'] or step(tuple(saved),deltas)[0]!=0xee:raise ValueError('Cycle closure')
    initial=json.loads((ROOT/'assets/stage6a1/conversion-report.json').read_text());raw=(ROOT/'assets/stage6a1/original_menu_indices.bin').read_bytes()
    actors=[]
    for a in initial['actors']:
        counts=[]
        for f in GRAPHICS.graphics_types((ROOT/'assets/stage5b/VYGR.DAT').read_bytes())[a['type']-1]['frames']:
            # VYGR uses original colour+1 under its mask, so original2 is NCM3.
            counts.append(sum(v==3 for b in f for v in (b&15,b>>4)))
        actors.append({'slot':a['slot'],'type':a['type'],'COLOR02_pixels_by_frame':counts})
    report={'issue':45,'source_uss_sha256':hashlib.sha256(data).hexdigest(),'evidence':'static exact opcodes, saved live ISR node/state, active Copper list and indexed pixels; not WinUAE runtime','original_register':'COLOR02 / $DFF184','FCM_index':2,'delta_table_CRAM':'$18214','signed_RGB4_deltas':deltas,'phase_steps':7,'steps_per_cycle':42,'IRQ_registration':{'function':'$C0CFF2','init_code':'BRAM $9D10-$9D24','interrupt_number':4,'Exec_bridge':'$C1180E -> -$A8 (AddIntServer)','saved_node':'$22E5E','Copper_INTREQ':irq[0]},'timebase':'one COPER request per active Copper list/display frame; PAL50 implies one RGB step per20ms, complete cycle840ms; code-derived, not timed with WinUAE','startup_state':[0xe00,0,7],'snapshot_state':saved,'gate':'A4+$2C42 !=0; skipped updates preserve word/phase/countdown','seed_policy':'keep Stage6a1 snapshot palette $0EC and matching saved phase/countdown for initial appearance; restart this snapshot state on RUN','other_effect_not_implemented':'COLOR03 at $DFF186 toggles XOR $DD0 every20 interrupts; outside requested COLOR02 change and remaining text preservation','menu_regions_index2':{'border_corners':[raw[0],raw[319],raw[-320],raw[-1]],'bonus_pixels':sum(v==2 for v in raw[112*320:123*320]),'option_pixels':sum(v==2 for v in raw[124*320:136*320])},'actors':actors,'trace':records}
    out.mkdir(parents=True,exist_ok=True);(out/'color-cycling-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    inc=f'.const CC_PALETTE_INDEX=2\n.const CC_START_WORD=${saved[0]:04x}\n.const CC_START_PHASE={saved[1]}\n.const CC_START_LEFT={saved[2]}\n.const CC_SEGMENT_STEPS=7\n.const CC_PHASES=6\n'
    for i,delta in enumerate(deltas):inc+=f'.const CC_DELTA_{i}=${delta&65535:04x}\n'
    (out/'color_cycle.inc').write_text(inc)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'assets/stage6a2');a=p.parse_args();r=analyze(a.output);print(json.dumps({k:r[k] for k in ['original_register','signed_RGB4_deltas','steps_per_cycle','timebase']}))
