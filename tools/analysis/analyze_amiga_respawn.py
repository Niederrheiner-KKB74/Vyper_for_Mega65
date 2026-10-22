#!/usr/bin/env python3
"""Stage10a4 bounded original evidence: player hit, respawn window, blink, fire latch, attack gate."""
import argparse,json
from pathlib import Path
from collections import Counter
import analyze_amiga_enemy_fire as B
BASE=0xc08760
RANGES=[('player_hit_starts_window',0xc09462,0xc094c0),('respawn_explosion_blink_end',0xc09590,0xc096a8),('fire_gate_and_release_latch',0xc0d08c,0xc0d130),('attack_selection_gate',0xc0d174,0xc0d194)]
def run(output):
 import capstone
 assert capstone.__version__=='5.0.7'
 source=B.ROOT/'assets/stage5b/original_sources';raw={n:(source/n).read_bytes() for n in B.HASHES}
 for n,data in raw.items():assert B.sha(data)==B.HASHES[n],n
 h=B.hunks(B.ofs_selected(raw['VYPER.ADF'])['Shot']['bytes']);code=h[0]['data'];ch=B.uss_chunks(raw['Vyper_Startscreen.uss'])
 copies=[]
 for ram,base in ((ch[b'BRAM']['data'],0xc00000),(raw['Vyper_Memory_Dump.dat'],0)):
  sig=bytes.fromhex('2f0a0c6c00062c1c670000b6');off=code.index(sig);start=ram.index(sig)-off;saved=ram[start:start+len(code)]
  bases={}
  for t in range(3):
   v=Counter((B.u32(saved,o)-B.u32(code,o))&0xffffffff for target,o in h[0]['relocations'] if target==t)
   if v:assert len(v)==1;bases[t]=next(iter(v))
  copies.append((saved,B.relocated(code,h[0]['relocations'],bases),base+start))
 md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_BIG_ENDIAN|capstone.CS_MODE_M68K_000);lines=[];ranges=[]
 for name,lo,hi in RANGES:
  a,b=lo-BASE,hi-BASE
  for saved,expected,_ in copies:assert saved[a:b]==expected[a:b],name
  ins=list(md.disasm(copies[0][0][a:b],lo));assert sum(i.size for i in ins)==hi-lo
  lines.append('\n; '+name+' (ADF relocations verified against BOTH saved runtime copies)\n')
  for i in ins:lines.append(f'{i.address:08X} dump:{copies[1][2]+i.address-BASE:06X} CODE+{i.address-BASE:04X} {i.bytes.hex():24} {i.mnemonic:10} {i.op_str}'.rstrip()+'\n')
  ranges.append({'name':name,'start':hex(lo),'end_exclusive':hex(hi),'verified_copies':2})
 output.mkdir(parents=True,exist_ok=True);(output/'68000-excerpts.txt').write_text(''.join(lines))
 (output/'evidence.json').write_text(json.dumps({'source_sha256':B.HASHES,'ranges':ranges,'scope':'Bounded disassembly of the respawn window ($2C4E=$114), blink toggle (timer%20, checked every 4 updates), fire gate/latch ($2C38) and attack gate. Updates per video frame not independently measured.'},indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=B.ROOT/'docs/stage10a4_amiga_evidence');run(p.parse_args().output)
