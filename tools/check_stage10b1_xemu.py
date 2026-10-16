#!/usr/bin/env python3
"""Supplemental headless test ONLY; requires the documented ~key XEMU patch.
UART pauses invalidate timing/visual comparisons. Never use on real hardware.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
from check_stage10a1_xemu import Monitor,labels
sys.path.insert(0,str(Path(__file__).parent/'analysis'))
from compare_stage10b1_registers import parse,geometry,disk_file,compare

def run(a):
 n=labels(a.artifacts/'stage10b1.sym');schema=json.loads((a.artifacts/'registers.json').read_text())
 m=Monitor(a.socket);report={'type':'supplemental headless controlled XEMU run','hardware':'NOT_RUN',
 'requested_xemu_release':'20260129235930 NOT available locally; user comparison required',
 'local_xemu_commit':'40dfef0d1d5f56be2469492715c12bdb32c75b67',
 'patch':'tools/diagnostics/stage10a1_xemu_trace.patch (fake keyboard, headless SDL, trace)',
 'ROM':'V920413 PAL80x25','D81_sha256':hashlib.sha256((a.artifacts/'VYPER_STAGE10B1.d81').read_bytes()).hexdigest(),
 'limits':'No real-hardware, exact-release, visual, physical-input or raster-timing acceptance claim', 'cases':[]}
 a.output.mkdir(parents=True,exist_ok=True)
 def paused(label):return m.wait(lambda r:r['pc']==n[label]+(3 if label=='main' else 1),timeout=60)
 def key(k,stop='main'):
  m.cmd(f'b {n[stop]:x}');m.cmd(f'~key{k:02x}');m.cmd('t0');r=paused(stop)
  if stop=='main':
   m.cmd('t0');r=paused(stop) # first breakpoint is AFTER LDA D610, before dispatch
  return r
 m.cmd(f'b {n["main"]:x}');m.cmd('~key0d');m.cmd('t0');paused('main')
 for profile,button,filename in [('S',None,'V10BSX.DAT'),('E',0x32,'V10BEX.DAT')]:
  if button:key(button)
  data=m.read(0x4800,schema['dump_size']);dump=parse(data,schema);assert dump['profile']==profile
  assert m.read(0xe000,4800)==(a.artifacts/'scene_screen.bin').read_bytes()
  assert m.read(0xff80000,4800)==(a.artifacts/'scene_colour.bin').read_bytes()
  atlas=(a.artifacts/'grid_atlas.bin').read_bytes();expected=bytearray()
  for y in range(25):
   for x in range(15):
    flags=(1 if x==0 else 0)|(2 if x==14 else 0)|(4 if y==0 else 0)|(8 if y==24 else 0)
    expected+=atlas[flags*64:flags*64+64]
  assert m.read(0x18000,24000)==expected,'grid DMA copy mismatch'
  r=dump['phases'][3];assert r[0xd058]==192 and r[0xd059]==0 and r[0xd05e]==96
  assert r[0xd031]&128 and r[0xd05a]==60 and r[0xd015]==3
  x0=r[0xd04c]+256*(r[0xd04d]&15);y0=r[0xd04e]+256*(r[0xd04f]&15)
  for spr,(x,y) in enumerate([(112,112),(232,64)]):
   sx=r[0xd000+2*spr]+256*((r[0xd010]>>spr)&1)+512*((r[0xd05f]>>spr)&1)
   sy=r[0xd001+2*spr]+256*((r[0xd077]>>spr)&1)+512*((r[0xd078]>>spr)&1)
   assert (sx,sy)==(x0+2*x-3,y0+2*y),(sx,sy)
  key(0x45);assert m.read(n['io_status'],1)==b'\0',m.read(n['dos_code'],2)
  exported=m.read(0x4800,schema['dump_size']);parse(exported,schema)
  on_disk=disk_file(a.disk.read_bytes(),filename);assert exported==on_disk,'SEQ bytes differ from RAM'
  (a.output/filename).write_bytes(on_disk)
  report['cases'].append({'profile':profile,'four_snapshots':True,'screen_colour_grid_DMA_verified':True,
   'sprite_coordinates_verified':True,'SEQ_exact_RAM_match':True,'DOS_status':'00','geometry':geometry(r)})
 # Restore before PLP/RTS; BASIC IRQ/cursor cannot change the saved colour RAM yet.
 key(0x58,'exit_restored')
 assert m.read(0xff80000,32768)==m.read(0x40000,32768),'colour RAM restore'
 initial=m.read(n['initial_vic'],128)
 for bank in range(4):
  m.write(0xffd3070,bytes([bank<<6]))
  assert m.read(0xffd3100,768)==m.read(0x6000+bank*768,768),'palette restore'
 m.write(0xffd3070,bytes([initial[0x70]]))
 report['cases'].append({'exit_before_RTS':'full32768 colour RAM and4x768 palette bytes restored'})
 m.cmd(f'b {n["main"]:x}');m.cmd('t0');time.sleep(.25)
 m.basic_key(b'RUN\r');m.cmd('t0');paused('main')
 parse(m.read(0x4800,schema['dump_size']),schema)
 report['cases'].append({'repeated_RUN':'returned to diagnostic main with valid new dump'})
 key(0x45)
 assert m.read(n['io_status'],1)==b'\0','repeated export must replace diagnostic file'
 report['cases'].append({'repeated_export_status':m.read(n['io_status'],1).hex(),'DOS':m.read(n['dos_code'],2).decode('ascii')})
 # Force a real KERNAL OPEN on unavailable device31 in emulator RAM only.
 # It must report failure, redraw the scene and still process native X.
 m.write(n['export_device']+1,b'\x1f');key(0x45)
 assert m.read(n['io_status'],1)!=b'\0','unavailable-device export incorrectly reports success'
 m.write(n['export_device']+1,b'\x08')
 assert m.read(0xffd3020,1)[0]&15==2,'failed export must set red border'
 key(0x58,'exit_restored')
 report['cases'].append({'export_failure':'controlled missing device31; red error, main live, X restoration reached'})
 left=parse((a.output/'V10BSX.DAT').read_bytes(),schema);right=parse((a.output/'V10BEX.DAT').read_bytes(),schema)
 (a.output/'profile_comparison.json').write_text(json.dumps(compare(left,right,schema),indent=2)+'\n')
 (a.output/'runtime.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--socket',required=True);p.add_argument('--disk',type=Path,required=True);p.add_argument('--artifacts',type=Path,default=Path('releases/stage_10b1'));p.add_argument('--output',type=Path,default=Path('docs/diagnostics/stage10b1'));a=p.parse_args();run(a)
