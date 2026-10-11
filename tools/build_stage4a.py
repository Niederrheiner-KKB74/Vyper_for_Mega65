#!/usr/bin/env python3
"""Reproduce Stage 4a from stage3b5c-stable; never modify stable releases."""
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
    old=(ROOT/'releases/stage_3b5c/STAGE3B5C.PRG').read_bytes()
    if BASE.sha(old)!='2de5edcc91b8d4a24afb7ec427b89ca0b17cbe4841b5cb5d9fe2c0a6f5f62d04':
        raise ValueError('Stable 3b-5c baseline mismatch')
    original=symbols((ROOT/'releases/stage_3b5c/STAGE3B5C.sym').read_text())
    def at(a):return a-0x2001+2
    if len(prg)!=at(0xcb00):raise ValueError('Unexpected PRG extent')
    expected=bytearray(old)+bytearray(len(prg)-len(old))
    patches=[]
    for oldname,newname,lo,hi in [('c_init','r_init',0x2100,0x2400),('c_key','r_key',0x2100,0x2400),
        ('c_move','r_move',0x2100,0x2400),('c_objects','r_objects',0x2100,0x2400),
        ('c_tick','r_tick',0x2100,0x2400),('c_render','r_render',original['hud_render'],original['hud_render']+3)]:
        call=b'\x20'+original[oldname].to_bytes(2,'little')
        sites=[i for i in range(at(lo),at(hi)) if old[i:i+3]==call]
        if len(sites)!=1:raise ValueError('Nonunique hook '+oldname)
        i=sites[0];expected[i:i+3]=b'\x20'+names[newname].to_bytes(2,'little');patches.append(hex(i-2+0x2001))
    # User-authorized extension to all 25 rows; no layout or object limits change.
    row_patches=[]
    def replace_one(lo,hi,before,after):
        sites=[i for i in range(at(lo),at(hi)) if old[i:i+len(before)]==before]
        if len(sites)!=1:raise ValueError('Nonunique row patch '+hex(lo))
        i=sites[0];expected[i:i+len(after)]=after;row_patches.append(hex(i-2+0x2001))
    for label in ('v012a_init_loop','v014_prepare_row'):
        replace_one(original[label]-2,original[label],b'\xa2\x02',b'\xa2\x00')
    for lo,hi in [('v012a_init_loop','v014_prepare_row'),('v014_prepare_row','v012a_blank_original'),
                  ('c_render_clear','c_render_player'),('c_render_finish','c_render_enemy')]:
        replace_one(original[lo],original[hi],b'\xe0\x17',b'\xe0\x19')
    for lo,hi in [('c_render','c_render_clear'),('c_render_paths','c_render_finish')]:
        replace_one(original[lo],original[hi],b'\xa2\x02',b'\xa2\x00')
    replace_one(original['v014_append'],original['v014_append_done'],b'\xe0\x17',b'\xe0\x19')
    i=at(original['v014_append']+7)
    if old[i:i+3]!=b'\xe0\x02\x90':raise ValueError('Unexpected lower row guard')
    expected[i:i+4]=b'\xea'*4;row_patches.append(hex(i-2+0x2001))
    for lo,hi in ((0x4e30,0x5000),(0x8660,0x8800),(0x8e20,0x9000),(0xca00,0xcb00)):
        if lo<0xca00 and any(old[at(lo):at(hi)]):raise ValueError('Occupied region '+hex(lo))
        expected[at(lo):at(hi)]=prg[at(lo):at(hi)]
    if expected!=prg:
        raise ValueError('Unexpected baseline changes '+str([hex(i-2+0x2001) for i,(a,b) in enumerate(zip(expected,prg)) if a!=b][:20]))
    for name,address in original.items():
        if name in names and names[name]!=address:raise ValueError('Old label moved '+name)
    return {'baseline_prg_sha256':BASE.sha(old),'engine_hooks':patches,'full_height_row_patches':row_patches,'changed_bytes':sum(a!=b for a,b in zip(old,prg)),'extended_bytes':len(prg)-len(old)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kickass',default=os.environ.get('KICKASS_JAR'))
    parser.add_argument('--output',type=Path,default=ROOT/'releases/stage_4a')
    args=parser.parse_args()
    if not args.kickass: parser.error('--kickass required')
    jar=Path(args.kickass).resolve()
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256: raise ValueError('Expected official pinned KickAssembler 5.25')
    PLAYER.verify_player_assets()
    EXPLOSIONS.build()
    if '.const c_EXP_FRAMES='+str(len(EXPLOSIONS.VALID_FRAME_INDICES)) not in (ROOT/'src/engine/stage4a_game.asm').read_text():
        raise ValueError('Explosion animation count does not match validated original records')
    generated=mapping_source()
    (ROOT/'src/engine/stage4a_mapping.asm').write_text(generated)
    sources=['stage4a.asm','stage4a_hud.asm','stage4a_templates.asm','stage4a_shots.asm','stage4a_mapping.asm','stage4a_game.asm','stage4a_offscreen.asm']
    with tempfile.TemporaryDirectory(prefix='vyper-4a-') as directory:
        work=Path(directory)
        for name,payload in BASE.baseline_files().items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                target=work/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(payload)
        shutil.copytree(ROOT/'assets/explosions',work/'explosion_assets')
        (work/'player_assets').mkdir()
        for name in PLAYER.PLAYER_FILES: shutil.copyfile(ROOT/'assets/player'/name,work/'player_assets'/name)
        for name in sources: shutil.copyfile(ROOT/'src/engine'/name,work/name)
        result=subprocess.run(['java','-jar',str(jar),'stage4a.asm','-o','STAGE4A.PRG','-symbolfile','-showmem'],cwd=work,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(result.stdout,end=''); result.check_returncode()
        prg=(work/'STAGE4A.PRG').read_bytes()
        sym=(work/'stage4a.sym').read_text()
        comparison=verify_engine(prg,symbols(sym))
        entries=[('STAGE4A',prg,0x82)]
        for name in ('VYLV.DAT','VYGR.DAT'):
            payload=(ROOT/'assets'/name).read_bytes()
            if BASE.sha(payload)!=BASE.DATA_SHA256[name]: raise ValueError('Original DAT mismatch')
            entries.append((name,payload,0x81))
        disk=bytearray(BASE.build_disk(entries)); header=39*40*256
        disk[header+4:header+20]=b'VYPER STAGE 4A'.ljust(16,b'\xa0'); disk=bytes(disk)
        report={'assembler':'KickAssembler 5.25','baseline':'stage3b5c-stable','comparison':comparison,'files':BASE.verify_disk(disk,entries),'hud':{'mode':'H640, CHARXSCALE=60; logical X doubled','logical_playfield_right_exclusive':240,'physical_hud_x':480,'physical_hud_width':160,'screen_row_stride':128,'screen_entries_per_row':64,'dynamic_row_offset':84,'font':'authored thin 5x7 glyphs, 8-column cells','colour_ram_bytes_saved':3200,'life_columns':4,'life_rows':2,'life_logical_x':[245,262,279,296],'life_y':[58,75],'initial_lives':3,'player2_active':False},'projectiles':{'player_channels':[0,1],'enemy_channels':[2,3,4,5],'free_channels':[6,7],'player_speed':3,'enemy_vy':1,'max_abs_vx':2,'enemy_probability':'1/8 per eligible frame','enemy_cooldown_frames':12,'test_enemy_0based':18,'attack_window_frames':96,'attack_period_frames':128,'test_toggle':'T','coordinates':'logical 240x200; sprite native X/Y from D04C-D04F','collisions':True},'mapping_status':json.loads((ROOT/'assets/vylv_vygr_mapping.json').read_text()),'runtime_xemu':'NOT RUN; user confirmation required'}
        outputs={'STAGE4A.PRG':prg,'VYPER_STAGE4A.d81':disk,'STAGE4A.sym':sym.encode(),'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(result.stdout[result.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()}
        for name in sources: outputs[name]=(ROOT/'src/engine'/name).read_bytes()
        report['offscreen']={'controls':{'F':'toggle isolated test','N':'next direction','P':'pause movement','X':'BASIC'},'signed_coordinates':'16-bit','clip_rect_exclusive':[0,0,240,200],'cases':['top','bottom','left','right','top-left diagonal'],'crop_buffer':'$CA00-$CAFF','diagnostics':'$1D00-$1D3F','stable':False}
        report['stage3b5c_preserved']={'explosions':json.loads((ROOT/'assets/explosions/conversion.json').read_text()),'enemies':23,'explosion_ticks_per_frame':3,'respawn_ticks':150,'blink_period_ticks':25,'score_bits':32,'score_overflow':'saturate','display':'low seven decimal digits','baseline_xemu':'Stage 3b-5c accepted by user; Stage 4a pending'}
        outputs['build-report.json']=(json.dumps(report,indent=2)+'\n').encode()
        outputs['vylv_vygr_mapping.json']=(ROOT/'assets/vylv_vygr_mapping.json').read_bytes()
        outputs['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {name}\n' for name,b in sorted(outputs.items())).encode()
        args.output.mkdir(parents=True,exist_ok=True)
        for name,b in outputs.items(): (args.output/name).write_bytes(b)
    print('Verified protected baseline, original explosion conversion and D81.')
if __name__=='__main__': main()
