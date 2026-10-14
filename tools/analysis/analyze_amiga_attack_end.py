#!/usr/bin/env python3
"""Issue77: read-only original ATTACK expansion/runtime and Stage9a comparison.
Only JSON/CSV/text evidence; never assembles, writes DATs or edits an engine.
Capstone5.0.7 required. Times below are update indices, NOT measured PAL frames.
"""
import argparse,csv,io,json,struct,sys,subprocess
from collections import Counter
from pathlib import Path
import analyze_amiga_enemy_fire as B
sys.path.insert(0,str(B.ROOT/'tools'))
import analyze_attack_descriptors as L
ROOT=B.ROOT
BASE=0xc08760
STABLE='9bbe02ed9d284575c14c23954659a781d6889ee9'
RANGES=[('attack_buffer_allocation',0xc0a198,0xc0a1c6),('attack_file_offsets_to_pointers',0xc0cb42,0xc0cc6e),('attack_buffer_free',0xc0c4cc,0xc0c4f6),('level_pointer',0xc0a2ea,0xc0a300),('actor_formation_y_and_types',0xc0acd2,0xc0ad32),('attack_expansion',0xc0afa6,0xc0b1b4),('nibble_decoder',0xc0c3bc,0xc0c40e),('attack_launch',0xc0d174,0xc0d27e),('animation_hit_entry_return_attack_death',0xc0d2a8,0xc0d56e)]
SELECT={1,2,3,4,5,25,47,50,56,99,100}
def s16(v):return (v+32768)%65536-32768

def expand(curve,start_y,limit=350):
 """C0B03E..B1A4: cyclic byte index, cumulative signed WORDs, terminal Y overwrite."""
 x=0;y=start_y;points=[]
 for k in range(limit):
  dx,dy=L.decode(curve[k%len(curve)]);x=s16(x+dx);y=s16(y+dy)
  points.append((x,y))
  if y>=216:
   return points,[(a,-1 if i==len(points)-1 else b) for i,(a,b) in enumerate(points)]
 raise ValueError('Allocated350-point safety bound exceeded; original loop guard is late')

def runtime(points,anchor):
 out=[]
 for i,(x,y) in enumerate(points):
  raw=s16(anchor+x);xx=0 if raw<0 else 223 if raw>224 else raw
  out.append({'update':i+1,'x':xx,'y':0 if y<0 else y,'state':2 if y<0 else 3,'sentinel':y<0})
  if y<0:break
 return out

def port(curve,x,y):
 """Existing9a finite one-pass + phase5/DY2; no proposed correction executed."""
 out=[]
 for i,b in enumerate(curve):
  dx,dy=L.decode(b);x=s16(x+dx);y=s16(y+dy)
  out.append({'update':i+1,'x':x,'y':y,'phase':5 if i==len(curve)-1 else 4})
 for _ in range(400):
  if y<0 or y>=256 or y>=200:
   out.append({'update':len(out)+1,'x':x,'y':-16,'phase':2});return out
  y+=2;out.append({'update':len(out)+1,'x':x,'y':y,'phase':5})
 raise ValueError('Port simulation guard')

