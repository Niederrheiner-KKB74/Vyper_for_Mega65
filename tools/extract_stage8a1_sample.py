#!/usr/bin/env python3
"""Extract ONLY original sound17; PR68 commit d135b75 is the evidence source."""
import argparse,csv,json,struct,binascii
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'analysis'))
import analyze_amiga_sound as SOUND
ROOT=SOUND.ROOT
def extract(output):
 raw={n:(ROOT/'assets/stage5b/original_sources'/n).read_bytes() for n in SOUND.BASE.HASHES}
 for n,b in raw.items():
  if SOUND.BASE.sha(b)!=SOUND.BASE.HASHES[n]:raise ValueError('Original source hash mismatch '+n)
 inventory,read=SOUND.ofs_inventory(raw['VYPER.ADF']);shot=read('/Vyper/Shot');pcm=read('/Vyper/sonquasar');h=SOUND.BASE.hunks(shot)
 with (ROOT/'docs/amiga_sound_evidence/samples.csv').open(newline='') as f:rows=list(csv.DictReader(f))
 row=rows[16]
 if (int(row['sound_id']),row['loaded'],int(row['Paula_PER']),int(row['bytes']))!=(17,'True',356,6720):raise ValueError('PR68 sample17 evidence changed')
 desc=0x20a+16*12;per,div,words,hold,ptr=struct.unpack_from('>4HI',h[1]['data'],desc)
 if (per,words,ptr)!=(356,3360,0):raise ValueError('Original descriptor mismatch')
 offset=sum(SOUND.BASE.u16(h[1]['data'],0x20e+12*i)*2 for i in range(16));blob=pcm[offset:offset+words*2]
 if offset!=int(row['sonquasar_offset']) or SOUND.BASE.sha(blob)!=row['sample_sha256']:raise ValueError('Original sample hash/offset mismatch')
 chunks=SOUND.BASE.uss_chunks(raw['Vyper_Startscreen.uss'])
 for ram,base in [(chunks[b'CRAM']['data'],0x18140),(raw['Vyper_Memory_Dump.dat'],0x2af50)]:
  p=SOUND.BASE.u32(ram,base+desc+8)
  if ram[p:p+len(blob)]!=blob:raise ValueError('Original sample differs from RAM evidence')
 # Exact rational nearest-integer calculation; no floating-point pitch decision.
 num=3546895*(1<<24);den=per*40500000;inc=(num+den//2)//den
 crc=binascii.crc_hqx(blob,0xffff)
 meta={'sound_id':17,'original':'/Vyper/sonquasar','original_file_offset':offset,'bytes':len(blob),'Paula_LEN_words':words,'Paula_PER':per,'signedness':'signed8, unchanged bytes; NO XOR','sha256':SOUND.BASE.sha(blob),'CRC16_CCITT_FALSE':crc,'Paula_clock_assumed_PAL':3546895,'counter_clock_assumed':40500000,'nominal_rate_Hz':3546895/per,'rate_increment':inc,'rate_increment_hex':f'${inc:06X}','actual_nominal_MEGA65_rate_Hz':inc*40500000/(1<<24),'expected_seconds':len(blob)*per/3546895,'sources_sha256':SOUND.BASE.HASHES,'analysis_commit':'d135b754beec10d608ac4bf6b91a2357247b62f3'}
 output=Path(output);output.mkdir(parents=True,exist_ok=True);(output/'sound17.s8').write_bytes(blob);(output/'sample17.json').write_text(json.dumps(meta,indent=2)+'\n')
 (output/'sample17.inc').write_text(f'.const SAMPLE_BYTES={len(blob)}\n.const SAMPLE_RATE=${inc:06x}\n.const SAMPLE_CRC=${crc:04x}\n')
 return meta
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);print(json.dumps(extract(p.parse_args().output),indent=2))
