#!/usr/bin/env python3
"""Standalone Stage8a1; no game build/import. Python3, Java, pinned KickAssembler5.25."""
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as DISK
import extract_stage8a1_sample as SAMPLE
ROOT=DISK.ROOT
PROTECTED='8e81363d13ff0e22578db36d7bd7446ffdd5a127'
def protect():
 for p in subprocess.check_output(['git','ls-tree','-r','--name-only',PROTECTED,'--','src','assets','releases','tools'],cwd=ROOT,text=True).splitlines():
  f=ROOT/p
  if f.read_bytes()!=subprocess.check_output(['git','show',PROTECTED+':'+p],cwd=ROOT):raise ValueError('Protected existing file changed '+p)
def build(jar,out):
 jar=Path(jar).resolve();out=Path(out).resolve()
 if DISK.sha(jar.read_bytes())!=DISK.KICKASS_SHA256:raise ValueError('KickAssembler5.25 hash mismatch')
 if out.is_relative_to(ROOT/'releases') and not out.is_relative_to(ROOT/'releases/stage_8a1'):raise ValueError('Protected release target')
 protect()
 with tempfile.TemporaryDirectory(prefix='vyper-stage8a1-') as d:
  w=Path(d);meta=SAMPLE.extract(w)
  blob=(w/'sound17.s8').read_bytes()
  if len(blob)!=6720 or DISK.sha(blob)!=meta['sha256']:raise ValueError('Sample17 resource invalid')
  shutil.copyfile(ROOT/'src/tests/stage8a1.asm',w/'stage8a1.asm')
  proc=subprocess.run(['java','-jar',str(jar),'stage8a1.asm','-o','STAGE8A1.PRG','-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  print(proc.stdout);proc.check_returncode();prg=(w/'STAGE8A1.PRG').read_bytes()
  if prg[:2]!=b'\x01\x20' or prg[2+0x4000-0x2001:]!=blob:raise ValueError('Embedded PCM differs from original')
  entries=[('STAGE8A1',prg,0x82)];disk=bytearray(DISK.build_disk(entries));h=39*40*256;disk[h+4:h+20]=b'VYPER STAGE8A1'.ljust(16,b'\xa0');disk=bytes(disk);files=DISK.verify_disk(disk,entries)
  report={'stage':'8a1','issue':69,'stable':False,'standalone':True,'protected_game_commit':PROTECTED,'sample':meta,'sample_start':0x4000,'sample_end_exclusive':0x5a40,'format':'CTRL82 Signed8, NO LOOP, NO XOR; channel0 only','routing':'fixed mono L/R, no dynamic panning,25% channel volume','files':files,'xemu':'NOT_RUN; no configured SDL XEMU runtime','real_hardware':'USER_ACCEPTANCE_PENDING'}
  result={'STAGE8A1.PRG':prg,'VYPER_STAGE8A1.d81':disk,'STAGE8A1.sym':(w/'stage8a1.sym').read_bytes(),'stage8a1.asm':(w/'stage8a1.asm').read_bytes(),'sample17.inc':(w/'sample17.inc').read_bytes(),'sample17.json':(w/'sample17.json').read_bytes(),'build-report.json':(json.dumps(report,indent=2)+'\n').encode(),'memory-map.txt':(proc.stdout[proc.stdout.index('Memory Map'):].split('Writing Symbol file')[0].strip()+'\n').encode()}
  result['SHA256SUMS.txt']=''.join(f'{DISK.sha(b)}  {n}\n' for n,b in sorted(result.items())).encode()
  out.mkdir(parents=True,exist_ok=True)
  for n,b in result.items():(out/n).write_bytes(b)
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--kickass',default=os.getenv('KICKASS_JAR'),required=not os.getenv('KICKASS_JAR'));p.add_argument('--output',type=Path,default=ROOT/'releases/stage_8a1');a=p.parse_args();build(a.kickass,a.output)
