#!/usr/bin/env python3
"""Build Stage5c from protected stage5b-stable, original RGB4 and all three SEQs."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as BASE
import build_stage3b3 as PLAYER
import convert_stage5c_palettes as PAL
ROOT=Path(__file__).resolve().parents[1]
COMPONENTS=['','_hud','_templates','_shots','_mapping','_game','_offscreen','_entry','_attack','_data','_level']
def protect_stable():
    if BASE.sha((ROOT/"assets/VYLV.DAT").read_bytes())!=BASE.DATA_SHA256["VYLV.DAT"]:raise ValueError("Original VYLV changed")
    for folder in ['src/engine','releases/stage_5b','assets/stage5b']:
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only','stage5b-stable','--',folder],cwd=ROOT).decode().splitlines()
        for name in paths:
            if folder=='src/engine' and not Path(name).name.startswith('stage5b'):continue
            old=subprocess.check_output(['git','show',f'stage5b-stable:{name}'],cwd=ROOT)
            if (ROOT/name).read_bytes()!=old:raise ValueError('Stable changed: '+name)
    for suffix in COMPONENTS:
        old=(ROOT/f'src/engine/stage5b{suffix}.asm').read_text()
        expected=old.replace('stage5b','stage5c').replace('Stage 5b','Stage 5c').replace('STAGE5B','STAGE5C')
        if suffix=='':
            expected=expected.replace('// Stage 5c / Issue #16 on stage4b1-stable: original attack bytes and moving formation.\n// Original selection/endmarker details remain explicitly provisional; see docs/stage5c_attack_formation.md.','// Stage 5c / Issue #31, from protected stage5b-stable: original level palettes.\n// Gameplay retained; palette format/evidence: docs/stage5c_original_palettes.md.')
            expected=expected.replace('    php\n    cli\n    ldx #<title','    php\n    cli\n    jsr pal.capture_device\n    ldx #<title',1)
            expected=expected.replace('    ldx #8\n    ldy #2\n    jsr $ffba','    ldx pal.device\n    ldy #2\n    jsr $ffba',1)
            expected=expected.replace('graphic_sum_ok:\n','graphic_sum_ok:\n    jsr pal.load\n    lda error\n    beq !valid+\n    jmp failed\n!valid:\n',1)
            expected=expected.replace('title: .text "STAGE 3B-2: LOADING ORIGINAL DATA"','title: .text "STAGE 5C: LOADING ORIGINAL DATA"')
            expected=expected.replace('success_msg: .text "VYLV + VYGR LOADED AND VERIFIED"','success_msg: .text "VYLV/VYGR/VYCL VERIFIED"')
            expected=expected.replace('error_msg: .text "STAGE 3B-2 LOAD ERROR $"','error_msg: .text "STAGE 5C LOAD ERROR $"')
            expected=expected.replace('    bne player_palette_loop\n    rts','    bne player_palette_loop\n    jmp pal.apply',1)
            expected=expected.replace('    lda #$08\n    jsr v012a_store\n    iny\n    lda #0\n    jsr v012a_store\n    lda VIC_D030','    lda #$08\n    jsr v012a_store\n    iny\n    jsr pal.glyph_colour\n    jsr v012a_store\n    lda VIC_D030',1)
            expected+='\n.import source "stage5c_palettes.asm"\n'
        if suffix=='_level':expected=expected.replace('    jsr v014_init_objects\n    jsr shots.p_init','    jsr pal.apply\n    jsr v014_init_objects\n    jsr shots.p_init',1)
        if suffix=='_hud':expected=expected.replace('    .byte 0,$6b,0','    .byte 0,$56,1 // Stage5c: extended colour backup $15600-$15A7F, after private pixies.')
        if (ROOT/f'src/engine/stage5c{suffix}.asm').read_text()!=expected:raise ValueError('Gameplay component changed: '+suffix)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kickass',default=os.environ.get('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/stage_5c');a=p.parse_args()
    if not a.kickass:p.error('--kickass required')
    destination=a.output.resolve()
    release_root=(ROOT/'releases').resolve()
    if destination.is_relative_to(release_root) and not destination.is_relative_to(release_root/'stage_5c'):raise ValueError('Output may not overwrite older release directories')
    jar=Path(a.kickass).resolve()
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256:raise ValueError('Expected pinned KickAssembler5.25')
    protect_stable();data,pal=PAL.build();PLAYER.verify_player_assets()
    sources=[f'stage5c{s}.asm' for s in COMPONENTS]+['stage5c_palettes.asm']
    with tempfile.TemporaryDirectory(prefix='vyper-5c-') as d:
        work=Path(d)
        for name,payload in BASE.baseline_files().items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                target=work/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
        shutil.copytree(ROOT/'assets/explosions',work/'explosion_assets')
        (work/'player_assets').mkdir()
        for name in PLAYER.PLAYER_FILES:shutil.copyfile(ROOT/'assets/player'/name,work/'player_assets'/name)
        for name in sources:shutil.copyfile(ROOT/'src/engine'/name,work/name)
        (work/'VYCL.DAT').write_bytes(data)
        run=subprocess.run(['java','-jar',str(jar),'stage5c.asm','-o','STAGE5C.PRG','-symbolfile','-showmem'],cwd=work,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(run.stdout,end='');run.check_returncode()
        prg=(work/'STAGE5C.PRG').read_bytes();sym=(work/'stage5c.sym').read_bytes()
    entries=[('STAGE5C',prg,0x82),('VYLV.DAT',(ROOT/'assets/VYLV.DAT').read_bytes(),0x81),('VYGR.DAT',(ROOT/'assets/stage5b/VYGR.DAT').read_bytes(),0x81),('VYCL.DAT',data,0x81)]
    disk=bytearray(BASE.build_disk(entries));head=39*40*256;disk[head+4:head+20]=b'VYPER STAGE 5C'.ljust(16,b'\xa0');disk=bytes(disk)
    report={'stage':'5c','issue':31,'stable':False,'baseline':'stage5b-stable','baseline_commit':subprocess.check_output(['git','rev-parse','stage5b-stable^{}'],cwd=ROOT).decode().strip(),
        'assembler':'KickAssembler5.25','files':BASE.verify_disk(disk,entries),'palette':pal,
        'memory':{'VYCL':'$5C300-$5C4DB','VYCL_mirror':'$6D00-$6EDB','palette_code':'$6B00-$6CFF','palette_state':'$6EF0-$6EF3','private_pixies':'$14000-$155FF; unchanged','extended_colour_backup':'$15600-$15A7F (relocated from $6B00-$6F7F)' },
        'palette_isolation':{'enemies':'bank1 entries17..24; transparent16','explosions':'bank1 entries0..15, unchanged','player_HUD_projectiles':'bank2 unchanged','BASIC_ROM':'bank3 untouched'},
        'runtime_xemu':'NOT_RUN; user acceptance required','original_Amiga_code_usage':'not independently proven','restrictions':{'attack_disabled_levels':[25,50,99,100]}}
    out={'STAGE5C.PRG':prg,'STAGE5C.sym':sym,'VYPER_STAGE5C.d81':disk,'VYCL.DAT':data,'VYLV.DAT':entries[1][1],'VYGR.DAT':entries[2][1],
        'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(run.stdout[run.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode(),
        'original_color_level_mapping.csv':(ROOT/'assets/original_color_level_mapping.csv').read_bytes(),'original_color_palettes_rgb4.csv':(ROOT/'assets/original_color_palettes_rgb4.csv').read_bytes()}
    for name in sources:out[name]=(ROOT/'src/engine'/name).read_bytes()
    out['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {n}\n' for n,b in sorted(out.items())).encode()
    a.output.mkdir(parents=True,exist_ok=True)
    for name,b in out.items():(a.output/name).write_bytes(b)
    print('Verified Stable5b protection, original palette bytes and four D81 directory chains.')
if __name__=='__main__':main()
