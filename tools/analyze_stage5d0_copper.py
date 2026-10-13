#!/usr/bin/env python3
"""Reproduce saved Amiga registers/Copper lists. Static analysis, no WinUAE run."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'assets/stage5b/original_sources'
HASHES={'Vyper_Startscreen.uss':'d836cbf88f0ac35b6ed3776df2add39f699113c1aeb9d02cdfe4651c82793916','Vyper_Memory_Dump.dat':'d74aea88fb4232e36caab80e51abc51f73d470a5b55a54f5cb010f1d910ddf8c'}
REG_NAMES={0x8e:'DIWSTRT',0x90:'DIWSTOP',0x92:'DDFSTRT',0x94:'DDFSTOP',0x100:'BPLCON0',0x102:'BPLCON1',0x104:'BPLCON2',0x8a:'COPJMP2'}
def chunks(data):
    i=0
    while i+8<=len(data):
        name=data[i:i+4];size=int.from_bytes(data[i+4:i+8],'big')
        if name==b'END ':return
        if size<12 or i+size>len(data):raise ValueError('Invalid USS chunk')
        flags=int.from_bytes(data[i+8:i+12],'big')
        if flags&1:raise ValueError('Compressed chunk is not handled')
        yield name,data[i+12:i+size]
        i+=size+4-size%4
    raise ValueError('Missing END chunk')
def be(data,i,n=2):return int.from_bytes(data[i:i+n],'big')
def copper(data,start):
    events=[];interesting=[];wait=None
    for i in range(start,min(len(data),start+4096),4):
        a,b=be(data,i),be(data,i+2)
        if (a,b)==(0xffff,0xfffe):events.append({'address':hex(i),'end':True});break
        if a&1:
            wait={'line8':a>>8,'horizontal':a&0xfe,'mask':hex(b),'skip':bool(b&1)}
            events.append({'address':hex(i),'wait_or_skip':wait.copy()})
        else:
            e={'address':hex(i),'register':hex(a&0x1fe),'value':hex(b)};events.append(e)
            if a in REG_NAMES:interesting.append({**e,'name':REG_NAMES[a],'after_wait':wait.copy() if wait else None})
    else:raise ValueError('No bounded Copper end at '+hex(start))
    return {'start':hex(start),'instructions':events,'display_moves':interesting,'execution':'STATIC_ONLY'}
def analyze():
    data={n:(SRC/n).read_bytes() for n in HASHES}
    for n,d in data.items():
        if hashlib.sha256(d).hexdigest()!=HASHES[n]:raise ValueError('Original source changed: '+n)
    ch=dict(chunks(data['Vyper_Startscreen.uss']));chip=ch[b'CHIP'];dump=data['Vyper_Memory_Dump.dat']
    if len(chip)!=360:raise ValueError('Unexpected compact custom-register payload')
    cop1=be(chip,4+0x80,4);cop2=be(chip,4+0x84,4)
    regs={'COP1LC':hex(cop1),'COP2LC':hex(cop2)}
    for reg in (0x8e,0x90,0x92,0x94,0x96):regs[REG_NAMES.get(reg,'DMACON')]=hex(be(chip,4+reg))
    # AUD $A0-$DF are absent in compact WinUAE CHIP save; 8 BPLPTR longs follow.
    regs['BPLCON0']=hex(be(chip,4+0xa0+8*4))
    lists=[{**copper(ch[b'CRAM'],p),'source':'savestate CRAM'} for p in [cop1,cop2]]
    lists += [{**copper(dump,p),'source':'separate memory dump'} for p in [0x1b5b4,0x1c4ec,0x2b38a,0x35496]]
    # Do not infer active title/overscan from width of a saved image or memory finds.
    return {'source_sha256':HASHES,'CHIP_bytes':len(chip),'CHIP_flags':hex(be(chip,0,4)),'saved_registers':regs,'lists':lists,'conditional_classic_OCS_ECS_interpretation':{'referenced_COP2_DDF_lowres_pixels':((0xd0-0x38)//8+1)*16,'DIW_horizontal_lowres_pixels':(0xc1+0x100)-0x81,'enabled_bitplane_raster_phase':[44,244],'enabled_raster_rows':200,'BPLCON0_4200':'lowres,4 bitplanes','BPLCON0_A200':'hires,2 bitplanes; not5 bitplanes','DIW_vertical_window_rows':0x140-5},'limitations':['No executed Copper trace or WinUAE/hardware runtime.','Snapshot BPLCON0=$0200 has zero planes; mode varies within list.','Active title352x240 and Overscan are not established by these saved registers/lists.','Other list addresses are memory finds, not evidence of activation.']}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'docs/stage5d0-copper-report.json');a=p.parse_args()
    report=analyze();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['saved_registers'],indent=2))
if __name__=='__main__':main()
