#!/usr/bin/env python3
"""Deterministic Stage6b1 test download, full release and rebuild instructions."""
import hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'releases/stage_6b1'
def package():
    paths=[p for p in OUT.iterdir() if p.is_file() and p.suffix!='.zip']
    paths += [ROOT/p for p in ['tools/build_stage6b1.py','tools/convert_stage6b1_menu.py','tools/package_stage6b1.py','tests/test_stage6b1.py','tests/test_stage6b1_rom.py','docs/stage6b1_menu_integration.md']]
    files={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
    files['README.txt']=b'Stage6b1 / Issue47. TEST BUILD, NOT Stable.\nMount releases/stage_6b1/VYPER_STAGE6B1.d81; LOAD"STAGE6B1",8 then RUN.\nOriginal title stays visible during loading, then the animated menu appears.\nJoystick2/cursors navigate; F1 starts selected level; F2/F3 placeholders; X exits.\nFull repository and protected stable assets/tags required for rebuild.\n'
    files['PACKAGE_SHA256SUMS.txt']=''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())).encode()
    dest=OUT/'VYPER_STAGE6B1.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(files.items()):
            i=zipfile.ZipInfo(n,(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=9)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for n,b in files.items():assert z.read(n)==b
    print(dest,len(files),'verified entries')
if __name__=='__main__':package()
