#!/usr/bin/env python3
"""Deterministic Stage5d1a test download bundle; requires repository for rebuild."""
import hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'releases/stage_5d_1_b2'
def package():
    paths=[p for p in OUT.iterdir() if p.is_file() and p.suffix!='.zip']
    paths += [ROOT/p for p in ['tools/build_stage5d1a.py','tools/package_stage5d1a.py','tests/test_stage5d1a.py','tests/test_stage5d1a_entry.py','docs/stage5d1_b2_integration.md']]
    files={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
    files['README.txt']=b'Stage 5d-1a / Issue41. Integrated title-loader plus confirmed B2 ENTRY correction. NOT Stable.\nMount releases/stage_5d_1_b2/VYPER_STAGE5D1A.d81, LOAD"STAGE5D1A",8 then RUN.\nOriginal repository/tag assets are required to rebuild. See included technical documentation.\n'
    files['PACKAGE_SHA256SUMS.txt']=''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())).encode()
    dest=OUT/'VYPER_STAGE5D1A.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(files.items()):
            i=zipfile.ZipInfo(n,(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=9)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for n,b in files.items():assert z.read(n)==b
    print(dest,len(files),'verified entries')
if __name__=='__main__':package()
