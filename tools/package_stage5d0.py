#!/usr/bin/env python3
"""Deterministic download ZIP: title disk, full ASM, tools, originals and reports."""
import hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'releases/stage_5d0'
def main():
    names=[p.relative_to(ROOT) for p in RELEASE.iterdir() if p.is_file() and p.suffix!='.zip']
    names += [Path(p) for p in ['src/tests/stage5d0.asm','tools/build_stage5d0.py','tools/build_stage3b1.py','tools/convert_stage5d0_title.py','tools/analyze_stage5d0_copper.py','tools/package_stage5d0.py','tools/stage5d0-requirements.txt','tests/test_stage5d0.py','docs/stage5d0_title_test.md','docs/stage5d0_title_preanalysis.md','docs/stage5d0-copper-report.json','docs/stage5d0-test-results.json','assets/stage5d0/original_sources/vyper_palette_candidate_9a50.png','assets/stage5d0/original_sources/vyper_title_palette.txt','assets/stage5b/original_sources/Vyper_Memory_Dump.dat','assets/stage5b/original_sources/Vyper_Startscreen.uss']]
    files={str(p):(ROOT/p).read_bytes() for p in names}
    files['README_STAGE5D0.txt']=b'''Vyper Stage 5d-0 / Issue #33 - isolated original-title test, NOT Stable.
PAL / ROM V920395 / BASIC 80x25. Mount releases/stage_5d0/VYPER_STAGE5D0.d81.
LOAD "STAGE5D0",8 then RUN. X/x returns to BASIC. Test DIRECTORY and RUN again.
Full details: docs/stage5d0_title_test.md (German).
Source and assets are included. Rebuild from the GitHub stage5d-title-test branch
with stage5c-stable fetched: build script protects that baseline using Git.
python tools/build_stage5d0.py --kickass /path/to/KickAss.jar
No own XEMU/hardware or executed Amiga-Copper trace is claimed.
'''
    files['PACKAGE_SHA256SUMS.txt']=''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())).encode()
    dest=RELEASE/'VYPER_STAGE5D0_test.zip'
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data,compresslevel=9)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for name,data in files.items():assert z.read(name)==data,name
    print(str(dest),dest.stat().st_size,'bytes; all packaged payloads verified.')
if __name__=='__main__':main()
