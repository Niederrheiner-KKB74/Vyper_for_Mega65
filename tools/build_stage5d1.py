#!/usr/bin/env python3
"""Stage5c Stable engine + Stage5d0 Stable FCM title; preserve both baselines."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as BASE
import build_stage3b3 as PLAYER
import build_stage5c as GAME
import convert_stage5c_palettes as PAL
import convert_stage5d1_title as TITLE
ROOT=Path(__file__).resolve().parents[1]
COMPONENTS=GAME.COMPONENTS+['_palettes']
def protect_stable():
    checked=0
    for tag,folders in [('stage5c-stable',['src/engine','releases/stage_5c','assets/stage5c']),('stage5d0-stable',['src/tests/stage5d0.asm','assets/stage5d0','releases/stage_5d0','tools/convert_stage5d0_title.py'])]:
        names=subprocess.check_output(['git','ls-tree','-r','--name-only',tag,'--',*folders],cwd=ROOT).decode().splitlines()
        for name in names:
            if name.startswith('src/engine/') and not Path(name).name.startswith('stage5c'):continue
            expected=subprocess.check_output(['git','show',tag+':'+name],cwd=ROOT)
            if (ROOT/name).read_bytes()!=expected:raise ValueError('Stable changed: '+name)
            checked+=1
    # All gameplay algorithms remain the normalized stable sources.
    for suffix in COMPONENTS:
        new=(ROOT/f'src/engine/stage5d1{suffix}.asm').read_text().replace('stage5d1','stage5c').replace('Stage 5d-1','Stage 5c').replace('STAGE5D1','STAGE5C')
        old=(ROOT/f'src/engine/stage5c{suffix}.asm').read_text()
        if suffix=='':
            new=new.replace('// Stage 5c / Issue #35, from protected stage5c-stable:','// Stage 5c / Issue #31, from protected stage5b-stable:')
            new=new.replace('    jsr titlecache.tc_restore // restore shared bootstrap on every game exit\n','')
            new=new.replace(' .import source "stage5c_title.asm"','*=$4000\n.fill $800,0')
            a=new.index('.namespace s3b {');b=new.index('.import source "stage5c_data.asm"',a)
            x=old.index('.namespace s3b {');y=old.index('.import source "stage5c_data.asm"',x)
            new=new[:a]+old[x:y]+new[b:] # Only standalone loader controller is changed.
        elif suffix=='_palettes':new=new.replace('filename: .text "VYCL.DAT,S,R"\n.byte 0','filename: .text "VYCL.DAT,S,R"')
        if new!=old:raise ValueError('Gameplay component changed: '+suffix)
    return checked
def build(jar,output):
    jar=Path(jar).resolve();output=Path(output).resolve()
    if output.is_relative_to(ROOT/'releases') and not output.is_relative_to(ROOT/'releases/stage_5d_1'):raise ValueError('Cannot overwrite other stages')
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256:raise ValueError('KickAssembler5.25 required')
    protected=protect_stable();PLAYER.verify_player_assets()
    lvl=(ROOT/'assets/VYLV.DAT').read_bytes();gr=(ROOT/'assets/stage5b/VYGR.DAT').read_bytes();cl=(ROOT/'assets/stage5c/VYCL.DAT').read_bytes();PAL.decode(cl)
    if BASE.sha(lvl)!=BASE.DATA_SHA256['VYLV.DAT']:raise ValueError('Original VYLV changed')
    for name,payload in [('VYLV.DAT',lvl),('VYGR.DAT',gr),('VYCL.DAT',cl)]:
        if payload!=(ROOT/'releases/stage_5c'/name).read_bytes():raise ValueError('Stable game DAT changed: '+name)
    sources=[f'stage5d1{s}.asm' for s in COMPONENTS]+['stage5d1_title.asm']
    with tempfile.TemporaryDirectory(prefix='vyper-5d1-') as d:
        w=Path(d);ti,title=TITLE.build(w)
        for name,payload in BASE.baseline_files().items():
            if name.startswith('vyper_original_animation_assets_v010/'):
                p=w/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
        shutil.copytree(ROOT/'assets/explosions',w/'explosion_assets');(w/'player_assets').mkdir()
        for name in PLAYER.PLAYER_FILES:shutil.copyfile(ROOT/'assets/player'/name,w/'player_assets'/name)
        for name in sources:shutil.copyfile(ROOT/'src/engine'/name,w/name)
        for name,payload in [('VYLV.DAT',lvl),('VYGR.DAT',gr),('VYCL.DAT',cl)]:(w/name).write_bytes(payload)
        run=subprocess.run(['java','-jar',str(jar),'stage5d1.asm','-o','STAGE5D1.PRG','-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(run.stdout,end='');run.check_returncode()
        prg=(w/'STAGE5D1.PRG').read_bytes()
        entries=[('STAGE5D1',prg,0x82),('VYTI.DAT',ti,0x81),('VYLV.DAT',lvl,0x81),('VYGR.DAT',gr,0x81),('VYCL.DAT',cl,0x81)]
        disk=bytearray(BASE.build_disk(entries));head=39*40*256;disk[head+4:head+20]=b'VYPER STAGE 5D1'.ljust(16,b'\xa0');disk=bytes(disk)
        files=BASE.verify_disk(disk,entries)
        report={'stage':'5d-1','issue':35,'stable':False,'baseline':'stage5c-stable','baseline_commit':subprocess.check_output(['git','rev-parse','stage5c-stable^{}'],cwd=ROOT).decode().strip(),'renderer':'stage5d0-stable','renderer_commit':subprocess.check_output(['git','rev-parse','stage5d0-stable^{}'],cwd=ROOT).decode().strip(),'protected_files':protected,'assembler':'KickAssembler5.25','files':files,'title':title,'gameplay':'Normalized Stage5c sources retained; only loader/title-exit hook/filename termination changed','xemu':'NOT_RUN; user acceptance required','handoff':'s3b.loading_complete -> restore video/palette/cursor -> save phase-shared bootstrap -> s3b.menu_or_game_start -> Level1'}
        out={'STAGE5D1.PRG':prg,'STAGE5D1.sym':(w/'stage5d1.sym').read_bytes(),'VYPER_STAGE5D1.d81':disk,'VYTI.DAT':ti,'VYLV.DAT':lvl,'VYGR.DAT':gr,'VYCL.DAT':cl,'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(run.stdout[run.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()}
        for name in sources+['title_layout.inc','conversion-report.json','title_screen.bin','title_fcm_unique.bin']:out[name]=(w/name).read_bytes()
        out['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {n}\n' for n,b in sorted(out.items())).encode()
        output.mkdir(parents=True,exist_ok=True)
        for n,b in out.items():(output/n).write_bytes(b)
    print('Both Stable baselines protected; original DATs, title pixels and D81 chains verified.')
    return report
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kickass',default=os.environ.get('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/stage_5d_1');a=p.parse_args()
    if not a.kickass:p.error('--kickass required')
    build(a.kickass,a.output)
if __name__=='__main__':main()
