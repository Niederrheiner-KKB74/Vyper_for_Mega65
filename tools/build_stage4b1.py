#!/usr/bin/env python3
"""Build Stage 4b-1 Level-1 entry from stage4b-stable; never modify stable releases."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
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
    old=(ROOT/'releases/stage_4b/STAGE4B.PRG').read_bytes()
    pinned='7fbd513baaa393cbde281dd1875bfc6cb8da7cae47efea2585e9b2f70e1dc9d4'
    if BASE.sha(old)!=pinned:raise ValueError('Stage 4b Stable mismatch')
    if len(prg)!=len(old):raise ValueError('Unexpected PRG extension')
    previous=symbols((ROOT/'releases/stage_4b/STAGE4B.sym').read_text())
    expected=bytearray(old)
    def at(a):return a-0x2001+2
    for lo,hi in ((0x5700,0x5b80),(0x5c20,0x5c80),(0x7ee2,0x7f71)):
        expected[at(lo):at(hi)]=prg[at(lo):at(hi)]
    relocations=[]
    for i in range(3,len(old)-1):
        if expected[i:i+2]==prg[i:i+2]:continue
        if old[i-1] not in (0x20,0x4c) or prg[i-1]!=old[i-1]:continue
        before=int.from_bytes(old[i:i+2],'little');after=int.from_bytes(prg[i:i+2],'little')
        labels=[n for n,v in previous.items() if v==before and names.get(n)==after and n.startswith('e_')]
        if labels:
            expected[i:i+2]=prg[i:i+2];relocations.append(labels[0])
    if expected!=prg:raise ValueError('Changes outside visibility controller/relocations')
    return {'baseline':'stage4b-stable','baseline_prg_sha256':pinned,'changed_bytes':sum(a!=b for a,b in zip(old,prg)),'extended_bytes':0,'relocations':relocations,'movement_timing':'unchanged; visibility after first nonzero delta','stable':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kickass',default=os.environ.get('KICKASS_JAR'))
    parser.add_argument('--output',type=Path,default=ROOT/'releases/stage_4b_1')
    args=parser.parse_args()
    if not args.kickass: parser.error('--kickass required')
    jar=Path(args.kickass).resolve()
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256: raise ValueError('Expected official pinned KickAssembler 5.25')
    PLAYER.verify_player_assets()
    EXPLOSIONS.build()
    if '.const c_EXP_FRAMES='+str(len(EXPLOSIONS.VALID_FRAME_INDICES)) not in (ROOT/'src/engine/stage4b1_game.asm').read_text():
        raise ValueError('Explosion animation count does not match validated original records')
    generated=mapping_source()
    (ROOT/'src/engine/stage4b1_mapping.asm').write_text(generated)
    sources=['stage4b1.asm','stage4b1_hud.asm','stage4b1_templates.asm','stage4b1_shots.asm','stage4b1_mapping.asm','stage4b1_game.asm','stage4b1_offscreen.asm','stage4b1_entry.asm']
    with tempfile.TemporaryDirectory(prefix='vyper-4b-') as directory:
        work=Path(directory)
        for name,payload in BASE.baseline_files().items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                target=work/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(payload)
        shutil.copytree(ROOT/'assets/explosions',work/'explosion_assets')
        (work/'player_assets').mkdir()
        for name in PLAYER.PLAYER_FILES: shutil.copyfile(ROOT/'assets/player'/name,work/'player_assets'/name)
        for name in sources: shutil.copyfile(ROOT/'src/engine'/name,work/name)
        result=subprocess.run(['java','-jar',str(jar),'stage4b1.asm','-o','STAGE4B1.PRG','-symbolfile','-showmem'],cwd=work,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(result.stdout,end=''); result.check_returncode()
        prg=(work/'STAGE4B1.PRG').read_bytes()
        sym=(work/'stage4b1.sym').read_text()
        comparison=verify_engine(prg,symbols(sym))
        entries=[('STAGE4B1',prg,0x82)]
        for name in ('VYLV.DAT','VYGR.DAT'):
            payload=(ROOT/'assets'/name).read_bytes()
            if BASE.sha(payload)!=BASE.DATA_SHA256[name]: raise ValueError('Original DAT mismatch')
            entries.append((name,payload,0x81))
        disk=bytearray(BASE.build_disk(entries)); header=39*40*256
        disk[header+4:header+20]=b'VYPER STAGE 4B1'.ljust(16,b'\xa0'); disk=bytes(disk)
        report={'assembler':'KickAssembler 5.25','baseline':'stage4b-stable','comparison':comparison,'files':BASE.verify_disk(disk,entries),'hud':{'mode':'H640, CHARXSCALE=60; logical X doubled','logical_playfield_right_exclusive':240,'physical_hud_x':480,'physical_hud_width':160,'screen_write_addressing':'45GS02 32-bit indirect, bypasses SYS MAPH bank-3 KERNAL','dynamic_clear':'25 physical DMA copies of 100 bytes; valid GOTOX640/NCM200 empty records','screen_row_stride':192,'screen_entries_per_row':96,'dynamic_row_offset':84,'font':'authored thin 5x7 glyphs, 8-column cells','colour_ram_bytes_saved':4800,'life_columns':4,'life_rows':2,'life_logical_x':[245,262,279,296],'life_y':[58,75],'initial_lives':3,'player2_active':False},'projectiles':{'player_channels':[0,1],'enemy_channels':[2,3,4,5],'free_channels':[6,7],'player_speed':3,'enemy_vy':1,'max_abs_vx':2,'enemy_probability':'1/8 per eligible frame','enemy_cooldown_frames':12,'test_enemy_0based':18,'attack_window_frames':96,'attack_period_frames':128,'test_toggle':'T','coordinates':'logical 240x200; sprite native X/Y from D04C-D04F','collisions':True},'mapping_status':json.loads((ROOT/'assets/vylv_vygr_mapping.json').read_text()),'runtime_xemu':'NOT RUN; user confirmation required'}
        outputs={'STAGE4B1.PRG':prg,'VYPER_STAGE4B1.d81':disk,'STAGE4B1.sym':sym.encode(),'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(result.stdout[result.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()}
        for name in sources: outputs[name]=(ROOT/'src/engine'/name).read_bytes()
        report['stage4b1']={'scope':'Issue 14: hide ENTRY spawn/leading-zero ticks until first movement; positions/timing unchanged','player_start':[112,184],'entry_parameters':{'point_ticks':1,'start_point_tick':1,'group_delay':0,'return_step':1},'entry_crop_pool':'$10000-$115FF','entry_diagnostics':'$1D40-$1D60 and $1E00-$1EFF','entry_visibility':'$1D64-$1D7A','default_test_attack':False,'player_y_fixed':184,'player_x_inclusive':[0,224],'original_entry_curves':'sign magnitude nibble decoder; two parallel groups, 16-frame spacing; one point/frame, separate spawn point; +/-1 both axes State 2; Debut timing/anchor pending original-binary verification','stable':False}
        report['offscreen']={'controls':{'F':'toggle isolated test','N':'next direction','P':'pause movement','X':'BASIC'},'signed_coordinates':'16-bit','clip_rect_exclusive':[0,0,240,200],'cases':['top','bottom','left','right','top-left diagonal'],'crop_buffer':'$CA00-$CAFF','diagnostics':'$1D00-$1D3F','stable':False}
        report['stage3b5c_preserved']={'explosions':json.loads((ROOT/'assets/explosions/conversion.json').read_text()),'enemies':22,'explosion_ticks_per_frame':3,'respawn_ticks':150,'blink_period_ticks':25,'score_bits':32,'score_overflow':'saturate','display':'low seven decimal digits','baseline_xemu':'Stage 3b-5c accepted by user; Stage 4b-1 pending'}
        outputs['build-report.json']=(json.dumps(report,indent=2)+'\n').encode()
        outputs['vylv_vygr_mapping.json']=(ROOT/'assets/vylv_vygr_mapping.json').read_bytes()
        outputs['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {name}\n' for name,b in sorted(outputs.items())).encode()
        args.output.mkdir(parents=True,exist_ok=True)
        for name,b in outputs.items(): (args.output/name).write_bytes(b)
    print('Verified protected baseline, original explosion conversion and D81.')
if __name__=='__main__': main()
