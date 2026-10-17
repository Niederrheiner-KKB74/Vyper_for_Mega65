#!/usr/bin/env python3
"""Supplemental local XEMU RAM/control test; no hardware/visual/timing acceptance claim."""
import argparse,hashlib,json,sys,time
from pathlib import Path
from check_stage10a1_xemu import Monitor,labels
sys.path.insert(0,str(Path(__file__).parent/'analysis'))
from inspect_stage10b1c import parse

def run(a):
 m=Monitor(a.socket);n=labels(a.artifacts/'stage10b1c.sym');s=json.loads((a.artifacts/'scene.json').read_text());a.output.mkdir(parents=True,exist_ok=True)
 def paused(label='main'):return m.wait(lambda r:r['pc']==n[label]+(3 if label=='main' else 1),timeout=60)
 def key(k,stop='main'):
  m.cmd(f'b {n[stop]:x}');m.cmd(f'~key{k:02x}');m.cmd('t0');paused(stop)
  if stop=='main':m.cmd('t0');paused(stop)
 def sample(tag):
  raw=m.read(0x4800,s['snapshot_size']);p=parse(raw,s);assert p['configuration_valid'],p['errors'];(a.output/f'{tag}.REG').write_bytes(raw);(a.output/f'{tag}.json').write_text(json.dumps(p,indent=2)+'\n');return p
 def actual_palette():
  saved=m.read(0xffd3070,1)[0];out=bytearray()
  for bank in range(4):m.write(0xffd3070,bytes([bank<<6]));out+=m.read(0xffd3100,768)
  m.write(0xffd3070,bytes([saved]));return bytes(out)
 m.cmd(f'b {n["main"]:x}');m.cmd('~key0d');m.cmd('t0');paused()
 results=[];palette=None
 for tag,k,mode in [('A_initial',None,'A'),('B',0x32,'B'),('A_returned',0x31,'A'),('B_repeated',0x32,'B'),('B_rebuilt',0x52,'B'),('B_sample_only',0x44,'B')]:
  if k:key(k)
  obj=sample(tag);assert obj['mode']==mode
  screen=m.read(0xe000,2400);assert screen==(a.artifacts/f'scene_{mode}_screen.bin').read_bytes()
  assert m.read(0xff80000,2400)==(a.artifacts/'scene_colour.bin').read_bytes()
  assert m.read(0xe960,96)==bytes(96) and m.read(0xff80960,96)==bytes(96)
  assert m.read(0x9040,128)==(a.artifacts/'player_ncm.bin').read_bytes()
  assert m.read(0x4000,2048)==(a.artifacts/'font.bin').read_bytes()
  current=actual_palette()
  if palette is None:palette=current
  else:assert current==palette
  atlas=(a.artifacts/'grid_atlas.bin').read_bytes();grid=b''.join(atlas[((1 if x==0 else 0)|(2 if x==14 else 0)|(4 if y==0 else 0)|(8 if y==24 else 0))*64:((1 if x==0 else 0)|(2 if x==14 else 0)|(4 if y==0 else 0)|(8 if y==24 else 0))*64+64] for y in range(25) for x in range(15))
  assert m.read(0x18000,24000)==grid
  results.append({'case':tag,'mode':mode,'rebuild_sequence':obj['rebuild_sequence'],'register_config_valid':True,'screen_colour_extra_row_font_original_pixie_grid_exact':True,'all_palette_banks_unchanged':True,'sprite_coordinates':obj['sprites'][:2]})
 key(0x58,'exit_restored');initial=m.read(n['initial_vic'],128)
 assert m.read(0xff80000,32768)==m.read(0x40000,32768)
 for bank in range(4):m.write(0xffd3070,bytes([bank<<6]));assert m.read(0xffd3100,768)==m.read(0x6000+bank*768,768)
 m.write(0xffd3070,bytes([initial[0x70]]))
 for addr in [0x31,0x54,0x5a,0x58,0x5e,0x79,0x7a]:assert m.read(0xffd3000+addr,1)[0]==initial[addr],hex(addr)
 assert m.read(0xffd3051,1)[0]&0xc0==initial[0x51]&0xc0
 assert m.read(0xffd301a,1)[0]&31==initial[0x1a]&31
 m.cmd(f'b {n["main"]:x}');m.cmd('t0');time.sleep(.25);m.basic_key(b'RUN\r');m.cmd('t0');paused();obj=sample('after_RUN');assert obj['mode']=='A' and obj['rebuild_sequence']==1
 key(0x58,'exit_restored')
 m.cmd('b 0');m.cmd('t0');time.sleep(.25);m.basic_key(b'DIRECTORY\r')
 def directory_ready(r):
  if r['pc']<0xe000 or m.read(0xd0,1)!=b'\0':return False
  raw=m.read(0x800,2000)
  text=''.join(chr((v&127)+64 if (v&127)<32 else v&127) for v in raw)
  return 'VYPER 10B1C TEST' in text
 m.wait(directory_ready)
 raw=m.read(0x800,2000);directory_text=''.join(chr((v&127)+64 if (v&127)<32 else v&127) for v in raw)
 assert 'DEVICE NOT PRESENT' not in directory_text
 report={'kind':'supplemental local headless XEMU RAM/control regression','local_xemu_commit':'40dfef0d1d5f56be2469492715c12bdb32c75b67','local_patch':'tools/diagnostics/stage10a1_xemu_trace.patch (~key monitor input)','ROM':'V920413 PAL80x25','D81_sha256':hashlib.sha256((a.artifacts/'VYPER_STAGE10B1C.d81').read_bytes()).hexdigest(),'cases':results,'restore':'full Colour32768, palette3072, mode/geometry/D051 controls/IRQmask verified before BASIC resumes','repeated_RUN':True,'BASIC_DIRECTORY':directory_text,'hardware':'NOT_RUN','exact_target_xemu_release':'NOT_RUN','visual_acceptance':'NOT_RUN','timing':'UART pauses invalidate wall/raster timing claims; no fabricated cycle measurements'}
 (a.output/'runtime.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--socket',required=True);p.add_argument('--artifacts',type=Path,default=Path('releases/stage_10b1c'));p.add_argument('--output',type=Path,default=Path('docs/diagnostics/stage10b1c'));run(p.parse_args())
