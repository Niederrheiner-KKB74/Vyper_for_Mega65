#!/usr/bin/env python3
"""Reproducible independent Stage 5d-0; protect confirmed Stage5c byte-for-byte."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as BASE
import convert_stage5d0_title as CONVERT
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/stage5d0/original_sources'
SOURCE_HASHES={'vyper_palette_candidate_9a50.png':'faa19d74583ec1a35f5ed81f1727f026e03a2de1fce9eb86dd73315ded484eea','vyper_title_palette.txt':'a108f6346556a15d6a6e2cb712fde23995eda05557f5d85c69cea5857c4e492e'}
def protect_stable():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only','stage5c-stable','--','src/engine','releases/stage_5c','assets/stage5c'],cwd=ROOT).decode().splitlines()
    checked=0
    for name in names:
        if not name.startswith(('releases/stage_5c/','assets/stage5c/')) and not Path(name).name.startswith('stage5c'):continue
        checked+=1
        if (ROOT/name).read_bytes()!=subprocess.check_output(['git','show','stage5c-stable:'+name],cwd=ROOT):raise ValueError('Stable changed: '+name)
    return checked
def build(jar,output):
    jar=Path(jar).resolve();output=Path(output).resolve()
    if output.is_relative_to(ROOT/'releases') and not output.is_relative_to(ROOT/'releases/stage_5d0'):raise ValueError('Cannot overwrite other releases')
    if BASE.sha(jar.read_bytes())!=BASE.KICKASS_SHA256:raise ValueError('Expected pinned KickAssembler5.25')
    protected=protect_stable()
    for name,sha in SOURCE_HASHES.items():
        if BASE.sha((SOURCE/name).read_bytes())!=sha:raise ValueError('Original input changed: '+name)
    with tempfile.TemporaryDirectory(prefix='vyper-5d0-') as d:
        work=Path(d)
        conversion=CONVERT.convert(SOURCE/'vyper_palette_candidate_9a50.png',SOURCE/'vyper_title_palette.txt',work)
        shutil.copyfile(ROOT/'src/tests/stage5d0.asm',work/'stage5d0.asm')
        run=subprocess.run(['java','-jar',str(jar),'stage5d0.asm','-o','STAGE5D0.PRG','-symbolfile','-showmem'],cwd=work,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(run.stdout,end='');run.check_returncode()
        prg=(work/'STAGE5D0.PRG').read_bytes();data=(work/'VYTI.DAT').read_bytes()
        entries=[('STAGE5D0',prg,0x82),('VYTI.DAT',data,0x81)]
        disk=bytearray(BASE.build_disk(entries));head=39*40*256;disk[head+4:head+20]=b'VYPER TITLE 5D0'.ljust(16,b'\xa0');disk=bytes(disk)
        files=BASE.verify_disk(disk,entries)
        report={'stage':'5d-0','issue':33,'stable':False,'baseline':'stage5c-stable','baseline_commit':subprocess.check_output(['git','rev-parse','stage5c-stable^{}'],cwd=ROOT).decode().strip(),'protected_paths_checked':protected,'assembler':'KickAssembler5.25','files':files,'conversion':conversion,'mode':'FCM CHR16/FCLRHI,44x30 cells,8x8,352x240 logical pixels;2x2 native PAL pixels','memory':{'code':'$2100-$2737 (see assembly map)','SEQ_buffers':'$6800-$69FF','screen':'$7000-$7A4F','colour':'$FF82000-$FF82A4F','colour_backup':'$15000-$15A4F','VYTI_load':'$40000-$54A74','aligned_FCM':'$40000-$549FF'},'xemu':'NOT_RUN; user acceptance required','Amiga_Copper':'Static saved-register/list analysis; active title execution not proven'}
        out={'STAGE5D0.PRG':prg,'STAGE5D0.sym':(work/'stage5d0.sym').read_bytes(),'VYPER_STAGE5D0.d81':disk,'VYTI.DAT':data,'stage5d0.asm':(work/'stage5d0.asm').read_bytes(),'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(run.stdout[run.stdout.index('Memory Map'):].split('Writing Symbol file')[0].rstrip()+'\n').encode()}
        for name in ['title_fcm.bin','title_palette_r.bin','title_palette_g.bin','title_palette_b.bin','conversion-report.json']:out[name]=(work/name).read_bytes()
        out['SHA256SUMS.txt']=''.join(f'{BASE.sha(b)}  {n}\n' for n,b in sorted(out.items())).encode()
        output.mkdir(parents=True,exist_ok=True)
        for name,b in out.items():(output/name).write_bytes(b)
    print('Verified original pixels/palette, protected Stable5c and both D81 file chains.')
    return report
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kickass',default=os.environ.get('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/stage_5d0');a=p.parse_args()
    if not a.kickass:p.error('--kickass required')
    build(a.kickass,a.output)
if __name__=='__main__':main()
