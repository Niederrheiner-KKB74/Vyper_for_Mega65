#!/usr/bin/env python3
"""Issue65: crossmatch selected player/timing/projectile instructions in three originals."""
import argparse,json
from pathlib import Path
from collections import Counter
import analyze_amiga_enemy_fire as BASE
RANGES=[('player_controls',0xc0d728,0xc0d764),('player_initialization',0xc0b5d0,0xc0b5e8),('sprite_coordinate_encoding',0xc0d56e,0xc0d5c8),('projectile_update',0xc0d5c8,0xc0d612),('projectile_spawn',0xc0d612,0xc0d6d6),('active_and_alternate_player_calls',0xc09708,0xc09758),('pre_sync_LoadView_and_raster_wait',0xc0944a,0xc09462),('loop_back',0xc09934,0xc09938),('library_stub_target',0xc119e8,0xc119f6),('update_counter',0xc0d08c,0xc0d0aa)]
def analyze(out):
 import capstone
 assert capstone.__version__=='5.0.7'
 source=BASE.ROOT/'assets/stage5b/original_sources';raw={n:(source/n).read_bytes() for n in BASE.HASHES}
 assert {n:BASE.sha(b) for n,b in raw.items()}==BASE.HASHES
 hs=BASE.hunks(BASE.ofs_selected(raw['VYPER.ADF'])['Shot']['bytes']);h=hs[0];chunks=BASE.uss_chunks(raw['Vyper_Startscreen.uss']);sources={}
 for name,saved,start,base in [('USS',chunks[b'BRAM']['data'],0x8760,0xc08760),('dump',raw['Vyper_Memory_Dump.dat'],0x21b20,0x21b20)]:
  image=saved[start:start+len(h['data'])];bases={}
  for t in range(3):
   vals=Counter((BASE.u32(image,o)-BASE.u32(h['data'],o))&0xffffffff for target,o in h['relocations'] if target==t)
   if vals:assert len(vals)==1;bases[t]=next(iter(vals))
  sources[name]={'image':image,'expected':BASE.relocated(h['data'],h['relocations'],bases),'base':base,'bases':bases}
 stub_evidence=[]
 for name,src in sources.items():
  ram=chunks[b'CRAM']['data'] if name=='USS' else raw['Vyper_Memory_Dump.dat']
  data=BASE.relocated(hs[1]['data'],hs[1]['relocations'],src['bases']);address=src['bases'][1]+0x5a
  assert ram[address:address+6]==data[0x5a:0x60]
  assert data[0x5a:0x5c]==b'\x4e\xf9' and BASE.u32(data,0x5c)==src['base']+0xc119e8-0xc08760
  stub_evidence.append({'source':name,'address':address,'DATA_offset':0x5a,'bytes':data[0x5a:0x60].hex()})
 md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_BIG_ENDIAN|capstone.CS_MODE_M68K_000);spans=[];text=[]
 for name,lo,hi in RANGES:
  a,b=lo-0xc08760,hi-0xc08760
  for s in sources.values():assert s['image'][a:b]==s['expected'][a:b],name
  rows=list(md.disasm(sources['USS']['image'][a:b],lo));assert sum(i.size for i in rows)==b-a,name
  text.append(f'\n; {name}: CODE+${a:04X}, Shot file+${h["file_offset"]+a:04X}; both runtime copies match relocated ADF\n')
  inst=[]
  for i in rows:
   o=i.address-0xc08760;d=0x21b20+o;f=h['file_offset']+o
   text.append(f'{i.address:08X} / {d:06X} / CODE+{o:04X} / FILE+{f:04X}  {i.bytes.hex():<22} {i.mnemonic:<9} {i.op_str}\n')
   inst.append({'USS':i.address,'dump':d,'CODE_offset':o,'Shot_offset':f,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str})
  spans.append({'name':name,'start':lo,'end_exclusive':hi,'instructions':inst,'both_runtime_copies_match_ADF':True})
 # Direct aligned JSRs; explicitly distinguish the two alternative paths.
 calls=[];code=sources['USS']['image']
 for o in range(0,len(code)-6,2):
  if code[o:o+2]==b'\x4e\xb9' and BASE.u32(code,o+2)==0xc0d728:calls.append(0xc08760+o)
  if code[o:o+2]==b'\x4e\xba' and 0xc08760+o+2+int.from_bytes(code[o+2:o+4],'big',signed=True)==0xc0d728:calls.append(0xc08760+o)
 assert calls==[0xc09726,0xc0974c],calls
 report={'issue':65,'source_sha256':BASE.HASHES,'disassembler':'Capstone5.0.7','library_stubs':stub_evidence,'player_calls':calls,'spans':spans,'player_step_per_call':2,'player_coordinate_format':'direct WORD low-resolution pixels; HPOS LSB retained','native_calls_per_PAL_frame':None,'limitations':['No active gameplay trace; menu USS is not timing evidence.','Eight-bit VHPOSR gate accepts PAL lines0 and256.','Pre-gate library trampoline uses LVO -222 (graphics LoadView), not WaitTOF -270.','2px/50Hz engine frame is an adjustable test default, not a proven original effective speed.']}
 out.mkdir(parents=True,exist_ok=True);(out/'evidence.json').write_text(json.dumps(report,indent=2)+'\n');(out/'68000-excerpts.txt').write_text('\n'.join(line.rstrip() for line in ''.join(text).splitlines())+'\n');print('Verified',len(spans),'spans; player calls:',list(map(hex,calls)))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=BASE.ROOT/'docs/stage7b5b_motion_evidence');analyze(p.parse_args().output)
