"""Regression tests for the actual repaired parser, cleanup opcodes and build guards."""
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from py65.devices.mpu6502 import MPU
from check_stage10a1_xemu import labels
from diagnostic_baseline import ROOT, protect, verify_archives
sys.path.insert(0,str(ROOT/'tools/analysis'))
from compare_stage10b1_registers import parse,compare

ART=Path(os.getenv('DIAGNOSTIC_BUILD_ROOT',str(ROOT/'build/diagnostics')))

def cleanup(stage, entry='io_cleanup', opened=0, close_error=False, dos_error=False):
    folder=ART/stage;memory=[0]*65536
    prg=(folder/(stage.upper()+'.PRG')).read_bytes()
    address=int.from_bytes(prg[:2],'little');memory[address:address+len(prg)-2]=prg[2:]
    names=labels(folder/(stage+'.sym'))
    memory[names['file_open']]=opened;memory[names['dos_open']]=0
    memory[names['io_status']]=0
    if 'profile' in names:memory[names['profile']]=ord('A' if stage!='stage10b1' else 'S')
    cpu=MPU(memory=memory,pc=names[entry]);cpu.sp=0xfd
    memory[0x1fe:0x200]=[0xff,0x0f]
    closes=[];lfn=0
    for _ in range(10000):
        if cpu.pc==0x1000:return closes,memory,names
        if cpu.pc==names['scratch_output']:
            cpu.p&=~1;cpu.pc=cpu.stPopWord()+1
        elif cpu.pc>=0xff00:
            pc=cpu.pc
            if pc==0xffba:lfn=cpu.a
            if pc==0xffc3:closes.append((cpu.a,bool(cpu.p&1)))
            error=(pc==0xffc0 and (lfn==2 or dos_error)) or (pc==0xffc3 and cpu.a==2 and close_error)
            cpu.p=(cpu.p|1) if error else (cpu.p&~1)
            if pc==0xffcf:cpu.a=ord('0')
            if pc==0xffb7:cpu.a=0;cpu.FlagsNZ(0)
            cpu.pc=cpu.stPopWord()+1
        else:cpu.step()
    raise AssertionError('Cleanup did not return')

class Consolidation(unittest.TestCase):
    def test_phase_start_timing_survives_without_register_differences(self):
        schema=json.loads((ART/'stage10b1/registers.json').read_text(encoding='utf-8'))
        original=(ROOT/'docs/diagnostics/stage10b1/V10BSX.DAT').read_bytes()
        for phase in range(4):
            for byte in (2,3):
                with self.subTest(phase=phase,byte=byte):
                    changed=bytearray(original);changed[32+phase*schema['block_size']+byte]^=1
                    changed[28:30]=b'\0\0';struct.pack_into('<H',changed,28,sum(changed)&65535)
                    left=parse(original,schema);right=parse(changed,schema)
                    report=compare(left,right,schema)
                    self.assertEqual(report['differences'],[])
                    self.assertIsNone(report['first_stable_divergence_phase'])
                    self.assertEqual(len(report['phase_context_differences']),1)
                    self.assertEqual(report['phase_context_differences'][0]['phase'],phase+1)
                    self.assertEqual(left['phase_context'][phase]['D012'],original[32+phase*schema['block_size']+2])

    def test_failed_open_does_not_close_foreign_lfn2(self):
        for stage in ('stage10b1','stage10b1a','stage10b1b'):
            for dos_error in (False,True):
                with self.subTest(stage=stage,dos_error=dos_error):
                    closes,m,n=cleanup(stage,entry='write_file',dos_error=dos_error)
                    self.assertNotIn(2,[lfn for lfn,_ in closes])
                    self.assertEqual(m[n['file_open']],0)
                    self.assertEqual(m[n['io_status']],2 if dos_error else 1)
                    self.assertEqual(closes,[] if dos_error else [(15,True)])

    def test_owned_close_success_error_and_status_channel_failure(self):
        for stage in ('stage10b1','stage10b1a','stage10b1b'):
            for close_error in (False,True):
                for dos_error in (False,True):
                    with self.subTest(stage=stage,close_error=close_error,dos_error=dos_error):
                        closes,m,n=cleanup(stage,opened=1,close_error=close_error,dos_error=dos_error)
                        self.assertEqual(closes,[(2,False)]+([] if dos_error else [(15,True)]))
                        self.assertEqual(m[n['file_open']],0)
                        self.assertEqual(m[n['io_status']],2 if dos_error else int(close_error))

    def test_archived_evidence_and_releases_match_original_blobs(self):
        self.assertGreater(verify_archives(),200)

    def test_archive_guard_rejects_modified_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);subprocess.run(['git','init','-q',str(root)],check=True)
            folder=root/'docs/diagnostic_consolidation';folder.mkdir(parents=True)
            sample=root/'docs/original.DAT';sample.write_bytes(b'original evidence\0')
            sha=subprocess.check_output(['git','hash-object','docs/original.DAT'],cwd=root,text=True).strip()
            (folder/'sources.json').write_text(json.dumps({'files':[{'path':'docs/original.DAT','blob_sha':sha}]}))
            self.assertEqual(verify_archives(root),1)
            sample.write_bytes(b'changed evidence\0')
            with self.assertRaisesRegex(ValueError,'Archived diagnostic evidence changed'):
                verify_archives(root)

    def test_output_cannot_overwrite_archives_or_repository_sources(self):
        for path in ('releases/stage_10b1','docs/diagnostics','src','tools','.'):
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'output'):
                protect(ROOT/path)

    def test_baseline_guard_needs_no_topic_branch_and_detects_edits_and_deletion(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'src').mkdir();source=root/'src/protected.asm';source.write_text('original\n')
            subprocess.run(['git','init','-q',str(root)],check=True)
            subprocess.run(['git','add','.'],cwd=root,check=True)
            subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid',
                            'commit','-qm','main baseline'],cwd=root,check=True)
            baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
            folder=root/'docs/diagnostic_consolidation';folder.mkdir(parents=True)
            (folder/'sources.json').write_text('{"files":[]}')
            self.assertEqual(protect(root/'build',root,baseline),root/'build')
            source.write_text('changed\n')
            with self.assertRaisesRegex(ValueError,'Protected HW2'):protect(root/'build',root,baseline)
            source.unlink()
            with self.assertRaisesRegex(ValueError,'Protected HW2'):protect(root/'build',root,baseline)

if __name__=='__main__':unittest.main()
