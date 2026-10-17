#!/usr/bin/env python3
"""Standalone Issue96 audio CURRENT-latch test, no productive source edits."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
import build_stage3b1 as D
import extract_stage8a1_sample as EX
ROOT=Path(__file__).resolve().parents[1]
BASE='fd6214c1c6be1adcedea095b0ebd474288a83403'
def build(jar,out):
 if hashlib.sha256(jar.read_bytes()).hexdigest()!=D.KICKASS_SHA256:raise ValueError('Expected pinned KickAssembler5.25')
 for p in subprocess.check_output(['git','diff',BASE,'--name-only','--','src','assets','releases','tools'],cwd=ROOT,text=True).splitlines():
  if subprocess.run(['git','cat-file','-e',BASE+':'+p],cwd=ROOT,stderr=subprocess.DEVNULL).returncode==0:raise ValueError('Protected baseline changed: '+p)
 out=out.resolve()
 if out.is_relative_to(ROOT/'releases') and not out.is_relative_to(ROOT/'releases/stage_10b1d'):raise ValueError('Protected output path')
 with tempfile.TemporaryDirectory(prefix='stage10b1d-') as t:
  w=Path(t);meta=EX.extract(w);shutil.copyfile(ROOT/'src/tests/stage10b1d.asm',w/'stage10b1d.asm')
  run=subprocess.run(['java','-jar',str(jar),'stage10b1d.asm','-o','STAGE10B1D.PRG','-symbolfile','-showmem'],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (w/'assembly.txt').write_text('\n'.join(x.rstrip() for x in run.stdout.replace(str(w),'.').splitlines())+'\n')
  if run.returncode:raise RuntimeError(run.stdout)
  prg=(w/'STAGE10B1D.PRG').read_bytes();entries=[('STAGE10B1D',prg,0x82)];disk=bytearray(D.build_disk(entries));disk[39*40*256+4:39*40*256+20]=b'VYPER 10B1D TEST'.ljust(16,b'\xa0');D.verify_disk(bytes(disk),entries);(w/'VYPER_STAGE10B1D.d81').write_bytes(disk)
  schema={'stage':'10b1d','base':BASE,'sample':meta,'target':0x16480,'end':0x17ec0,'sentinel':0x18020,'mailbox':0x1fd3,'A_order':[0xd72c,0xd72a,0xd72b],'B_order':[0xd72a,0xd72b,0xd72c],'volume':64,'control_start':0x82,'counter_increment':4127,'log_address':0x5000,'log_size':2080,'header_size':32,'record_size':32,'capacity':64,'phases':{'0':'BEFORE','1':'LATCHED','2':'AFTER_START','3':'DONE','4':'STOP','5':'D711_OBSERVATION','6':'TIMEOUT'},'errors':{'0':'OK','1':'sample CRC','2':'foreign active audio','3':'mixer/global init','4':'CURRENT pointer mismatch','5':'watchdog','6':'sentinel reset failed'},'hardware':'NOT_RUN','exact_target_xemu':'NOT_RUN','hearing':'NOT_RUN','stable':False}
  (w/'test.json').write_text(json.dumps(schema,indent=2)+'\n');out.mkdir(parents=True,exist_ok=True)
  files={p.name:p.read_bytes() for p in w.iterdir() if p.is_file()}
  for n,b in files.items():(out/n).write_bytes(b)
  (out/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())))
  print('Built',len(prg),'PRG bytes;',len(disk),'D81 bytes;',meta['sha256'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--kickass',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'releases/stage_10b1d');a=p.parse_args();build(a.kickass.resolve(),a.output)
