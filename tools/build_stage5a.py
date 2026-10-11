#!/usr/bin/env python3
"""Build Stage 5a all100 levels from stage4c-stable; never modify stable releases."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import re
import analyze_stage4c_attack as ATTACK
import build_stage3b1 as BASE
import build_stage3b3 as PLAYER
import build_explosion_assets as EXPLOSIONS
from build_stage3b2 import symbols
ROOT = Path(__file__).resolve().parents[1]
def mapping_source():
    rows=json.loads((ROOT/'assets/vylv_vygr_mapping.json').read_text())
    if [r['vylv_index'] for r in rows]!=list(range(38)) or rows[14]['vygr_type_1based']!=15:
        raise ValueError('Mapping index14 must select type15')
    if [r['vylv_index'] for r in rows if r['confirmed']]!=[14]:
        raise ValueError('Only mapping14 is confirmed')
    if any(type(r['vygr_type_1based']) is not int or not 1<=r['vygr_type_1based']<=36 or type(r['confirmed']) is not bool for r in rows):
        raise ValueError('Mapping type range/status invalid')
    return '*=$8900 "Projectile pointers and mapping"\n.namespace shots {\npointer_data: .fill 16,0\np_mapping: .byte '+','.join(str(r['vygr_type_1based']) for r in rows)+'\np_mapping_confirmed: .byte '+','.join(str(int(r['confirmed'])) for r in rows)+"""
}
*=$8a00 "Monochrome projectile graphics"
.namespace shots {
// Player: 1 logical pixel wide, four high; native H640/V400 pixels are doubled.
.fill 64, (i<24 && mod(i,3)==0) ? $c0 : 0
// Enemy: 3 logical pixels wide, four high, red. Different width and colour.
.fill 64, (i<24 && mod(i,3)==0) ? $fc : 0
}
"""

def verify_engine(prg,names):
    old=(ROOT/'releases/stage_4c/STAGE4C.PRG').read_bytes()
    # Baseline archive is immutable; comparison is recorded, not an arbitrary patch allowlist.
    import subprocess
    original=subprocess.check_output(['git','show','stage4c-stable:releases/stage_4c/STAGE4C.PRG'],cwd=ROOT)
    if old!=original:raise ValueError('Stage4c Stable archive changed')
    for name in ['VYLV.DAT','VYGR.DAT']:
        if BASE.sha((ROOT/'assets'/name).read_bytes())!=BASE.DATA_SHA256[name]:raise ValueError('Original data changed')
    return {'baseline':'stage4c-stable','baseline_prg_sha256':BASE.sha(old),
            'changed_bytes':sum(a!=b for a,b in zip(old,prg)),
            'player_speed':'1 pixel/frame','formation_speed':'1 pixel/2 frames', 'stable':False}

def main():
    import analyze_stage5a_capacity as CAPACITY
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kickass',default=os.environ.get('KICKASS_JAR'))
    parser.add_argument('--output',type=Path,default=ROOT/'releases/stage_5a')
    args=parser.parse_args()
    if not args.kickass:parser.error('--kickass required')
    jar=Path(args.kickass).resolve()
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256:raise ValueError('Expected pinned KickAssembler5.25')
    PLAYER.verify_player_assets();EXPLOSIONS.build()
    capacity=CAPACITY.audit()
    for f in (ROOT/'releases/stage_4c').iterdir():
        original=subprocess.check_output(['git','show','stage4c-stable:releases/stage_4c/'+f.name],cwd=ROOT)
        if f.read_bytes()!=original:raise ValueError('Stable release changed: '+f.name)
    for component in ['hud','shots','templates']:
        stable=(ROOT/'src/engine'/f'stage4c_{component}.asm').read_text()
        new=(ROOT/'src/engine'/f'stage5a_{component}.asm').read_text()
        if stable.replace('stage4c','stage5a').replace('Stage 4c','Stage 5a')!=new:
            raise ValueError('Protected component changed: '+component)
    (ROOT/'src/engine/stage5a_mapping.asm').write_text(mapping_source())
    sources=['stage5a.asm']+[f'stage5a_{c}.asm' for c in ['hud','templates','shots','mapping','game','offscreen','entry','attack','data','level']]
    with tempfile.TemporaryDirectory(prefix='vyper-5a-') as directory:
        work=Path(directory)
        for name,payload in BASE.baseline_files().items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                target=work/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
        shutil.copytree(ROOT/'assets/explosions',work/'explosion_assets')
        (work/'player_assets').mkdir()
        for name in PLAYER.PLAYER_FILES:shutil.copyfile(ROOT/'assets/player'/name,work/'player_assets'/name)
        for name in sources:shutil.copyfile(ROOT/'src/engine'/name,work/name)
        result=subprocess.run(['java','-jar',str(jar),'stage5a.asm','-o','STAGE5A.PRG','-symbolfile','-showmem'],cwd=work,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(result.stdout,end='');result.check_returncode()
        prg=(work/'STAGE5A.PRG').read_bytes();sym=(work/'stage5a.sym').read_text()
        comparison=verify_engine(prg,symbols(sym))
        entries=[('STAGE5A',prg,0x82)]
        for name in ['VYLV.DAT','VYGR.DAT']:entries.append((name,(ROOT/'assets'/name).read_bytes(),0x81))
        disk=bytearray(BASE.build_disk(entries));header=39*40*256
        disk[header+4:header+20]=b'VYPER STAGE 5A'.ljust(16,b'\xa0');disk=bytes(disk)
        report={'stage':'5a','issue':23,'stable':False,'baseline':'stage4c-stable',
                'assembler':'KickAssembler5.25','comparison':comparison,
                'files':BASE.verify_disk(disk,entries),'capacity':capacity['summary'],
                'controls':{'+':'next level, clamp100, physical release debounce','-':'previous level, clamp1','button':'new Port2 press in LEVEL_CLEAR,100->1','R':'GAME_OVER restart Level1, score0, lives3, retain highscore','X':'clean BASIC exit'},
                'restrictions':{'attack_disabled_levels':[25,50,99,100],
                                'reason':'user-approved pending original one-byte special curve semantics',
                                'mapping':'only14->15 confirmed; all other historical table entries provisional'},
                'memory':{'active_record':'$12000-$126FF','header':'$7600-$7607','code':'below$A000; manager$6000 replaces obsolete initial colour template',
                          'private_pixies':'$10000-$115FF (22x256, existing)','blank_template':'$6700-$67FF',
                          'runtime_metadata':'$1D80-$1DB1 and $6A20-$6AD7','groups':4,
                          'entry_cursor_bits':16,'entry_delay_bits':16,'rrb_slots':24,'screen_stride':192},
                'runtime_xemu':'NOT_RUN; user confirmation required'}
        outputs={'STAGE5A.PRG':prg,'VYPER_STAGE5A.d81':disk,'STAGE5A.sym':sym.encode(),
                 'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),
                 'memory-map.txt':(result.stdout[result.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode(),
                 'vylv_vygr_mapping.json':(ROOT/'assets/vylv_vygr_mapping.json').read_bytes()}
        for name in sources:outputs[name]=(ROOT/'src/engine'/name).read_bytes()
        outputs['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {name}\n' for name,b in sorted(outputs.items())).encode()
        args.output.mkdir(parents=True,exist_ok=True)
        for name,b in outputs.items():(args.output/name).write_bytes(b)
    print('Verified all100 original records, stable archive, preserved HUD/projectiles and D81.')
if __name__=='__main__':main()
