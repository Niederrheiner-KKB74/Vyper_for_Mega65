#!/usr/bin/env python3
"""Deterministic ZIP of the full-game Stage7b5a release, sources and reports."""
import hashlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'releases/stage_7b5a'
def package():
    paths=[p for p in OUT.iterdir() if p.is_file() and p.suffix!='.zip' and p.name!='DELIVERY_SHA256SUMS.txt']
    paths += [ROOT/p for p in ['tools/build_stage7b5a.py','tools/convert_stage7a2_stars.py',
        'tools/measure_stage7b5a_events.py','tools/convert_stage7b5a_fire.py','tools/analyze_stage7b2_projectiles.py','tools/package_stage7b5a.py','tests/test_stage7b5a.py','docs/stage7b5a_original_fire_events.md']]
    paths += [ROOT/'docs/amiga_enemy_fire_analysis.md',ROOT/'docs/amiga_vs_stage7b4_fire_comparison.md',ROOT/'assets/amiga_enemy_fire_level_parameters.csv',ROOT/'tools/analysis/analyze_amiga_enemy_fire.py',ROOT/'tools/analysis/requirements.txt']
    paths += [p for p in (ROOT/'assets/stage7b2').rglob('*') if p.is_file()]
    files={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
    files['README.txt']=(
        'Stage7b5a / Issue63. TEST BUILD, NOT Stable.\n'
        'Mount releases/stage_7b5a/VYPER_STAGE7B5A.d81; LOAD"STAGE7B5A",8 then RUN.\n'
        'Original title/loader/menu first; F1 starts the full game; Original3x7 shots, player red tip up/enemy down; 2 player+6 enemy projectiles, no owner quota;30-frame attack cadence; LEVEL CLEAR fire starts transition.\n'
        'Joystick PORT2. Blue 1px/8 frames, red /4, yellow /2; accepted Stage7a1 parameters.\n'
        'No star test keys or profiler. X BASIC, R after GAME OVER, +/- levels.\n'
        'No XEMU test claimed; please confirm original event timing in levels1/3/29/54, six-shot cap and BASIC/RUN tests.\n'
        'Full repository with original assets and protected stable tags required to rebuild.\n'
        'Build, measurements and test limits: docs/stage7b5a_original_fire_events.md.\n'
    ).encode()
    files['PACKAGE_SHA256SUMS.txt']=''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())).encode()
    dest=OUT/'VYPER_STAGE7B5A.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(files.items()):
            i=zipfile.ZipInfo(n,(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED
            i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=9)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for n,b in files.items():assert z.read(n)==b
    (OUT/'DELIVERY_SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='DELIVERY_SHA256SUMS.txt'))
    print(dest,len(files),'verified entries')
if __name__=='__main__':package()
