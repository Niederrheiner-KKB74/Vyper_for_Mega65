#!/usr/bin/env python3
"""Deterministic standalone Stage6a2 visual test download package."""
import hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'releases/stage_6a2'
def package():
    paths=[p for p in OUT.iterdir() if p.is_file() and p.suffix!='.zip']
    paths += [ROOT/p for p in ['tools/build_stage6a2.py','tools/convert_stage6a1_menu.py','tools/analyze_stage6a2_cycling.py','tools/package_stage6a2.py','tests/test_stage6a2.py','docs/stage6a2_color_cycling.md']]
    files={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
    files['README.txt']=b'Stage6a2 / Issue45: independent original 320x200 menu, 32 animated types plus original COLOR02 cycling. NOT Stable.\nMount releases/stage_6a2/VYPER_STAGE6A2.d81. LOAD"STAGE6A2",8 then RUN. Only X exits; menu options do nothing.\nFull generated ASM and binary inputs are inside releases/stage_6a2/. Reproducible conversion/build/testing uses Git branch stage6a2 with original repository assets and Stable tags.\nSee docs/stage6a2_color_cycling.md for original evidence and XEMU acceptance.\n'
    files['PACKAGE_SHA256SUMS.txt']=''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())).encode()
    dest=OUT/'VYPER_STAGE6A2.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(files.items()):
            i=zipfile.ZipInfo(n,(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=9)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for n,b in files.items():assert z.read(n)==b
    print(dest,len(files),'verified entries')
if __name__=='__main__':package()
