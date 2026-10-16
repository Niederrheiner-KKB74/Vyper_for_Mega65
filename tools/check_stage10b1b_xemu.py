#!/usr/bin/env python3
"""Controlled supplemental headless test; requires documented local ~key patch.
Not a real-hardware, exact-release, visual or raster-timing acceptance test.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
from check_stage10a1_xemu import Monitor,labels
sys.path.insert(0,str(Path(__file__).parent/'analysis'))
from compare_stage10b1b import parse,compare,configuration,disk_file

def run(a):
 n=labels(a.artifacts/'stage10b1b.sym');s=json.loads((a.artifacts/'registers.json').read_text());m=Monitor(a.socket)
 report={'kind':'supplemental local XEMU controlled-state test','local_xemu_commit':'40dfef0d1d5f56be2469492715c12bdb32c75b67','patch':'tools/diagnostics/stage10a1_xemu_trace.patch','ROM':'V920413 PAL80x25','hardware':'NOT_RUN','exact_target_xemu_release':'NOT_RUN','visual_acceptance':'NOT_RUN','timing':'UART pauses invalidate raster/wall timing claims','D81_sha256':hashlib.sha256((a.artifacts/'VYPER_STAGE10B1B.d81').read_bytes()).hexdigest(),'scenes':[]}
 a.output.mkdir(parents=True,exist_ok=True)
 def paused(label):return m.wait(lambda r:r['pc']==n[label]+(3 if label=='main' else 1),timeout=90)
 def key(k,stop='main'):
  m.cmd(f'b {n[stop]:x}');m.cmd(f'~key{k:02x}');m.cmd('t0');paused(stop)
  if stop=='main':m.cmd('t0');paused(stop)
 def snapshot(bank):
  data=b''.join(m.read(seg['address'],seg['length']) for seg in s['buffers']['PRE' if bank==5 else 'POST']);obj=parse(data,s);c=configuration(obj,s);assert c['profile_E_constant_checks_pass'],c;return data,obj
 def actual_palette():
  saved=m.read(0xffd3070,1)[0];out=bytearray()
  for bank in range(4):
   m.write(0xffd3070,bytes([(saved&63)|(bank<<6)]));out+=m.read(0xffd3100,768)
  m.write(0xffd3070,bytes([saved]));return bytes(out)
 def live():return {r['name']:(actual_palette() if r['name']=='palettes' else m.read(r['address'],r['length'])) for r in s['regions']}
 m.cmd(f'b {n["main"]:x}');m.cmd('~key0d');m.cmd('t0');paused('main')
 for index,scene in enumerate('ABCD'):
  if index:key(0x31+index)
  provisional,obj=snapshot(5);assert obj['scene']==scene and obj['phase']=='PRE'
  assert m.read(0xe000,4800)==(a.artifacts/f'scene_{scene}_screen.bin').read_bytes(),('screen',scene)
  assert m.read(0xff80000,4800)==(a.artifacts/f'scene_{scene}_colour.bin').read_bytes(),('colour',scene)
  before=live();key(0x45)
  assert m.read(n['pending_post'],1)==b'\1'
  pre,p=snapshot(5);post,q=snapshot(4);assert (p['phase'],q['phase'])==('PRE','POST')
  assert p['sequence']==q['sequence']==index+1
  for region in p['regions']:
   if region['name']!='write_shadows':assert region['data']==before[region['name']],('PRE actual',scene,region['name'])
  after=live()
  for region in q['regions']:assert region['data']==after[region['name']],('POST actual',scene,region['name'])
  cmp=compare(p,q,s,require_pair=True)
  assert cmp['non_annotation_different_bytes']==0,cmp['memory_comparison']
  assert disk_file(a.disk.read_bytes(),f'V1B{scene}X.PRE')==pre
  try:disk_file(a.disk.read_bytes(),f'V1B{scene}X.PST')
  except ValueError:pass
  else:raise AssertionError('POST serialized before explicit S/photo pause')
  (a.output/f'V1B{scene}X.PRE').write_bytes(pre);(a.output/f'V1B{scene}X.PST').write_bytes(post)
  (a.output/f'{scene}_PRE_POST.json').write_text(json.dumps(cmp,indent=2)+'\n')
  key(0x53);assert m.read(n['pending_post'],1)==b'\0'
  assert snapshot(4)[0]==post,'S overwrote frozen POST'
  assert disk_file(a.disk.read_bytes(),f'V1B{scene}X.PST')==post
  assert hashlib.sha256(m.read(0x92c0,64)).hexdigest()==s['markers']['phase']['END'],'S must distinguish END from photographed PST'
  report['scenes'].append({'scene':scene,'configuration_and_isolation':True,'PRE_and_POST_CRC_valid':True,'actual_RAM_regions_verified':len(q['regions']),'all4_palette_banks_verified':True,'PRE_disk_exact_match':True,'POST_not_written_before_S':True,'POST_disk_exact_match_after_S':True,'frozen_POST_unchanged_by_S':True,'unexpected_non_annotation_memory_bytes':0,'unexpected_stable_register_differences':cmp['unexpected_stable_register_differences']})
 key(0x58,'exit_restored')
 assert m.read(0xff80000,32768)==m.read(0x40000,32768),'full colour restore'
 initial=m.read(n['initial_vic'],128)
 assert m.read(0xffd3051,1)[0]&0xc0==initial[0x51]&0xc0
 assert m.read(0xffd301a,1)[0]&31==initial[0x1a]&31
 for bank in range(4):
  m.write(0xffd3070,bytes([bank<<6]));assert m.read(0xffd3100,768)==m.read(0x6000+768*bank,768),'full palette restore'
 m.write(0xffd3070,bytes([initial[0x70]]))
 report['restore']='Colour32768Bytes, palette3072Bytes, D051 controls and IRQ mask verified before BASIC resumes'
 m.cmd(f'b {n["main"]:x}');m.cmd('t0');time.sleep(.25);m.basic_key(b'RUN\r');m.cmd('t0');paused('main');snapshot(5)
 report['repeated_RUN']=True
 # Force a missing-device PRE export in emulator RAM only, not the shipped PRG.
 m.write(n['export_device']+1,b'\x1f');key(0x45);m.write(n['export_device']+1,b'\x08')
 error,obj=snapshot(4);assert obj['measured_export_error']!=0
 assert m.read(n['pending_post'],1)==b'\1'
 assert hashlib.sha256(m.read(0x92c0,64)).hexdigest()==s['markers']['phase']['ERR']
 key(0x53);assert m.read(n['pending_post'],1)==b'\0';key(0x58,'exit_restored')
 report['export_failure']='Missing device31 reported in frozen POST with ERR marker; S serialization and X remain functional'
 (a.output/'runtime.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--socket',required=True);p.add_argument('--disk',type=Path,required=True);p.add_argument('--artifacts',type=Path,default=Path('releases/stage_10b1b'));p.add_argument('--output',type=Path,default=Path('docs/diagnostics/stage10b1b'));a=p.parse_args();run(a)
