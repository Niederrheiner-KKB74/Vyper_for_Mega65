#!/usr/bin/env python3
"""Standalone Stage8a2. Requires Python3, Java and checksum-pinned KickAssembler5.25."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as D
import extract_stage8a2_samples as EX
ROOT=D.ROOT
BASE='b56ae48b3bac92d40885ef78530a72eb882df16b'
def protect():
 for p in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--','src','assets','releases','tools'],cwd=ROOT,text=True).splitlines():
  if (ROOT/p).read_bytes()!=subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT):raise ValueError('Protected baseline changed: '+p)
def build(jar,out):
 jar=Path(jar).resolve();out=Path(out).resolve();protect()
 if D.sha(jar.read_bytes())!=D.KICKASS_SHA256:raise ValueError('KickAssembler hash')
 if out.is_relative_to(ROOT/'releases') and not out.is_relative_to(ROOT/'releases/stage_8a2'):raise ValueError('Protected release')
 with tempfile.TemporaryDirectory(prefix='stage8a2-') as t:
  w=Path(t);meta=EX.extract(w);shutil.copyfile(ROOT/'src/tests/stage8a2.asm',w/'stage8a2.asm')
  proc=subprocess.run(['java','-jar',str(jar),'stage8a2.asm','-o','STAGE8A2.PRG','-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);print(proc.stdout);proc.check_returncode()
  prg=(w/'STAGE8A2.PRG').read_bytes();entries=[('STAGE8A2',prg,0x82),('VYAU.DAT',(w/'VYAU.DAT').read_bytes(),0x81)]
  disk=bytearray(D.build_disk(entries));h=39*40*256;disk[h+4:h+20]=b'VYPER STAGE8A2'.ljust(16,b'\xa0');disk=bytes(disk);files=D.verify_disk(disk,entries)
  report=dict(stage='8a2',issue=71,stable=False,baseline=BASE,archive=meta,files=files,xemu='NOT_RUN',hardware='PENDING',buffer_bytes_per_source=4096,half_bytes=2048)
  result={'STAGE8A2.PRG':prg,'VYPER_STAGE8A2.d81':disk,'STAGE8A2.sym':(w/'stage8a2.sym').read_bytes(),'stage8a2.asm':(w/'stage8a2.asm').read_bytes(),'samples.inc':(w/'samples.inc').read_bytes(),'archive.inc':(w/'archive.inc').read_bytes(),'samples.json':(w/'samples.json').read_bytes(),'samples.csv':(w/'samples.csv').read_bytes(),'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(proc.stdout[proc.stdout.index('Memory Map'):].split('Writing Symbol file')[0].strip()+'\n').encode()}
  result['SHA256SUMS.txt']=''.join(f'{D.sha(b)}  {n}\n' for n,b in sorted(result.items())).encode();out.mkdir(parents=True,exist_ok=True)
  for n,b in result.items():(out/n).write_bytes(b)
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kickass',default=os.getenv('KICKASS_JAR'),required=not os.getenv('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/stage_8a2');a=p.parse_args();build(a.kickass,a.output)
