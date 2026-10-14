#!/usr/bin/env python3
"""Deterministic test delivery; all release files plus source/build/test/analysis evidence."""
import hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'releases/stage_7b5b'
def package():
 paths=[p for p in OUT.iterdir() if p.is_file() and p.suffix!='.zip' and p.name!='DELIVERY_SHA256SUMS.txt']
 paths += [ROOT/p for p in ('tools/build_stage7b5b.py','tools/package_stage7b5b.py','tools/analysis/analyze_stage7b5b_motion.py','tools/analysis/analyze_amiga_enemy_fire.py','tools/analysis/requirements.txt','tools/convert_stage7b5a_fire.py','tests/test_stage7b5b.py','docs/stage7b5b_player_and_projectile_motion.md')]
 paths+=list((ROOT/'docs/stage7b5b_motion_evidence').glob('*'))
 files={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
 files['README.txt']=b'Stage7b5b / Issue65. TEST, NOT Stable.\nMount VYPER_STAGE7B5B.d81, LOAD"STAGE7B5B",8 then RUN. Joystick PORT2.\nF1 starts game. Player default2px/50Hzframe is adjustable TEST value, not proven native effective speed.\nOriginal per-update enemy motion; see docs/stage7b5b_player_and_projectile_motion.md.\nFull repository with protected Git references and original inputs required to rebuild.\nXEMU acceptance pending.\n'
 files['PACKAGE_SHA256SUMS.txt']=''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())).encode()
 dest=OUT/'VYPER_STAGE7B5B.zip'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,b in sorted(files.items()):
   i=zipfile.ZipInfo(n,(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=9)
 with zipfile.ZipFile(dest) as z:
  assert z.testzip() is None
  for n,b in files.items():assert z.read(n)==b
 (OUT/'DELIVERY_SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='DELIVERY_SHA256SUMS.txt'))
 print(dest,len(files),'verified entries')
if __name__=='__main__':package()
