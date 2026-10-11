#!/usr/bin/env python3
"""Deterministic three-D81 bundle with generated sources and test documentation."""
import hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'releases/debut_y_geometry_test'
def package():
    names=[p.relative_to(ROOT) for p in OUT.rglob('*') if p.is_file() and p.suffix!='.zip']
    names += [Path(p) for p in ['src/tests/debut_y_geometry/y_geometry.asm','tools/build_debut_y_geometry.py','tools/analyze_debut_y_geometry.py','tools/package_debut_y_geometry.py','tests/test_debut_y_geometry.py','docs/debut_y_geometry_comparison.md']]
    files={str(p):(ROOT/p).read_bytes() for p in names}
    files['README.txt']=b'''Issue37: three independent Debut-Y tests; NONE Stable.
A: Y; B: Y-16; C: floor(Y*25/29). ENTRY only.
Each A/B/C directory contains a complete D81 with its PRG and all 3 game DATs.
Mount A/VYPER_Y_A.D81 (inside releases/debut_y_geometry_test/) and
LOAD "VYPER_Y_A",8 then RUN. B/C equivalent. + and - select levels.
German comparison tables and XEMU test: docs/debut_y_geometry_comparison.md.
Generated full ASM and symbols are included. For reproducible builds/tests,
use Git branch test-debut-y-geometry with stage5c-stable tag and original repo assets.
python tools/build_debut_y_geometry.py --variant all --kickass /path/to/KickAss.jar
No own XEMU/Amiga acceptance is claimed. User comparison is pending.
'''
    files['PACKAGE_SHA256SUMS.txt']=''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())).encode()
    dest=OUT/'VYPER_DEBUT_Y_ABC.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(files.items()):
            i=zipfile.ZipInfo(n,(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=9)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for n,b in files.items():assert z.read(n)==b,n
    print(dest,len(files),'verified entries')
if __name__=='__main__':package()
