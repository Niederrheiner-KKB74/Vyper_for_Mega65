#!/usr/bin/env python3
"""Issue37: three independent Stage5c-derived ENTRY presentation tests."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as BASE
import build_stage3b3 as PLAYER
import build_stage5c as GAME
ROOT=Path(__file__).resolve().parents[1]
TAG='stage5c-stable'
PINNED_BASELINE='2997719d704095afc630830435cb2d2f76b7f696'
SOURCES=[f'stage5c{s}.asm' for s in GAME.COMPONENTS]+['stage5c_palettes.asm']
def original(name):return subprocess.check_output(['git','show',TAG+':'+name],cwd=ROOT)
def source_set():
    sources={n:original('src/engine/'+n) for n in SOURCES}
    # Only three fixed-entrypoint hooks. Preserve all original origins.
    n='stage5c_entry.asm';s=sources[n].decode()
    for old,new in [('e_init:\n','e_init:\n    jsr ygeometry.clear\n'),('e_objects:\n','e_objects:\n    jsr ygeometry.restore\n'),('    jmp attack.a_postframe','    jmp ygeometry.postframe')]:
        assert s.count(old)==1,old
        s=s.replace(old,new,1)
    # e_init/e_objects grow by six bytes in this segment; no neighbouring origin changes.
    sources[n]=s.encode()
    sources['stage5c.asm']+=b'\n.import source "y_geometry.asm"\n'
    sources['y_geometry.asm']=(ROOT/'src/tests/debut_y_geometry/y_geometry.asm').read_bytes()
    return sources
def build(variant,jar,output):
    assert variant in 'ABC' and len(variant)==1
    jar=Path(jar).resolve();output=Path(output).resolve()
    if output.is_relative_to(ROOT/'releases') and not output.is_relative_to(ROOT/'releases/debut_y_geometry_test'):raise ValueError('Protected release destination')
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256:raise ValueError('KickAssembler5.25 required')
    for n in SOURCES:
        if (ROOT/'src/engine'/n).read_bytes()!=original('src/engine/'+n):raise ValueError('Stage5c source modified: '+n)
    if subprocess.check_output(['git','rev-parse',TAG+'^{}'],cwd=ROOT,text=True).strip()!=PINNED_BASELINE:raise ValueError('Unexpected Stage5c Stable commit')
    PLAYER.verify_player_assets()
    sources=source_set();sources['variant.inc']=f'.const TEST_VARIANT={"ABC".index(variant)+1}\n'.encode()
    dats={n:original('releases/stage_5c/'+n) for n in ['VYLV.DAT','VYGR.DAT','VYCL.DAT']}
    with tempfile.TemporaryDirectory(prefix='debut-y-') as d:
        w=Path(d)
        for n,b in BASE.baseline_files().items():
            if n.startswith('vyper_original_animation_assets_v010/'):
                p=w/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        shutil.copytree(ROOT/'assets/explosions',w/'explosion_assets');(w/'player_assets').mkdir()
        for n in PLAYER.PLAYER_FILES:shutil.copyfile(ROOT/'assets/player'/n,w/'player_assets'/n)
        for n,b in sources.items():(w/n).write_bytes(b)
        for n,b in dats.items():(w/n).write_bytes(b)
        run=subprocess.run(['java','-jar',str(jar),'stage5c.asm','-o',f'VYPER_Y_{variant}.PRG','-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(run.stdout);run.check_returncode();prg=(w/f'VYPER_Y_{variant}.PRG').read_bytes()
        entries=[(f'VYPER_Y_{variant}',prg,0x82)]+[(n,b,0x81) for n,b in dats.items()]
        disk=bytearray(BASE.build_disk(entries));header=39*40*256;disk[header+4:header+20]=f'VYPER Y TEST {variant}'.encode().ljust(16,b'\xa0');disk=bytes(disk);checked=BASE.verify_disk(disk,entries)
        out={f'VYPER_Y_{variant}.PRG':prg,f'VYPER_Y_{variant}.D81':disk,f'VYPER_Y_{variant}.sym':(w/'stage5c.sym').read_bytes(),**dats,**sources,'memory-map.txt':(run.stdout[run.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()}
        report={'issue':37,'variant':variant,'stable':False,'baseline':TAG,'baseline_commit':subprocess.check_output(['git','rev-parse',TAG+'^{}'],cwd=ROOT,text=True).strip(),'files':checked,'transform':{'A':'Y','B':'Y-16','C':'floor(Y*25/29)'}[variant],'xemu':'NOT_RUN; user comparison pending'}
        out['build-report.json']=(json.dumps(report,indent=2)+'\n').encode()
        out['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {n}\n' for n,b in sorted(out.items())).encode()
        output.mkdir(parents=True,exist_ok=True)
        for n,b in out.items():(output/n).write_bytes(b)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--variant',choices=['A','B','C','all'],default='all');p.add_argument('--kickass',default=os.environ.get('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/debut_y_geometry_test');a=p.parse_args()
    if not a.kickass:p.error('--kickass required')
    for v in 'ABC' if a.variant=='all' else a.variant:build(v,a.kickass,a.output/v)
