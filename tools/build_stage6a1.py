#!/usr/bin/env python3
"""Reproducible isolated animated-menu build; never change Stable artifacts."""
import argparse,json,os,subprocess,tempfile,shutil
from pathlib import Path
import build_stage3b1 as BASE
import convert_stage6a1_menu as CONVERT
ROOT=Path(__file__).resolve().parents[1]
TAG='stage5d1a-stable'
PIN='39890c0095fab55b2ea71f95cccf59a3419848c6'
def protect_stable():
    if subprocess.check_output(['git','rev-parse',TAG+'^{}'],cwd=ROOT,text=True).strip()!=PIN:raise ValueError('Unexpected Stage5d1a Stable')
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',TAG,'--','src/engine','releases/stage_5d_1_b2'],cwd=ROOT,text=True).splitlines()
    for n in names:
        if (ROOT/n).read_bytes()!=subprocess.check_output(['git','show',TAG+':'+n],cwd=ROOT):raise ValueError('Stable changed: '+n)
    return len(names)
def build(jar,output):
    jar=Path(jar).resolve();output=Path(output).resolve()
    if output.is_relative_to(ROOT/'releases') and not output.is_relative_to(ROOT/'releases/stage_6a1'):raise ValueError('Protected release destination')
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256:raise ValueError('Pinned KickAssembler5.25 required')
    protected=protect_stable()
    with tempfile.TemporaryDirectory(prefix='vyper-6a1-') as d:
        w=Path(d);conversion=CONVERT.convert(w)
        for n in ['stage6a1.asm','stage6a1_animation.asm']:shutil.copyfile(ROOT/'src/tests'/n,w/n)
        run=subprocess.run(['java','-jar',str(jar),'stage6a1.asm','-o','STAGE6A1.PRG','-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);print(run.stdout);run.check_returncode()
        prg=(w/'STAGE6A1.PRG').read_bytes();data=(w/'VYMN.DAT').read_bytes();entries=[('STAGE6A1',prg,0x82),('VYMN.DAT',data,0x81)]
        disk=bytearray(BASE.build_disk(entries));h=39*40*256;disk[h+4:h+20]=b'VYPER MENU 6A1'.ljust(16,b'\xa0');disk=bytes(disk);files=BASE.verify_disk(disk,entries)
        out={p.name:p.read_bytes() for p in w.iterdir() if p.is_file() and p.suffix in ['.asm','.inc','.bin','.DAT','.json','.png']}
        out.update({'STAGE6A1.PRG':prg,'STAGE6A1.sym':(w/'stage6a1.sym').read_bytes(),'VYPER_STAGE6A1.d81':disk,'memory-map.txt':(run.stdout[run.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()})
        report={'stage':'6a1','issue':43,'stable':False,'baseline':TAG,'baseline_commit':PIN,'protected_files':protected,'files':files,'conversion':conversion,'animation':'PAL50Hz frame gate; original per-actor 1..6-frame periods/countdowns; adjustable global divider; no Amiga runtime trace','xemu':'NOT_RUN; user acceptance pending'}
        out['build-report.json']=(json.dumps(report,indent=2)+'\n').encode();out['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {n}\n' for n,b in sorted(out.items())).encode()
        output.mkdir(parents=True,exist_ok=True)
        for n,b in out.items():(output/n).write_bytes(b)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kickass',default=os.environ.get('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/stage_6a1');a=p.parse_args()
    if not a.kickass:p.error('--kickass required')
    build(a.kickass,a.output)
