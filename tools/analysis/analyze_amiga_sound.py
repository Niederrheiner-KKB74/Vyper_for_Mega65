#!/usr/bin/env python3
"""Issue67: read-only Amiga sound evidence/extraction. Never builds or edits an engine.

Default output is metadata/disassembly only. --samples-out exports original bytes
outside the repository; --wav adds explicitly clock-labelled, unpanned previews.
Requires the existing pinned Capstone5.0.7, otherwise only Python stdlib.
"""
import argparse,csv,io,json,struct,sys,wave
from pathlib import Path
from collections import Counter
import analyze_amiga_enemy_fire as BASE
ROOT=BASE.ROOT
sys.path.insert(0,str(ROOT/'tools'))
import analyze_attack_descriptors as LEVELS
import analyze_stage5d0_copper as COP
CODE_BASE=0xc08760
TYPE_OFFSET=0x2baa # actual18-byte record starts with graphics descriptor pointer
SOUND_OFFSET=0x20a
SKIP={4,13,14,23} #1-based sample IDs, not executable filenames
RANGES=[
 ('transition_cues_and_rectangle_phase',0xc08ef4,0xc0932a),
 ('mute_and_pause',0xc0936c,0xc09424),
 ('player_destruction',0xc09462,0xc09570),
 ('sound_initialization_caller',0xc09af6,0xc09b0a),
 ('copper_server_registration',0xc09cf2,0xc09d26),
 ('logical_pair_reset',0xc0a286,0xc0a2ea),
 ('enemy_type_sound_fields_and_graphics',0xc0a9b2,0xc0abd8),
 ('cleanup_caller',0xc0c40e,0xc0c438),
 ('conditional_copper_sound_tick',0xc0cff2,0xc0d07e),
 ('gameplay_tick_and_player_fire',0xc0d08c,0xc0d174),
 ('attack_selection_sound',0xc0d174,0xc0d27e),
 ('both_enemy_hit_sound_sites',0xc0d2de,0xc0d3e2),
 ('entry_sound',0xc0d3e2,0xc0d42a),
 ('enemy_projectile_sound_and_position_pointer',0xc0d612,0xc0d66c),
 ('sound_tick',0xc0d77e,0xc0d846),
 ('sample_loader_and_irq_initialization',0xc0e820,0xc0ea18),
 ('sound_teardown',0xc0ea66,0xc0eae8),
 ('two_audio_interrupt_callbacks',0xc0eae8,0xc0eb44),
 ('AddIntServer_bridge',0xc1180e,0xc1181e),
 ('AllocMem_bridge',0xc1184c,0xc11862),
 ('SetIntVector_bridge',0xc118dc,0xc118ec),
 ('WaitTOF_bridge',0xc11a74,0xc11a7e),
]

def ofs_inventory(adf):
 """Validate all directory/file headers; read data only for selected originals.

 The disk also contains an unrelated blank-name header with a bad data pointer.
 We do not silently relax checks or claim its data chain was validated.
 """
 if len(adf)!=901120 or adf[:4]!=b'DOS\0':raise ValueError('Expected original OFS disk')
 def block(n):
  if not 0<n<1760:raise ValueError('OFS block bound')
  b=adf[n*512:(n+1)*512]
  if sum(struct.unpack('>128I',b))&0xffffffff:raise ValueError(f'OFS checksum block{n}')
  return b
 entries={};seen=set()
 def walk(n,parent=''):
  if n in seen:raise ValueError('OFS header cycle')
  seen.add(n);b=block(n);w=struct.unpack('>128I',b);name=b[433:433+b[432]].decode('latin1');path=parent+'/'+name
  if w[127] in (1,2):
   for q in w[6:78]:
    chain=set()
    while q:
     if q in chain:raise ValueError('OFS hash chain cycle')
     chain.add(q);walk(q,path);q=BASE.u32(block(q),496)
  elif w[127]==0xfffffffd:
   if path in entries:raise ValueError('Duplicate OFS path')
   entries[path]={'path':path,'name':name,'header_block':n,'first_data':w[4],'bytes':w[81]}
 walk(880)
 def read(path):
  f=entries[path];data=bytearray();q=f['first_data'];seq=1;chain=set();blocks=[]
  while q:
   if q in chain:raise ValueError('OFS data cycle')
   chain.add(q);bb=block(q);v=struct.unpack('>6I',bb[:24])
   if v[0]!=8 or v[1]!=f['header_block'] or v[2]!=seq or v[3]>488:raise ValueError('OFS data sequence')
   data+=bb[24:24+v[3]];blocks.append(q);q=v[4];seq+=1
  if len(data)!=f['bytes']:raise ValueError('OFS file size')
  f['data_blocks']=blocks;f['sha256']=BASE.sha(data);return bytes(data)
 return entries,read

