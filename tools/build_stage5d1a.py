#!/usr/bin/env python3
"""Stage5d1 title/loader + user-confirmed B2 ENTRY integration; protect baselines."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as BASE
import build_stage3b3 as PLAYER
import build_stage5c as GAME
import convert_stage5c_palettes as PAL
import convert_stage5d1_title as TITLE
ROOT=Path(__file__).resolve().parents[1]
COMPONENTS=GAME.COMPONENTS+['_palettes']
BASELINE='e295fa81d5c18b009eb22841ea5db2da7c8a6279'
B2_COMMIT='4cb73e71974f4102bdad003cdbc1cae1b0896407'
def protect_stable():
    import build_stage5d1 as PREVIOUS
    checked=PREVIOUS.protect_stable()
    for name in subprocess.check_output(['git','ls-tree','-r','--name-only',BASELINE,'--','src/engine','releases/stage_5d_1'],cwd=ROOT,text=True).splitlines():
        if (ROOT/name).read_bytes()!=subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT):raise ValueError('Protected baseline changed: '+name)
    for suffix in COMPONENTS+['_title']:
        new=(ROOT/f'src/engine/stage5d1a{suffix}.asm').read_text().replace('stage5d1a','stage5d1').replace('Stage 5d-1a','Stage 5d-1').replace('STAGE5D1A','STAGE5D1')
        if suffix=='':new=new.replace('\n.import source "stage5d1_entry_projection.asm"\n','')
        if suffix=='_entry':
            for hook in ['    jsr ygeometry.clear\n','    jsr ygeometry.restore\n','    jsr ygeometry.finish_entry\n']:new=new.replace(hook,'')
            new=new.replace('    jmp ygeometry.postframe','    jmp attack.a_postframe')
        if new!=(ROOT/f'src/engine/stage5d1{suffix}.asm').read_text():raise ValueError('Unexpected gameplay change: '+suffix)
    original=subprocess.check_output(['git','show',B2_COMMIT+':src/tests/debut_y_b2/y_geometry.asm'],cwd=ROOT).decode()
    expected=original.replace('.import source "variant.inc"','.const TEST_VARIANT=2 // Confirmed B2: ENTRY only, original Y minus 16')
    if (ROOT/'src/engine/stage5d1a_entry_projection.asm').read_text()!=expected:raise ValueError('B2 source differs')
    return checked
def build(jar,output):
    jar=Path(jar).resolve();output=Path(output).resolve()
    if output.is_relative_to(ROOT/'releases') and not output.is_relative_to(ROOT/'releases/stage_5d_1_b2'):raise ValueError('Cannot overwrite other stages')
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256:raise ValueError('KickAssembler5.25 required')
    protected=protect_stable();PLAYER.verify_player_assets()
    lvl=(ROOT/'assets/VYLV.DAT').read_bytes();gr=(ROOT/'assets/stage5b/VYGR.DAT').read_bytes();cl=(ROOT/'assets/stage5c/VYCL.DAT').read_bytes();PAL.decode(cl)
    if BASE.sha(lvl)!=BASE.DATA_SHA256['VYLV.DAT']:raise ValueError('Original VYLV changed')
    for name,payload in [('VYLV.DAT',lvl),('VYGR.DAT',gr),('VYCL.DAT',cl)]:
        if payload!=(ROOT/'releases/stage_5c'/name).read_bytes():raise ValueError('Stable game DAT changed: '+name)
    sources=[f'stage5d1a{s}.asm' for s in COMPONENTS]+['stage5d1a_title.asm','stage5d1a_entry_projection.asm']
    with tempfile.TemporaryDirectory(prefix='vyper-5d1-') as d:
        w=Path(d);ti,title=TITLE.build(w)
        for name,payload in BASE.baseline_files().items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                p=w/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
        shutil.copytree(ROOT/'assets/explosions',w/'explosion_assets');(w/'player_assets').mkdir()
        for name in PLAYER.PLAYER_FILES:shutil.copyfile(ROOT/'assets/player'/name,w/'player_assets'/name)
        for name in sources:shutil.copyfile(ROOT/'src/engine'/name,w/name)
        for name,payload in [('VYLV.DAT',lvl),('VYGR.DAT',gr),('VYCL.DAT',cl)]:(w/name).write_bytes(payload)
        run=subprocess.run(['java','-jar',str(jar),'stage5d1a.asm','-o','STAGE5D1A.PRG','-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(run.stdout,end='');run.check_returncode()
        prg=(w/'STAGE5D1A.PRG').read_bytes()
        entries=[('STAGE5D1A',prg,0x82),('VYTI.DAT',ti,0x81),('VYLV.DAT',lvl,0x81),('VYGR.DAT',gr,0x81),('VYCL.DAT',cl,0x81)]
        disk=bytearray(BASE.build_disk(entries));head=39*40*256;disk[head+4:head+20]=b'VYPER STAGE5D1A'.ljust(16,b'\xa0');disk=bytes(disk)
        files=BASE.verify_disk(disk,entries)
        report={'stage':'5d-1a','integration_baseline':BASELINE,'b2_commit':B2_COMMIT,'issue':41,'stable':False,'baseline':'stage5c-stable','baseline_commit':subprocess.check_output(['git','rev-parse','stage5c-stable^{}'],cwd=ROOT).decode().strip(),'renderer':'stage5d0-stable','renderer_commit':subprocess.check_output(['git','rev-parse','stage5d0-stable^{}'],cwd=ROOT).decode().strip(),'protected_files':protected,'assembler':'KickAssembler5.25','files':files,'title':title,'gameplay':'Stage5d1 title/loader preserved; confirmed B2 ENTRY hooks and projection only','xemu':'NOT_RUN; user acceptance required','handoff':'s3b.loading_complete -> restore video/palette/cursor -> save phase-shared bootstrap -> s3b.menu_or_game_start -> Level1'}
        out={'STAGE5D1A.PRG':prg,'STAGE5D1A.sym':(w/'stage5d1a.sym').read_bytes(),'VYPER_STAGE5D1A.d81':disk,'VYTI.DAT':ti,'VYLV.DAT':lvl,'VYGR.DAT':gr,'VYCL.DAT':cl,'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(run.stdout[run.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()}
        for name in sources+['title_layout.inc','conversion-report.json','title_screen.bin','title_fcm_unique.bin']:out[name]=(w/name).read_bytes()
        out['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {n}\n' for n,b in sorted(out.items())).encode()
        output.mkdir(parents=True,exist_ok=True)
        for n,b in out.items():(output/n).write_bytes(b)
    print('Stable baselines protected; confirmed B2 source, original DATs, title pixels and D81 chains verified.')
    return report
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kickass',default=os.environ.get('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/stage_5d_1_b2');a=p.parse_args()
    if not a.kickass:p.error('--kickass required')
    build(a.kickass,a.output)
if __name__=='__main__':main()
