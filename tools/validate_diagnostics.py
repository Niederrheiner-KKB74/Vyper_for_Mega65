#!/usr/bin/env python3
"""Build and independently reproduce the five archived diagnostic tools, then test."""
import argparse
import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from diagnostic_baseline import ROOT, HW2_BASE, protect, verify_archives

def hashes(folder):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.iterdir()) if p.is_file()}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kickass',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'build/diagnostics')
    args=parser.parse_args()
    output=protect(args.output);jar=args.kickass.resolve()
    results={}
    for suffix in ('','a','b','c','d'):
        stage='stage10b1'+suffix
        builder=importlib.import_module('build_'+stage)
        target=output/stage
        builder.build(jar,target)
        with tempfile.TemporaryDirectory(prefix='diagnostic-rebuild-') as temp:
            second=Path(temp);builder.build(jar,second)
            if hashes(target)!=hashes(second):
                raise ValueError('Independent rebuild differs: '+stage)
        results[stage]={'reproducible':True,'files':hashes(target)}
    env=os.environ.copy()
    env['KICKASS_JAR']=str(jar);env['DIAGNOSTIC_BUILD_ROOT']=str(output)
    output.mkdir(parents=True,exist_ok=True)
    with (output/'host_tests.txt').open('w',encoding='utf-8') as log:
        subprocess.run([sys.executable,'-m','unittest','discover','-s','tools',
                        '-p','test_stage10b1*.py','-v'],cwd=ROOT,env=env,
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run([sys.executable,str(ROOT/'tools/analysis/analyze_stage10b1b_hardware.py'),
                    '--output',str(output/'hardware_comparison')],cwd=ROOT,env=env,check=True)
    report={'main_base':HW2_BASE,'method':'Regular source assembly, independent rebuilds and CPU/parser tests',
            'preserved_archive_files':verify_archives(),'builds':results,
            'host_tests':'passed; see host_tests.txt','new_hardware_or_xemu_run':False}
    (output/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Five diagnostic builds reproduced; host tests and archived hardware analysis passed.')

if __name__=='__main__':main()