def csv_bytes(rows):
 b=io.StringIO(newline='');w=csv.DictWriter(b,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);return b.getvalue()
def s8(v):return v if v<128 else v-256

def analyze(source,output,samples_out=None,wav=False,paula_clock=3546895):
 import capstone
 if capstone.__version__!='5.0.7':raise ValueError('Capstone5.0.7 required')
 if wav and samples_out is None:raise ValueError('--wav requires --samples-out')
 if samples_out is not None and samples_out.resolve().is_relative_to(ROOT):raise ValueError('Export sample binaries outside repository')
 if paula_clock<=0:raise ValueError('Invalid Paula clock')
 raw={n:(source/n).read_bytes() for n in BASE.HASHES}
 for n,b in raw.items():
  if BASE.sha(b)!=BASE.HASHES[n]:raise ValueError('Original source changed: '+n)
 inventory,read=ofs_inventory(raw['VYPER.ADF'])
 selected=['/Vyper/Shot','/Vyper/vyper','/Vyper/a','/Vyper/sonquasar','/Vyper/s/startup-sequence','/Vyper/Wave/Forme']
 files={p:read(p) for p in selected}
 if files['/Vyper/s/startup-sequence'].splitlines()[2]!=b'shot':raise ValueError('Startup target changed')
 shot=files['/Vyper/Shot'];hs=BASE.hunks(shot);h=hs[0];data=hs[1]['data'];snd=files['/Vyper/sonquasar'];chunks=BASE.uss_chunks(raw['Vyper_Startscreen.uss'])
 sig=bytes.fromhex('2f0a0c6c00062c1c670000b6');off=h['data'].index(sig);sources={}
 for name,ram,map_base in [('USS',chunks[b'BRAM']['data'],0xc00000),('dump',raw['Vyper_Memory_Dump.dat'],0)]:
  if ram.count(sig)!=1:raise ValueError('Ambiguous CODE image')
  start=ram.index(sig)-off;saved=ram[start:start+len(h['data'])];bases={}
  for t in range(3):
   vals=Counter((BASE.u32(saved,o)-BASE.u32(h['data'],o))&0xffffffff for target,o in h['relocations'] if target==t)
   if vals:
    if len(vals)!=1:raise ValueError('Ambiguous relocation')
    bases[t]=next(iter(vals))
  sources[name]={'base':map_base+start,'bases':bases,'saved':saved,'expected':BASE.relocated(h['data'],h['relocations'],bases),'ram':chunks[b'CRAM']['data'] if name=='USS' else ram}
 if sources['USS']['base']!=CODE_BASE or sources['dump']['base']!=0x21b20:raise ValueError('Unexpected CODE mapping')
 md=capstone.Cs(capstone.CS_ARCH_M68K,capstone.CS_MODE_BIG_ENDIAN|capstone.CS_MODE_M68K_000)
 text=[];spans=[];verified_addresses=set()
 for name,lo,hi in RANGES:
  a,b=lo-CODE_BASE,hi-CODE_BASE
  for src in sources.values():
   if src['expected'][a:b]!=src['saved'][a:b]:raise ValueError('Runtime code mismatch '+name)
  ins=[]
  for i in md.disasm(sources['USS']['saved'][a:],lo):
   if i.address>=hi:break
   if i.address+i.size>hi:raise ValueError('Range cuts instruction '+name)
   ins.append(i)
  if sum(i.size for i in ins)!=b-a or any(i.mnemonic in ('dc.w','.byte') or 'invalid' in i.op_str or '$aaaa' in i.op_str for i in ins):raise ValueError('Not completely decoded '+name)
  text.append(f'\n; {name}: CODE+${a:04X}; Shot file+${h["file_offset"]+a:04X}; both saved copies match relocated ADF\n');rows=[]
  for i in ins:
   o=i.address-CODE_BASE;dump=sources['dump']['base']+o;fo=h['file_offset']+o
   text.append((f'{i.address:08X} / {dump:06X} / CODE+{o:04X} / FILE+{fo:04X}  {i.bytes.hex():<22} {i.mnemonic:<9} {i.op_str}').rstrip()+'\n')
   rows.append({'USS':i.address,'dump':dump,'CODE_offset':o,'Shot_offset':fo,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str});verified_addresses.add(i.address)
  spans.append({'name':name,'start':lo,'end_exclusive':hi,'both_runtime_copies_match_relocated_ADF':True,'instructions':rows})
 # Aligned one-instruction scan is candidate discovery, not a CFG/disassembly proof.
 candidates=[];calls=[];code=sources['USS']['saved']
 for p in range(0,len(code)-6,2):
  for i in md.disasm(code[p:p+12],CODE_BASE+p,count=1):
   if any(s in i.op_str for s in ('$dff0a','$dff0b','$dff0c','$dff0d','$dff096','$dff09a','$dff09c','$dff09e')):
    candidates.append({'USS':i.address,'CODE_offset':p,'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str,'in_verified_instruction_stream':i.address in verified_addresses})
   if i.mnemonic in ('jsr','bsr'):
    for name,target in [('tick',0xc0d77e),('init',0xc0e820),('reset',0xc0a286),('cleanup',0xc0ea66)]:
     if i.op_str.startswith(f'$'+format(target,'x')):calls.append({'routine':name,'target':target,'USS':i.address,'bytes':i.bytes.hex()})
 #24 descriptors, sample boundaries from the actual loader's sequential reads/seeks.
 sample_rows=[];offset=0;sample_data={}
 for i in range(24):
  p=SOUND_OFFSET+12*i;per,pan,length,hold,initial=struct.unpack_from('>HHHHI',data,p);n=length*2;blob=snd[offset:offset+n];sid=i+1
  if len(blob)!=n or per==0 or pan not in (4,6,8) or initial!=0:raise ValueError('Invalid original sound descriptor')
  ptrs={}
  for name,src in sources.items():
   addr=src['bases'][1]+p;saved=src['ram'][addr:addr+12]
   if saved[:8]!=data[p:p+8]:raise ValueError('Descriptor words mismatch')
   ptr=BASE.u32(saved,8);ptrs[name]=ptr
   if sid in SKIP:
    if ptr!=0:raise ValueError('Skipped sample loaded')
   elif ptr==0 or src['ram'][ptr:ptr+n]!=blob:raise ValueError('Sample differs from runtime RAM '+str(sid))
  signed=[s8(v) for v in blob];rate=paula_clock/per
  sample_rows.append({'sound_id':sid,'loaded':sid not in SKIP,'DATA_offset':p,'Shot_descriptor_offset':hs[1]['file_offset']+p,'sonquasar_offset':offset,'bytes':n,'Paula_LEN_words':length,'Paula_PER':per,'pan_divisor':pan,'busy_ticks':hold,'USS_pointer':ptrs['USS'],'dump_pointer':ptrs['dump'],'sample_sha256':BASE.sha(blob),'signed8_min':min(signed),'signed8_max':max(signed),'signed8_mean':round(sum(signed)/n,6),'PAL_assumed_rate_Hz':round(rate,6),'PAL_nominal_duration_s':round(n/rate,6),'MEGA65_40M5_rate_increment':round(rate*(1<<24)/40500000)})
  sample_data[sid]=blob;offset+=n
 if offset!=164836 or len(snd)!=164849:raise ValueError('Sound file coverage changed')
 #Real18-byte type record: framepointer,frames,delay,width,death,shot,entry,attack.
 types=[];existing=json.loads((ROOT/'assets/stage5b/vylv_vygr_mapping.json').read_text())
 for i in range(38):
  p=TYPE_OFFSET+18*i;fields=struct.unpack_from('>I7H',data,p);death,gun,entry,attack=fields[-4:]
  for name,src in sources.items():
   expected=BASE.relocated(data,hs[1]['relocations'],src['bases'])[p:p+18]
   if src['ram'][src['bases'][1]+p:src['bases'][1]+p+18]!=expected:raise ValueError('Type descriptor mismatch')
  ptr=BASE.u32(sources['dump']['ram'],sources['dump']['bases'][1]+p)
  if existing[i]['vylv_index']!=i or existing[i]['vygr_type_1based']!=i+1 or int(existing[i]['original_descriptor_address'][1:],16)!=ptr or existing[i]['frame_count']!=fields[1]:raise ValueError('Existing graphics mapping mismatch')
  if any(s in SKIP or not 1<=s<=24 for s in (death,gun,entry,attack)):raise ValueError('Invalid type sound ID')
  types.append({'vylv_index':i,'vygr_type_1based':i+1,'DATA_offset':p,'Shot_offset':hs[1]['file_offset']+p,'USS_record':sources['USS']['bases'][1]+p,'dump_record':sources['dump']['bases'][1]+p,'dump_frame_descriptor':ptr,'frames':fields[1],'destruction_sound':death,'shot_sound':gun,'entry_sound':entry,'attack_sound':attack,'evidence':'confirmed_code_and_both_runtime_tables'})
 # Independently match all2194 unchanged level type bytes to the original Forme.
 audit=[];used=set();forme=files['/Vyper/Wave/Forme']
 for number,interval,groups,enemies,attacks in LEVELS.parse((ROOT/'assets/VYLV.DAT').read_bytes()):
  original=bytes(v for x,y,t,a in enemies for v in (x,y-16))+bytes(t for x,y,t,a in enemies)+bytes(a for x,y,t,a in enemies);pos=forme.find(original)
  if pos<0:raise ValueError('Forme/VYLV mismatch')
  used.update(e[2] for e in enemies);audit.append({'level':number,'Forme_offset':pos,'enemies':len(enemies),'graphic_types':[e[2] for e in enemies]})
 if len(audit)!=100 or sum(x['enemies'] for x in audit)!=2194:raise ValueError('Level audit changed')
 # Saved Copper lists: active roots plus four previously bounded memory finds.
 copper=[];chip=chunks[b'CHIP']['data']
 for name,ram,addresses in [('USS',chunks[b'CRAM']['data'],[COP.be(chip,0x84,4),COP.be(chip,0x88,4)]),('dump',raw['Vyper_Memory_Dump.dat'],[0x1b5b4,0x1c4ec,0x2b38a,0x35496])]:
  for p in addresses:
   l=COP.copper(ram,p);moves=[e for e in l['instructions'] if 'register' in e]
   copper.append({'source':name,'start':p,'active_in_saved_USS':name=='USS','audio_moves':[e for e in moves if 0xa0<=int(e['register'],16)<=0xde],'dma_interrupt_moves':[e for e in moves if int(e['register'],16) in (0x96,0x9a,0x9c,0x9e)],'instructions':l['instructions']})
 if any(c['audio_moves'] for c in copper):raise ValueError('New Copper audio moves require analysis')
 irq=[e for e in copper[1]['dma_interrupt_moves'] if e.get('value')=='0x8010']
 if len(irq)!=1:raise ValueError('Changed active Copper IRQ')
 #Start DMA mask and panning constants are DATA in CODE, never disassemble as opcodes.
 constants=code[0xc0d07e-CODE_BASE:0xc0d08c-CODE_BASE]
 if constants.hex()!='8203820c000000003c0028001e00':raise ValueError('Sound constants changed')
 working_sets=[];samples={r['sound_id']:r for r in sample_rows}
 for level in audit:
  ids={17,19,22,24}
  for idx in level['graphic_types']:
   ids.update(types[idx][k] for k in ('destruction_sound','shot_sound','entry_sound','attack_sound'))
  working_sets.append({'level':level['level'],'sound_IDs':sorted(ids),'bytes':sum(samples[i]['bytes'] for i in ids),'interpretation':'all four type events plus fixed effects, upper bound even where a port disables attack'})
 events=[]
 def event(label,sid,site,pair,t=None,condition=''):
  s=samples[sid];row={'event':label,'vylv_index':t['vylv_index'] if t else '', 'vygr_type_1based':t['vygr_type_1based'] if t else '', 'sound_id':sid,'USS_trigger':site,'dump_trigger':0x21b20+site-CODE_BASE,'CODE_offset':site-CODE_BASE,'Shot_offset':h['file_offset']+site-CODE_BASE,'Paula_channels':pair,'sonquasar_offset':s['sonquasar_offset'],'sample_bytes':s['bytes'],'Paula_PER':s['Paula_PER'],'pan_divisor':s['pan_divisor'],'busy_ticks':s['busy_ticks'],'volume_rule':'left=240/div-floor(clamp(X,0,240)/div);right=floor(clamp(X,0,240)/div)','admission':condition,'evidence':'confirmed_static_code_and_byte_matches'};events.append(row)
 for t in types:
  for label,key,site,pair in [('enemy_destroyed','destruction_sound',0xc0d332,'2,3'),('enemy_shot','shot_sound',0xc0d63c,'2,3'),('enemy_entry','entry_sound',0xc0d41c,'0,1'),('enemy_attack','attack_sound',0xc0d21e,'0,1')]:event(label,t[key],site,pair,t,'pair busy_count==0; last pending writer before tick wins')
 for label,sid,site in [('player_shot',17,0xc0d10a),('player_destroyed',19,0xc09498),('level_transition_early',24,0xc08f52),('level_transition_rectangles',22,0xc09060)]:event(label,sid,site,'0,1',condition='unconditional pending overwrite; stops current pair DMA')
 report={'issue':67,'analysis_only':True,'engine_base':'f7350d6 (main merge of tested Stage7b5b)','sources_sha256':BASE.HASHES,'ADF_inventory':list(inventory.values()),'selected_files_validated':selected,'startup':files['/Vyper/s/startup-sequence'].decode(),'HUNK_sections':[{'file_offset':h['file_offset'],'bytes':len(h['data']),'allocated_bytes':h['allocated_bytes'],'relocations':len(h['relocations'])} for h in hs],'mappings':{n:{k:v for k,v in s.items() if k in ('base','bases')} for n,s in sources.items()},'verified_spans':spans,'direct_hardware_candidates':candidates,'direct_callers':calls,'sample_file':{'path':'/Vyper/sonquasar','bytes':len(snd),'sha256':BASE.sha(snd),'described_bytes':offset,'unconsumed_tail_bytes':len(snd)-offset,'tail_sha256':BASE.sha(snd[offset:]),'loaded_sample_bytes':sum(r['bytes'] for r in sample_rows if r['loaded'])},'samples':sample_rows,'enemy_types':types,'sample_working_sets':working_sets,'events':events,'level_Forme_audit':audit,'types_not_in_100_levels':sorted(set(range(38))-used),'copper_lists':copper,'saved_AUD_chunks':{k.decode():v['data'].hex() for k,v in chunks.items() if k[:3]==b'AUD'},'suspected_addresses':{'dump_26B48':raw['Vyper_Memory_Dump.dat'][0x26b48:0x26b58].hex(),'interpretation_26B48':'operand inside LEA at dump26B46 / USS C0D786, not routine entry','dump_311E_3262_sha256':BASE.sha(raw['Vyper_Memory_Dump.dat'][0x311e:0x3264]),'interpretation_311E_3262':'outside game CODE; no proven sound-routine identity'},'hardware_assumptions':{'preview_Paula_clock_Hz':paula_clock,'MEGA65_counter_clock_Hz':40500000,'WAV_rate':'rounded clock/PER; mono raw sample only, no Paula stereo/analogue filter/timing/preemption'},'limitations':['Static code/data proof, no executed WinUAE/hardware audio trace.','Menu savestate is idle audio, not a gameplay audio recording.','Aligned opcode scan is discovery only; unverified candidates are not code proof.','Four nonactive dump Copper finds do not establish all possible dynamic lists.','Other executable a is not a HUNK_HEADER image; not treated as the running Shot CODE.','Unrelated blank-name disk file data not read; do not claim whole-disk data-chain validity.','Native mainloop cadence remains open; busy counts are audio-tick units, not measured milliseconds.','Teardown passes SetIntVector arguments0x80/0x200 rather than setup7/9; intent apparent, correct restoration NOT proven.', 'No game source, DAT, PRG or D81 generated/modified.']}
 output.mkdir(parents=True,exist_ok=True)
 (output/'evidence.json').write_text(json.dumps(report,indent=2)+'\n');(output/'68000-excerpts.txt').write_text('Addresses: USS / dump / CODE offset / extracted Shot file offset.\n'+''.join(text));(output/'samples.csv').write_text(csv_bytes(sample_rows));(output/'enemy_types.csv').write_text(csv_bytes(types));(output/'events.csv').write_text(csv_bytes(events))
 if samples_out is not None:
  samples_out.mkdir(parents=True,exist_ok=True)
  for row in sample_rows:
   sid=row['sound_id'];blob=sample_data[sid];(samples_out/f'sound_{sid:02d}.s8').write_bytes(blob)
   if wav:
    with wave.open(str(samples_out/f'sound_{sid:02d}_PER{row["Paula_PER"]}.wav'),'wb') as w:
     w.setparams((1,1,round(paula_clock/row['Paula_PER']),0,'NONE','not compressed'));w.writeframes(bytes(v^128 for v in blob))
  (samples_out/'preview-parameters.json').write_text(json.dumps(report['hardware_assumptions'],indent=2)+'\n');(samples_out/'samples.csv').write_text(csv_bytes(sample_rows))
 print(json.dumps({'verified_spans':len(spans),'instructions':sum(len(s['instructions']) for s in spans),'samples':24,'loaded':20,'types':38,'destruction_IDs':sorted(set(t['destruction_sound'] for t in types)),'levels':len(audit),'extracted_raw_samples':str(samples_out) if samples_out else None},indent=2))
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=ROOT/'assets/stage5b/original_sources');p.add_argument('--output',type=Path,default=ROOT/'docs/amiga_sound_evidence');p.add_argument('--samples-out',type=Path);p.add_argument('--wav',action='store_true');p.add_argument('--paula-clock',type=int,default=3546895);a=p.parse_args();analyze(a.source,a.output,a.samples_out,a.wav,a.paula_clock)