def write_csv(path,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def analyze(source,out):
 import capstone
 if capstone.__version__!='5.0.7':raise ValueError('Pinned capstone5.0.7 required')
 raw={n:(source/n).read_bytes() for n in B.HASHES}
 for n,b in raw.items():
  if B.sha(b)!=B.HASHES[n]:raise ValueError('Original hash mismatch '+n)
 fs=B.ofs_selected(raw['VYPER.ADF']);hs=B.hunks(fs['Shot']['bytes']);code=hs[0]['data'];chunks=B.uss_chunks(raw['Vyper_Startscreen.uss'])
 sig=bytes.fromhex('2f0a0c6c00062c1c670000b6');off=code.index(sig);sources={}
 for name,ram,mapbase in [('USS',chunks[b'BRAM']['data'],0xc00000),('dump',raw['Vyper_Memory_Dump.dat'],0)]:
  assert ram.count(sig)==1
  start=ram.index(sig)-off;saved=ram[start:start+len(code)];bases={}
  for t in range(3):
   vals=Counter((B.u32(saved,o)-B.u32(code,o))&0xffffffff for target,o in hs[0]['relocations'] if target==t)
   if vals:
    assert len(vals)==1;bases[t]=next(iter(vals))
  sources[name]={'base':mapbase+start,'bases':bases,'saved':saved,'relocated':B.relocated(code,hs[0]['relocations'],bases)}
 assert sources['USS']['base']==BASE and sources['dump']['base']==0x21b20
 md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_BIG_ENDIAN|capstone.CS_MODE_M68K_000)
 text=[];spans=[]
 for label,lo,hi in RANGES:
  a=lo-BASE;b=hi-BASE
  for src in sources.values():assert src['saved'][a:b]==src['relocated'][a:b],label
  ins=list(md.disasm(sources['USS']['saved'][a:b],lo));assert sum(i.size for i in ins)==hi-lo and not any(i.mnemonic in ('.byte','dc.w') for i in ins)
  text.append(f'\n;{label}: verified relocated ADF CODE against BOTH runtime copies\n')
  for i in ins:
   delta=i.address-BASE
   text.append(f'{i.address:08X} dump:{0x21b20+delta:06X} CODE+{delta:04X} Shot+{hs[0]["file_offset"]+delta:04X} USSfile+{chunks[b"BRAM"]["payload_offset"]+i.address-0xc00000:06X} {i.bytes.hex():24} {i.mnemonic:9} {i.op_str}'.rstrip()+'\n')
  spans.append({'name':label,'USS_start':lo,'USS_end_exclusive':hi,'CODE_start':a,'both_runtime_copies_match_relocated_ADF':True})
 # Pin semantics-critical opcode bytes, rather than accepting a merely decodable range.
 checks={0xc0b052:'3028005e',0xc0b05a:'6604',0xc0b05c:'426dfff6',0xc0b180:'0c7100d81800',0xc0b186:'6d00fe8a',0xc0b1a4:'33bcffff1800',0xc0d232:'216800700074',0xc0d4b2:'22680074',0xc0d4d6:'31590012',0xc0d4dc:'317c0002006e'}
 for addr,h in checks.items():assert sources['USS']['saved'][addr-BASE:addr-BASE+len(bytes.fromhex(h))].hex()==h
 level=fs['Level']['bytes'];attack=fs['Attack']['bytes'];form=fs['Forme']['bytes']
 records=list(L.parse((ROOT/'assets/VYLV.DAT').read_bytes()));cases=[];level4=[];trace=[];all_stats=[];negative=[]
 for number,interval,groups,enemies,curves in records:
  r=level[(number-1)*114:number*114];fo=B.u32(r,0x44);n=len(enemies);assert B.u16(r,0x66)==len(curves)
  assert form[fo:fo+4*n]==bytes(v for x,y,t,c in enemies for v in (x,y-16))+bytes(e[2] for e in enemies)+bytes(e[3] for e in enemies)
  for j,c in enumerate(curves):
   co=B.u32(r,0x4e+j*4);cl=B.u16(r,0x5e+j*2);assert cl==len(c) and attack[co:co+cl]==c
  per=[]
  for slot,(x,y,typ,ci) in enumerate(enemies):
   c=curves[ci];generated,stored=expand(c,y);actual=runtime(stored,x);p=port(c,x,y-min(e[1] for e in enemies))
   early=next((i+1 for i,(_,yy) in enumerate(stored[:-1]) if yy<0),None)
   if early:negative.append((number,slot,early))
   dx,dy=map(sum,zip(*(L.decode(b) for b in c)))
   row={'level':number,'slot':slot,'curve':ci,'Attack_file_offset':B.u32(r,0x4e+ci*4),'packed_bytes':len(c),'formation_x':x,'original_y':y,'port_start_y':y-min(e[1] for e in enemies),'net_dx':dx,'net_dy':dy,'original_generated_points':len(generated),'full_passes_before_terminal':(len(generated)-1)//len(c),'terminal_raw_x':generated[-1][0],'terminal_raw_y':generated[-1][1],'last_nonnegative_runtime_y':actual[-2]['y'] if len(actual)>1 else None,'runtime_exit_update':len(actual),'port_after_first_x':p[len(c)-1]['x'],'port_after_first_y':p[len(c)-1]['y'],'port_return_update':len(p)}
   per.append(row)
   if number in SELECT:cases.append(row)
   if number==4:
    level4.append(row)
    if slot in (0,1,4):
     for k in range(max(len(actual),len(p))):
      aa=actual[k] if k<len(actual) else {};pp=p[k] if k<len(p) else {}
      trace.append({'slot':slot,'update':k+1,'packed_index':k%len(c),'original_x':aa.get('x'),'original_y':aa.get('y'),'original_state':aa.get('state'),'port_x':pp.get('x'),'port_y':pp.get('y'),'port_phase':pp.get('phase')})
  all_stats.append({'level':number,'curve_lengths':[len(c) for c in curves],'actors':len(per),'min_points':min(x['original_generated_points'] for x in per),'max_points':max(x['original_generated_points'] for x in per),'actors_extending_past_first_pass':sum(x['original_generated_points']>x['packed_bytes'] for x in per)})
 assert sum(x['actors'] for x in all_stats)==2194 and len(records)==100
 assert len(records[3][4][0])==43 and tuple(map(sum,zip(*(L.decode(b) for b in records[3][4][0]))))==(2,38)
 stable_paths=subprocess.check_output(['git','ls-tree','-r','--name-only',STABLE,'--','src','assets','releases','tools'],cwd=ROOT,text=True).splitlines()
 assert all((ROOT/p).read_bytes()==subprocess.check_output(['git','show',STABLE+':'+p],cwd=ROOT) for p in stable_paths),'Stable modified'
 report={'issue':77,'analysis_only':True,'stable_base':STABLE,'source_sha256':B.HASHES,'VYLV_sha256':B.sha((ROOT/'assets/VYLV.DAT').read_bytes()),'Stage9a_attack_sha256':B.sha((ROOT/'src/engine/stage9a_attack.asm').read_bytes()),'files':{k:{'bytes':len(fs[k]['bytes']),'sha256':B.sha(fs[k]['bytes'])} for k in ('Shot','Level','Attack','Forme','Debut')},'code_sources':{k:{'base':v['base'],'hunk_bases':v['bases'],'whole_CODE_difference_bytes':sum(a!=b for a,b in zip(v['saved'],v['relocated']))} for k,v in sources.items()},'verified_spans':spans,'level4_packed_hex':records[3][4][0].hex(),'level4':level4,'all_100_levels':all_stats,'premature_negative_Y_cases':negative,'max_points':max(x['max_points'] for x in all_stats),'protected_existing_files':len(stable_paths),'limitations':['Static disassembly and arithmetic simulation, not WinUAE execution or measured50Hz frames.','Original terminal216 and port200 are different coordinate conventions.','Supplied start-screen USS plus separate ChipRAM only; no newly recorded level4 active trace.']}
 if any(out.resolve().is_relative_to(ROOT/d) for d in ('src','assets','releases')):raise ValueError('Protected output target')
 out.mkdir(parents=True,exist_ok=True)
 (out/'68000-excerpts.txt').write_text(''.join(text));(out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');write_csv(out/'cases.csv',cases);write_csv(out/'level4_trace.csv',trace)
 (out/'SHA256SUMS.txt').write_text(''.join(f'{B.sha(p.read_bytes())}  {p.name}\n' for p in sorted(out.iterdir()) if p.name!='SHA256SUMS.txt'))
 print(json.dumps({'levels':100,'actors':2194,'max_points':report['max_points'],'negative_Y_before_terminal':negative,'level4_slot0':level4[0],'stable_files_unchanged':len(stable_paths)},indent=2))
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=ROOT/'assets/stage5b/original_sources');p.add_argument('--output',type=Path,default=ROOT/'docs/amiga_attack_end_evidence');a=p.parse_args();analyze(a.source,a.output)
