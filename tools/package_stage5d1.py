#!/usr/bin/env python3
"""Deterministic Stage5d1 test bundle, with complete source/assets/build tools."""
import hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'releases/stage_5d_1'
def main():
    names=set()
    for folder in ['src','tools','tests','assets']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:names.add(p.relative_to(ROOT))
    for p in RELEASE.iterdir():
        if p.is_file() and p.suffix!='.zip':names.add(p.relative_to(ROOT))
    for name in ['AGENTS.md','docs/stage5d1_title_loader_integration.md','docs/stage5d1-test-results.json','docs/memory_map.md','docs/project_status.md','releases/stage_2ja_stable/Stage_2ja_STABLE_ARCHIVE.zip']:
        names.add(Path(name))
    files={str(p):(ROOT/p).read_bytes() for p in sorted(names)}
    files['README_STAGE5D1.txt']=b'''Vyper Stage 5d-1 / Issue #35 - title during SEQ loading. NOT Stable.
Mount releases/stage_5d_1/VYPER_STAGE5D1.d81 in PAL XEMU / ROM V920395.
LOAD "STAGE5D1",8 then RUN. Title first, then automatic Level 1.
X returns to BASIC. Test DIRECTORY and repeated RUN.
German documentation: docs/stage5d1_title_loader_integration.md.
Complete engine sources, originals, converters and build tools are included.
For reproducible baseline protection and inherited regression, use the repository
branch stage5d-1 with tags stage5c-stable and stage5d0-stable fetched.
python -m pip install -r tools/stage5d0-requirements.txt
python tools/build_stage5d1.py --kickass /path/to/KickAss.jar
No own XEMU/hardware success is claimed; user acceptance is pending.
'''
    files['PACKAGE_SHA256SUMS.txt']=''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())).encode()
    dest=RELEASE/'VYPER_STAGE5D1_test.zip'
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            i=zipfile.ZipInfo(name,(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,data,compresslevel=9)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for name,data in files.items():assert z.read(name)==data,name
    print(dest,dest.stat().st_size,'bytes;',len(files),'verified entries')
if __name__=='__main__':main()
