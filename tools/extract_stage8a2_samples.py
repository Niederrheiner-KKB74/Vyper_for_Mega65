#!/usr/bin/env python3
"""Lossless packing of the twenty evidenced, loaded sonquasar segments."""
import argparse,binascii,csv,json,struct
from pathlib import Path
import extract_stage8a1_sample as BASE
ROOT=BASE.ROOT

def extract(output):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 # Reuse the stable extractor's source/descriptor/runtime integrity checks.
 import tempfile
 with tempfile.TemporaryDirectory() as t:BASE.extract(t)
 S=BASE.SOUND
 raw={n:(ROOT/'assets/stage5b/original_sources'/n).read_bytes() for n in S.BASE.HASHES}
 _,read=S.ofs_inventory(raw['VYPER.ADF']);pcm=read('/Vyper/sonquasar');h=S.BASE.hunks(read('/Vyper/Shot'))
 chunks=S.BASE.uss_chunks(raw['Vyper_Startscreen.uss'])
 with (ROOT/'docs/amiga_sound_evidence/samples.csv').open() as f:rows=list(csv.DictReader(f))
 archive=bytearray();meta=[];offset=0
 for i,row in enumerate(rows):
  per,div,words,busy,ptr=struct.unpack_from('>4HI',h[1]['data'],0x20a+12*i);blob=pcm[offset:offset+words*2]
  if offset!=int(row['sonquasar_offset']) or S.BASE.sha(blob)!=row['sample_sha256']:raise ValueError('Descriptor/sample integrity mismatch')
  if (per,div,words,busy)!=(int(row['Paula_PER']),int(row['pan_divisor']),int(row['Paula_LEN_words']),int(row['busy_ticks'])):raise ValueError('Original metadata mismatch')
  if (row['loaded']=='True')!=(i+1 not in (4,13,14,23)):raise ValueError('Unexpected loaded sample set')
  if row['loaded']=='True':
   for ram,base in [(chunks[b'CRAM']['data'],0x18140),(raw['Vyper_Memory_Dump.dat'],0x2af50)]:
    p=S.BASE.u32(ram,base+0x20a+12*i+8)
    if ram[p:p+len(blob)]!=blob:raise ValueError('Runtime PCM evidence mismatch')
   den=per*40500000;rate=(3546895*(1<<24)+den//2)//den
   meta.append(dict(id=i+1,original_offset=offset,offset=len(archive),length=len(blob),per=per,divisor=div,busy=busy,rate=rate,sha256=S.BASE.sha(blob),crc=binascii.crc_hqx(blob,65535)))
   archive+=blob
  offset+=words*2
 if len(meta)!=20 or len(archive)!=154304:raise ValueError('Archive dimensions')
 (output/'VYAU.DAT').write_bytes(archive)
 report=dict(source_sha256=S.BASE.HASHES,archive_bytes=len(archive),archive_sha256=S.BASE.sha(archive),archive_crc=binascii.crc_hqx(archive,65535),samples=meta)
 (output/'samples.json').write_text(json.dumps(report,indent=2)+'\n')
 with (output/'samples.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(meta[0]),lineterminator="\n");writer.writeheader();writer.writerows(meta)
 inc=f'.const ARCHIVE_BYTES={len(archive)}\n.const ARCHIVE_CRC=${report["archive_crc"]:04x}\n'
 (output/'archive.inc').write_text(inc)
 inc=''
 fields={'ids':lambda m:m['id'],'length_lo':lambda m:m['length']&255,'length_hi':lambda m:m['length']>>8,'src_lo':lambda m:m['offset']&255,'src_hi':lambda m:(m['offset']>>8)&255,'src_bank':lambda m:m['offset']>>16,'rate_lo':lambda m:m['rate']&255,'rate_hi':lambda m:(m['rate']>>8)&255,'rate_bank':lambda m:m['rate']>>16,'divisors':lambda m:m['divisor'],'busy_values':lambda m:m['busy']}
 for n,fn in fields.items():inc+=n+': .byte '+','.join(str(fn(m)) for m in meta)+'\n'
 # Endian-neutral crossbar coefficients: original Paula VOL/64 rounded to 8bit,
 # then replicated into BOTH bytes. Max coefficient error < 1/510.
 inc+='gains: .byte '+','.join(str((v*255+32)//64) for v in range(61))+'\n'
 (output/'samples.inc').write_text(inc)
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);extract(p.parse_args().output)
