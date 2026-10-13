#!/usr/bin/env python3
"""Deterministic ZIP of the full-game Stage7a2 release, sources and reports."""
import hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'releases/stage_7a2'
def package():
    paths=[p for p in OUT.iterdir() if p.is_file() and p.suffix!='.zip' and p.name!='DELIVERY_SHA256SUMS.txt']
    paths += [ROOT/p for p in ['tools/build_stage7a2.py','tools/convert_stage7a2_stars.py',
        'tools/package_stage7a2.py','tests/test_stage7a2.py','docs/stage7a2_starfield_integration.md']]
    files={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
    files['README.txt']=(
        'Stage7a2 / Issue51. TEST BUILD, NOT Stable.\n'
        'Mount releases/stage_7a2/VYPER_STAGE7A2.d81; LOAD"STAGE7A2",8 then RUN.\n'
        'Original title/loader/menu first; F1 starts the full game with the accepted starfield.\n'
        'Joystick PORT2. Blue 1px/8 frames, red /4, yellow /2; accepted Stage7a1 parameters.\n'
        'No star test keys or profiler. X BASIC, R after GAME OVER, +/- levels.\n'
        'No XEMU test claimed; please confirm visual, LEVEL CLEAR/level continuity and BASIC/RUN tests.\n'
        'Full repository with original assets and protected stable tags required to rebuild.\n'
        'Build, measurements and test limits: docs/stage7a2_starfield_integration.md.\n'
    ).encode()
    files['PACKAGE_SHA256SUMS.txt']=''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())).encode()
    dest=OUT/'VYPER_STAGE7A2.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(files.items()):
            i=zipfile.ZipInfo(n,(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED
            i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=9)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for n,b in files.items():assert z.read(n)==b
    print(dest,len(files),'verified entries')
if __name__=='__main__':package()
